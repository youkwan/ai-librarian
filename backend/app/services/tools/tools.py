import httpx
import asyncio
import inspect
import sys
from typing import Annotated
from datetime import datetime
from duckduckgo_search import DDGS
from langchain_core.tools import tool
from langchain_community.tools import WikipediaQueryRun
from langchain_core.tools.base import InjectedToolCallId, BaseTool
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper

from app.services.tools.google_books import GoogleBooksClient
from app.services.tools.helper import tool_helper, get_current_tool_stream
from app.core.settings import settings


@tool
@tool_helper
def get_current_time(
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """Get the current time and return it as a descriptive string.

    Returns:
        A string containing the current time, including year, month, day, hour, minute, second, and microsecond. The format is generally 'The current time is YYYY-MM-DD HH:MM:SS.ffffff'.
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

    if result:
        stream.send_complete(result.text)
        return result.text
    else:
        stream.send_complete("Unable to retrieve any information from the web")
        return "Unable to retrieve any information from the web"


@tool
@tool_helper
async def search_google_books(
    tool_call_id: Annotated[str, InjectedToolCallId],
    query: str,
) -> str:
    """Searches the Google Books API for books matching a given query.

    Args:
        query: Required. The search query string (e.g., book title, author, topic).

    Returns:
        A formatted string containing the top book suggestions found for the query,
        including title, authors, summary, and a link.
        If no books are found, it returns a message indicating that.
        If an API error occurs, it returns an error message.

        Example format for successful results::

            Here are 5 suggestions for books related to 'artificial intelligence':

            1. "Artificial Intelligence: A Modern Approach" by Stuart Russell and Peter Norvig: Summary...
            You can read more at http://...

            2. "Book Title 2" by Author Name: Summary...
            You can read more at http://...

            ...
    """
    stream = get_current_tool_stream()

    google_books_client = GoogleBooksClient()
    result = await google_books_client.arun(query)
    stream.send_complete(result)
    return result


@tool
@tool_helper
def search_arxiv(
    tool_call_id: Annotated[str, InjectedToolCallId],
    query: str,
) -> str:
    """Searches the Arxiv API for academic papers matching a given query.

    This tool is useful for finding research papers, preprints, and technical documents
    in various scientific fields.

    Args:
        query: Required. The search query string (e.g., paper title, author, topic, or keywords).
              You can use specific search operators to refine your search:
              - author: Search by author name (e.g., "author:Einstein")
              - title: Search in paper titles (e.g., "title:quantum")
              - abstract: Search in abstracts (e.g., "abstract:machine learning")
              - category: Search by subject category (e.g., "cat:cs.AI")

    Returns:
        A formatted string containing the top research papers found for the query.
        Each paper entry includes:
        - Title
        - Authors
        - Abstract
        - Publication date
        - arXiv ID
        - Link to the paper

        If no papers are found, it returns a message indicating that.
        If an API error occurs, it returns an error message.

        Example output::

            Published: 2023-01-01
            Title: Example Paper Title
            Authors: Author1, Author2, Author3
            Summary: This is a brief summary of the paper...
            Link: https://arxiv.org/abs/1234.5678

            Published: 2023-01-02
            Title: Another Paper Title
            Authors: Author4, Author5
            Summary: Another brief summary...
            Link: https://arxiv.org/abs/8765.4321
    """
    stream = get_current_tool_stream()
    arxiv = ArxivAPIWrapper(
        top_k_results=settings.top_k_results,
        ARXIV_MAX_QUERY_LENGTH=settings.arxiv_max_query_length,
        load_max_docs=settings.load_max_docs,
        load_all_available_meta=settings.load_all_available_meta,
        doc_content_chars_max=settings.doc_content_chars_max,
    )
    result = arxiv.run(query)
    stream.send_complete(result)
    return result


@tool
@tool_helper
def search_wikipedia(
    tool_call_id: Annotated[str, InjectedToolCallId],
    query: str,
) -> str:
    """Searches Wikipedia for articles matching a given query.

    This tool is useful for finding general knowledge, historical information,
    and detailed explanations about various topics.

    Args:
        query: Required. The search query string (e.g., topic, person, event, or concept).
              You can use specific search operators to refine your search:
              - intitle: Search in article titles (e.g., "intitle:Python")
              - insource: Search in article source text (e.g., "insource:programming")
              - prefix: Search for articles with specific prefix (e.g., "prefix:Category:")
              - namespace: Search in specific namespaces (e.g., "namespace:Help")

    Returns:
        A formatted string containing the Wikipedia article(s) found for the query.
        Each article entry includes:
        - Title
        - Summary of the article content
        - Link to the full article

        If no articles are found, it returns a message indicating that.
        If an API error occurs, it returns an error message.

        Example output::

            Page: Example Article
            Summary: This is a brief summary of the article content...
            Link: https://en.wikipedia.org/wiki/Example_Article

            Page: Another Article
            Summary: Another brief summary...
            Link: https://en.wikipedia.org/wiki/Another_Article
    """
    stream = get_current_tool_stream()
    wikipedia = WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(
            top_k_results=settings.wikipedia_top_k_results,
            lang=settings.wikipedia_lang,
            load_all_available_meta=settings.wikipedia_load_all_available_meta,
            doc_content_chars_max=settings.wikipedia_doc_content_chars_max,
        )
    )

    try:
        result = wikipedia.run(query)
        stream.send_complete(result)
        return result
    except Exception as e:
        stream.send_error(f"Error: {e}")
        return f"Error: {e}"


@tool
@tool_helper
def search_web(
    tool_call_id: Annotated[str, InjectedToolCallId],
    keywords: str,
    focus_on_news: bool = False,
    region: str = "wt-wt",
) -> str:
    """Searches the web using DuckDuckGo to find information based on the provided keywords.

    This tool is useful for finding up-to-date information or answers to specific questions.

    Args:
        keywords: The search query string. You can use search operators to refine your search for better results. See examples below.
        region: The region code to tailor the search results to a specific country or language. Defaults to "wt-wt" (No region). See the full list of available region codes below.
        focus_on_news: Whether to focus on news results. Defaults to False.

    **Keyword Search Operators:**

    Use these operators within the `keywords` argument to make your search more precise:

    - `cats dogs`: Results containing either "cats" or "dogs".
    - `"cats and dogs"`: Results containing the exact phrase "cats and dogs". Related results if none found.
    - `cats -dogs`: Results about "cats" but excluding "dogs". Use `-` to exclude terms.
    - `cats +dogs`: Results specifically including "dogs" along with "cats". Use `+` for inclusion.
    - `cats filetype:pdf`: Returns only PDF files related to "cats". Supported types: pdf, doc(x), xls(x), ppt(x), html.
    - `dogs site:example.com`: Returns pages about "dogs" only from the website `example.com`.
    - `cats -site:example.com`: Returns pages about "cats", excluding results from `example.com`.
    - `intitle:dogs`: Returns pages where the word "dogs" appears in the page title.
    - `inurl:cats`: Returns pages where the word "cats" appears in the URL.

    **Region Codes:**

    Specify a `region` code to get results localized for that area.

    - `xa-ar`: Arabia
    - `xa-en`: Arabia (English)
    - `ar-es`: Argentina
    - `au-en`: Australia
    - `at-de`: Austria
    - `be-fr`: Belgium (French)
    - `be-nl`: Belgium (Dutch)
    - `br-pt`: Brazil
    - `bg-bg`: Bulgaria
    - `ca-en`: Canada (English)
    - `ca-fr`: Canada (French)
    - `ct-ca`: Catalan
    - `cl-es`: Chile
    - `cn-zh`: China
    - `co-es`: Colombia
    - `hr-hr`: Croatia
    - `cz-cs`: Czech Republic
    - `dk-da`: Denmark
    - `ee-et`: Estonia
    - `fi-fi`: Finland
    - `fr-fr`: France
    - `de-de`: Germany
    - `gr-el`: Greece
    - `hk-tzh`: Hong Kong
    - `hu-hu`: Hungary
    - `in-en`: India
    - `id-id`: Indonesia
    - `id-en`: Indonesia (English)
    - `ie-en`: Ireland
    - `il-he`: Israel
    - `it-it`: Italy
    - `jp-jp`: Japan
    - `kr-kr`: Korea
    - `lv-lv`: Latvia
    - `lt-lt`: Lithuania
    - `xl-es`: Latin America
    - `my-ms`: Malaysia
    - `my-en`: Malaysia (English)
    - `mx-es`: Mexico
    - `nl-nl`: Netherlands
    - `nz-en`: New Zealand
    - `no-no`: Norway
    - `pe-es`: Peru
    - `ph-en`: Philippines (English)
    - `ph-tl`: Philippines (Tagalog)
    - `pl-pl`: Poland
    - `pt-pt`: Portugal
    - `ro-ro`: Romania
    - `ru-ru`: Russia
    - `sg-en`: Singapore
    - `sk-sk`: Slovak Republic
    - `sl-sl`: Slovenia
    - `za-en`: South Africa
    - `es-es`: Spain
    - `se-sv`: Sweden
    - `ch-de`: Switzerland (German)
    - `ch-fr`: Switzerland (French)
    - `ch-it`: Switzerland (Italian)
    - `tw-tzh`: Taiwan
    - `th-th`: Thailand
    - `tr-tr`: Turkey
    - `ua-uk`: Ukraine
    - `uk-en`: United Kingdom
    - `us-en`: United States (English)
    - `ue-es`: United States (Spanish)
    - `ve-es`: Venezuela
    - `vn-vi`: Vietnam
    - `wt-wt`: No region (Default)

    Returns:
        A string containing the search results, typically a list of snippets including title, URL, and description for each result. The format may vary based on the search engine's response.
    """
    stream = get_current_tool_stream()
    try:
        if focus_on_news:
            result = DDGS().news(
                keywords,
                max_results=settings.max_web_search_results,
                region=region,
            )
        else:
            result = DDGS().text(
                keywords,
                max_results=settings.max_web_search_results,
                region=region,
            )
    except Exception as e:
        stream.send_error(f"Error: {e}")
        return f"Error: {e}"
    stream.send_complete(tool_tokens=result)
    return result


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
