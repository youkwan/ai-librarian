import functools
import inspect
import random
import sys
import time
from typing import Annotated
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId, BaseTool

from app.services.helper import tool_helper, get_current_tool_stream


@tool
@tool_helper
def search(query: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> str:
    """Search"""
    stream = get_current_tool_stream()

    status1 = f"🔍 Initializing search for '{query}'..."
    stream.send_progress(tool_tokens=status1, metadata={"step": 1})
    time.sleep(1.5)
    status2 = "⏳ Performing search across databases..."
    stream.send_progress(tool_tokens=status2, metadata={"step": 2})
    time.sleep(2.0)
    status3 = "📊 Aggregating results..."
    stream.send_progress(tool_tokens=status3, metadata={"step": 3})
    time.sleep(1.0)
    final_result = f"Search for '{query}' completed. Found 3 relevant documents."
    stream.send_progress(
        tool_tokens=final_result,
        metadata={"step": 4, "is_final": True},
    )
    return final_result


@tool
@tool_helper
def get_temperature(
    tool_call_id: Annotated[str, InjectedToolCallId],
    location: str,
) -> str:
    """Get the temperature in a given location"""
    stream = get_current_tool_stream()

    temperature = random.randint(0, 40)

    tool_output = f"The temperature in {location} is {temperature}C"
    stream.send_complete(tool_tokens=tool_output)

    return tool_output


@tool
@tool_helper
def get_humidity(
    tool_call_id: Annotated[str, InjectedToolCallId],
    location: str,
) -> str:
    """Get the humidity in a given location"""
    stream = get_current_tool_stream()
    if not stream:
        raise RuntimeError("ToolStreamContext not found.")

    time.sleep(0.05)
    humidity = random.randint(0, 100)
    tool_output = f"The humidity in {location} is {humidity}%"
    stream.send_complete(tool_tokens=tool_output)

    return tool_output


@tool
@tool_helper
def add(
    tool_call_id: Annotated[str, InjectedToolCallId],
    a: int,
    b: int,
) -> int:
    """Add two numbers together"""
    stream = get_current_tool_stream()
    if not stream:
        raise RuntimeError("ToolStreamContext not found.")

    result = a + b
    message_content = f"The sum of {a} and {b} is {result}."
    stream.send_complete(tool_tokens=message_content)

    return result


@tool
@tool_helper
def get_current_time(
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """Get the current time"""
    stream = get_current_tool_stream()
    if not stream:
        raise RuntimeError("ToolStreamContext not found.")

    current_time_str = f"The current time is {datetime.now()}"
    stream.send_complete(tool_tokens=current_time_str)

    return current_time_str


# Dynamically append all @tool functions in the current module
TOOLS = [
    obj
    for _, obj in inspect.getmembers(sys.modules[__name__])
    if isinstance(obj, BaseTool)
]


# Dynamically mapping tool names to their descriptions (docstrings)
TOOLS_INFO = [
    {"tool_name": obj.name, "tool_description": obj.description}
    for _, obj in inspect.getmembers(sys.modules[__name__])
    if isinstance(obj, BaseTool)
]
