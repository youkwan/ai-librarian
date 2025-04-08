import random
from typing import Annotated
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_core.tools.base import InjectedToolCallId
from langgraph.types import Command
from langgraph.config import get_stream_writer

from app.models.schema import ToolCall


@tool
def get_temperature(
    tool_call_id: Annotated[str, InjectedToolCallId], location: str
) -> Command:
    """Get the temperature in a given location"""

    temperature = random.randint(0, 40)
    tool_output = f"The temperature in {location} is {temperature}C"

    tool_call = ToolCall(
        name="get_temperature",
        output=tool_output,
    )

    writer = get_stream_writer()
    writer(tool_call.model_dump())
    return Command(
        update={
            "tools_used": [tool_call],
            "messages": [ToolMessage(content=tool_output, tool_call_id=tool_call_id)],
        }
    )


@tool
def get_humidity(
    tool_call_id: Annotated[str, InjectedToolCallId], location: str
) -> Command:
    """Get the humidity in a given location"""
    humidity = random.randint(0, 100)
    tool_output = f"The humidity in {location} is {humidity}%"
    tool_call = ToolCall(
        name="get_humidity",
        output=tool_output,
    )
    writer = get_stream_writer()
    writer(tool_call.model_dump())
    return Command(
        update={
            "tools_used": [tool_call],
            "messages": [ToolMessage(content=tool_output, tool_call_id=tool_call_id)],
        }
    )


@tool
def add(tool_call_id: Annotated[str, InjectedToolCallId], a: int, b: int) -> int:
    """Add two numbers together"""
    return Command(
        update={
            "tools_used": [
                ToolCall(
                    name="add",
                    output=a + b,
                )
            ],
            "messages": [
                ToolMessage(content=f"{a}+{b}={a+b}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool
def get_time() -> str:
    """Get the current time"""
    return f"The current time is {datetime.now()}"


TOOLS = [get_time, get_temperature, get_humidity, add]
