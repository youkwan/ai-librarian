import asyncio
import functools
import inspect
import random
import sys
import time
from typing import Annotated
from datetime import datetime
import httpx
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId, BaseTool

from app.services.helper import tool_helper, get_current_tool_stream


@tool
@tool_helper
def get_current_time(
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """Get the current time and return it as a descriptive string.

    The function returns a string indicating the current time, including year,
    month, day, hour, minute, second, and microsecond. The format is
    generally 'The current time is YYYY-MM-DD HH:MM:SS.ffffff'.
    """
    stream = get_current_tool_stream()

    current_time_str = f"The current time is {datetime.now()}"
    stream.send_complete(tool_tokens=current_time_str)

    return current_time_str


@tool
@tool_helper
async def get_current_weather(
    tool_call_id: Annotated[str, InjectedToolCallId],
    lat: float,
    lon: float,
) -> str:
    """Gets the current weather for a given geographical location using the OpenWeatherMap API.

    Args:
        lat: Required. The latitude of the location.
        lon: Required. The longitude of the location.

    Returns:
        A string containing the weather data in XML format as requested from the API.
        Example structure:
        <?xml version="1.0" encoding="UTF-8"?>
        <current>
            <city id="..." name="...">...</city>
            <temperature value="..." min="..." max="..." unit="kelvin"></temperature>
            <feels_like value="..." unit="kelvin"></feels_like>
            <humidity value="..." unit="%"></humidity>
            <pressure value="..." unit="hPa"></pressure>
            <wind>...</wind>
            <clouds value="..." name="..."></clouds>
            <visibility value="..."></visibility>
            <precipitation mode="..."></precipitation>
            <weather number="..." value="..." icon="..."></weather>
            <lastupdate value="..."></lastupdate>
        </current>
    """
    stream = get_current_tool_stream()
    stream.send_progress(tool_tokens="Getting weather data from OpenWeatherMap...")

    async with httpx.AsyncClient() as client:
        result = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": "5e2be625a32ec0c5d4fc159f58266494",
                "mode": "xml",
            },
        )

    stream.send_complete(tool_tokens=result.text)
    return result.text


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


if __name__ == "__main__":

    async def main():
        result = await get_current_weather.ainvoke(
            input={
                "tool_call_id": "123",
                "lat": 37.7749,
                "lon": -122.4194,
            }
        )
        print(result)

    asyncio.run(main())
