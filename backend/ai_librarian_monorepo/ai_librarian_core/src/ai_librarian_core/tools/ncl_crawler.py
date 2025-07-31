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
        >>> result = ncl_crawler_tool.invoke({"query": "Artificial Intelligence"})
        >>> print(result)
        1. Artificial Intelligence: A Modern Approach (Stuart Russell) - https://aleweb.ncl.edu.tw/F/...
        2. Artificial Intelligence and Deep Learning (Ian Goodfellow) - https://aleweb.ncl.edu.tw/F/...
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
