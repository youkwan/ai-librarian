import functools
import inspect
from collections.abc import Callable
from contextvars import ContextVar
from typing import Annotated, Any, Literal

from langchain_core.messages import ToolMessage
from langchain_core.tools.base import InjectedToolCallId
from langgraph.config import get_stream_writer
from langgraph.types import Command, StreamWriter

from agent_core.models.toolcall import ToolCall


def create_command(tool_name: str, tool_output: Any, tool_call_id: str) -> Command:
    """Helper to create the standard Command object for tool results."""
    content = str(tool_output)
    return Command(
        update={
            "tools_used": [ToolCall(name=tool_name, output=content)],
            "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        }
    )


def tool_helper(func: Callable) -> Callable:
    """Decorator to simplify creating LangGraph tools with streaming and Command wrapping.

    This decorator should be applied **directly** to the tool function, **before**
    the standard `@tool` decorator.

    It handles:
    1. Setting up and managing the ToolStreamManager context for streaming events.
    2. Allowing the tool function to use `get_current_tool_stream()` to send progress updates
       or stream partial results during execution (useful for long-running tools).
    3. Automatically wrapping the raw return value of the tool function
       into a LangGraph `Command` object.

    The decorated function should:
    - Implement the core tool logic.
    - Use `get_current_tool_stream().send_progress(...)` to send intermediate updates or partial results.
    - Optionally, use `get_current_tool_stream().send_complete(...)` to send a final result
      along with the completion signal. If `send_complete` is **not** called, a default
      `completed` event (without data) will be sent automatically upon successful completion.
    - Return the final raw result (e.g., a string, int, dict), **not** a `Command` object.

    Usage Example:
        ```python
        from langchain_core.tools import tool
        from .helper import tool_helper, get_current_tool_stream

        @tool # Applied second (outer)
        @tool_helper # Applied first (inner)
        def my_tool(param1: str, *, tool_call_id: ...) -> str:
            '''My awesome tool description.'''
            stream = get_current_tool_stream()
            stream.send_progress("Starting long task...")
            # ... partial work 1 ...
            stream.send_progress("Partial result 1 data...")
            # ... partial work 2 ...
            stream.send_progress("Partial result 2 data...")
            # ... final work ...
            final_result = "Final aggregated result"
            stream.send_complete(final_result) # Optional: stream out final result
            return final_result
        ```
    """

    tool_name = func.__name__
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, tool_call_id: Annotated[str, InjectedToolCallId], **kwargs):
            with ToolStreamManager(tool_name):
                raw_output = await func(*args, tool_call_id=tool_call_id, **kwargs)
            return create_command(tool_name, raw_output, tool_call_id)

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(*args, tool_call_id: Annotated[str, InjectedToolCallId], **kwargs):
            with ToolStreamManager(tool_name):
                raw_output = func(*args, tool_call_id=tool_call_id, **kwargs)
            return create_command(tool_name, raw_output, tool_call_id)

        return sync_wrapper


_current_tool_stream = ContextVar("current_tool_stream", default=None)


class ToolStreamManager:
    """Manages the streaming lifecycle (start, delta, completed) for a tool call.

    Handles acquiring the stream writer, sending start/delta/completed events,
    and managing the completion state. Intended to be used as a context manager
    via the @tool_helper decorator, which also handles setting/resetting the
    necessary context variable.

    Usage Example (within a tool function decorated by @tool_helper):
        ```python
        stream = get_current_tool_stream()
        stream.send_partial_result("partial result 1...")
        # ... perform step 1 ...
        stream.send_partial_result("partial result 2...")
        # ... perform step 2 ...
        final_data = "Process finished successfully."
        # Option 1: Send final data with the completed event
        stream.send_complete(final_data)
        # Option 2: let __exit__ send default completed event
        # stream.send_partial_result(final_data)
        ```
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.writer: StreamWriter | None = None
        self._completion_sent: bool = False  # Flag to track if completion was manually sent
        self._reset_token = None  # Token for resetting context var

    def _send(
        self,
        type: Literal["start", "delta", "completed"],
        tool_tokens: str = None,
        metadata: dict = {},
    ):
        """Helper to format and send stream messages."""

        write_data = {
            "type": type,
            "tool_name": self.tool_name,
            "metadata": metadata,
        }
        if tool_tokens is not None:
            write_data["tool_tokens"] = tool_tokens

        try:
            self.writer(write_data)  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Error sending stream message type '{type}' for tool {self.tool_name}: {e}")

    def __enter__(self):
        """Acquires the stream writer, sends the 'start' event, and sets the context variable."""
        try:
            self.writer = get_stream_writer()

            if not self.writer:
                raise RuntimeError(f"Could not get stream writer for tool {self.tool_name}.")

            self._send("start")
            self._reset_token = _current_tool_stream.set(self)

            return self

        except Exception:
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sends the default 'completed' event if not already sent manually."""
        if self.writer and not exc_type and not self._completion_sent:
            self._send("completed")

        self._completion_sent = True

        if self._reset_token:
            _current_tool_stream.reset(self._reset_token)

        return False

    def send_partial_result(self, tool_tokens: str, metadata: dict = {}) -> None:
        """Sends an intermediate progress update during tool execution."""
        if self._completion_sent:
            raise RuntimeError(f"Attempted to send progress for {self.tool_name} after completion was already sent.")
        else:
            self._send("delta", tool_tokens, metadata)

    def send_complete(self, tool_tokens: str | None = None, metadata: dict = {}) -> None:
        """Sends the completed event, optionally with final tool call result."""
        if self._completion_sent:
            raise RuntimeError(f"Attempted to send completion for {self.tool_name} multiple times.")
        else:
            self._send("completed", tool_tokens, metadata)
            self._completion_sent = True


def get_current_tool_stream() -> ToolStreamManager:
    """Gets the ToolStreamManager for the current execution context."""

    stream = _current_tool_stream.get()
    if stream is None:
        raise RuntimeError("Invariant violation: ToolStreamManager context was unexpectedly None.")
    return stream
