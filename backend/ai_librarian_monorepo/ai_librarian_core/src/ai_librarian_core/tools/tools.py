from ai_librarian_core.tools.date_time import DateTimeTool
from ai_librarian_core.tools.google_books import GoogleBooksQueryRun
from ai_librarian_core.tools.ncl_crawler import NCLCrawlerToolRun
from langchain_community.tools import (
    ArxivQueryRun,
    DuckDuckGoSearchResults,
    YouTubeSearchTool,
)
from langchain_community.tools.openweathermap import OpenWeatherMapQueryRun
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool
from langchain_google_community import GoogleSearchAPIWrapper, GoogleSearchRun
from pydantic import ValidationError


def init_built_in_tools() -> list[BaseTool]:
    tools = [
        DateTimeTool(),
        ArxivQueryRun(),
        DuckDuckGoSearchResults(),
        YouTubeSearchTool(),
        NCLCrawlerToolRun(),
        WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
    ]

    try:
        tools.append(GoogleSearchRun(api_wrapper=GoogleSearchAPIWrapper()))
    except ValidationError:
        pass
    try:
        tools.append(GoogleBooksQueryRun())
    except ValidationError:
        pass
    try:
        tools.append(OpenWeatherMapQueryRun())
    except ValidationError:
        pass

    return tools


# # Dynamically append all @tool functions in the current module
# TOOLS = [obj for _, obj in inspect.getmembers(sys.modules[__name__]) if isinstance(obj, BaseTool)]


# # Dynamically mapping tool names to their descriptions (docstrings)
# TOOLS_INFO = [
#     {"tool_name": obj.name, "tool_description": obj.description}
#     for _, obj in inspect.getmembers(sys.modules[__name__])
#     if isinstance(obj, BaseTool)
# ]
