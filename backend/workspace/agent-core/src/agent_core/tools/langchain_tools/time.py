import asyncio
from datetime import datetime

from langchain_core.tools import tool


@tool("time")
async def get_current_time() -> str:
    """Get the current time, including the timezone.

    Returns:
        str: The current time in ISO 8601 format.
    """
    local_time = datetime.now().astimezone()
    local_time_str = local_time.isoformat()
    return f"The current time is {local_time_str}"


if __name__ == "__main__":
    print(asyncio.run(get_current_time.ainvoke({})))
