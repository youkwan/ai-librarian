import functools
from contextvars import ContextVar
from typing import Annotated, Literal
from langchain_core.messages import ToolMessage
from langchain_core.tools.base import InjectedToolCallId
from langgraph.types import Command, StreamWriter
from langgraph.config import get_stream_writer

from app.models.schemas import ToolCall


def create_command(tool_name: str, tool_output: any, tool_call_id: str) -> Command:
    """Helper to create the standard Command object for tool results."""
    content = str(tool_output)  # Must be string
    return Command(
        update={
            "tools_used": [ToolCall(name=tool_name, output=content)],
            "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        }
    )


def tool_helper(func):
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
      `complete` event (without data) will be sent automatically upon successful completion.
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
            # Option 1: Send final result via complete (optional)
            # stream.send_complete(final_result)
            # Option 2: Just return, default complete will be sent
            return final_result
        ```
    """

    @functools.wraps(func)
    def wrapper(*args, tool_call_id: Annotated[str, InjectedToolCallId], **kwargs):
        tool_name = func.__name__

        with ToolStreamManager(tool_name):
            raw_output = func(*args, tool_call_id=tool_call_id, **kwargs)

        return create_command(tool_name, raw_output, tool_call_id)

    return wrapper


_current_tool_stream = ContextVar("current_tool_stream", default=None)


class ToolStreamManager:
    """
    Manages the streaming lifecycle (start, delta, complete) for a tool call.

    Handles acquiring the stream writer, sending start/delta/complete events,
    and managing the completion state. Intended to be used as a context manager
    via the @tool_helper decorator, which also handles setting/resetting the
    necessary context variable.

    Usage Example (within a tool function decorated by @tool_helper):
        ```python
        stream = get_current_tool_stream()
        stream.send_progress("Starting step 1...")
        # ... perform step 1 ...
        stream.send_progress("Step 1 complete. Starting step 2...")
        # ... perform step 2 ...
        final_data = "Process finished successfully."
        # Option 1: Send final data with the complete event
        stream.send_complete(final_data)
        # Option 2: Send progress, let __exit__ send default complete
        # stream.send_progress(final_data)
        ```
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.writer: StreamWriter | None = None
        self._completion_sent: bool = (
            False  # Flag to track if completion was manually sent
        )
        self._reset_token = None  # Token for resetting context var

    def _send(
        self,
        type: Literal["start", "delta", "complete"],
        tool_tokens: str = None,
        metadata: dict = {},
    ):
        """Internal helper to format and send stream messages."""

        write_data = {
            "type": type,
            "tool_name": self.tool_name,
            "metadata": metadata,
        }
        if tool_tokens is not None:
            write_data["tool_tokens"] = tool_tokens

        try:
            self.writer(write_data)
        except Exception as e:
            raise RuntimeError(
                f"Error sending stream message type '{type}' for tool {self.tool_name}: {e}"
            )

    def __enter__(self):
        """Acquires the stream writer, sends the 'start' event, and sets the context variable.
        Raises RuntimeError if a stream writer cannot be obtained.
        """
        try:
            self.writer = get_stream_writer()

            if not self.writer:
                raise RuntimeError(
                    f"Could not get stream writer for tool {self.tool_name}."
                )

            self._send("start")
            self._reset_token = _current_tool_stream.set(self)

            return self

        except Exception as e:
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sends the default 'complete' event if not already sent manually
        and no exception occurred.
        """
        if self.writer and not exc_type and not self._completion_sent:
            self._send("complete")

        self._completion_sent = True

        if self._reset_token:
            _current_tool_stream.reset(self._reset_token)

        return False

    def send_progress(self, tool_tokens: str, metadata: dict = {}):
        """Sends an intermediate progress update during tool execution."""
        if self._completion_sent:
            raise RuntimeError(
                f"Attempted to send progress for {self.tool_name} after completion was already sent."
            )
        else:
            self._send("delta", tool_tokens, metadata)

    def send_complete(self, tool_tokens: str = None, metadata: dict = {}):
        """Sends the complete event, optionally with final tool call result."""
        if self._completion_sent:
            raise RuntimeError(
                f"Attempted to send completion for {self.tool_name} multiple times."
            )
        else:
            self._send("complete", tool_tokens, metadata)
            self._completion_sent = True


def get_current_tool_stream() -> ToolStreamManager:
    """Gets the ToolStreamManager for the current execution context.
    Assumes the context is properly set by the @tool_helper decorator,
    as __enter__ would raise an error otherwise.
    """
    # We can now assume __enter__ either succeeded (and set the context var)
    # or raised an error (preventing this code from being reached).
    stream = _current_tool_stream.get()
    # As a defensive measure, check if stream is unexpectedly None, although this shouldn't happen.
    if stream is None:
        raise RuntimeError(
            "Invariant violation: ToolStreamManager context was unexpectedly None."
        )
    return stream
