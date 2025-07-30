from ai_librarian_core.wrapper.ncl_crawler import NCLCrawler
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field


class NCLCrawlerToolRun(BaseTool):
    """A tool for searching the Taiwan National Central Library(NCL, 國家圖書館) catalog.

    This tool allows searching books in the NCL catalog by keywords. It returns a formatted
    string containing book information including title, author and link.

    Example:
        >>> ncl_crawler_tool = NCLCrawlerToolRun()
        >>> result = asyncio.run(ncl_crawler_tool.arun("AI"))
        >>> print(result)
        1. 人工智慧 (李宏毅) - https://aleweb.ncl.edu.tw/F/...
        2. AI人工智慧導論 (Stuart Russell) - https://aleweb.ncl.edu.tw/F/...
        ...
    """

    name: str = "NCLCrawler"
    description: str = (
        "A tool for searching the Taiwan National Central Library(NCL, 國家圖書館) catalog."
        "The search results are returned in a string, containing the title, author, and link of the book."
        "The title and author are returned in the same language as the query, and the link is the URL of the book."
    )
    ncl_crawler: NCLCrawler = Field(default_factory=NCLCrawler)

    def _run(
        self,
        query: str,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        return self.ncl_crawler.run(query)
