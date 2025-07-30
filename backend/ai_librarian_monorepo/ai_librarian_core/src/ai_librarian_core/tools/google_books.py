from ai_librarian_core.wrapper.google_books import RobustGoogleBooksAPIWrapper
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class RobustGoogleBooksQueryInput(BaseModel):
    """Input schema for the GoogleBooksQuery tool."""

    query: str = Field(description="query to look up on google books")


class RobustGoogleBooksQueryRun(BaseTool):
    """Tool that searches the Google Books API."""

    name: str = "GoogleBooks"
    description: str = (
        "A wrapper around Google Books. "
        "Useful for when you need to answer general inquiries about "
        "books of certain topics and generate recommendation based "
        "off of key words"
        "Input should be a query string"
    )
    api_wrapper: RobustGoogleBooksAPIWrapper = Field(default_factory=RobustGoogleBooksAPIWrapper)
    args_schema: type[BaseModel] = RobustGoogleBooksQueryInput

    def _run(
        self,
        query: str,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        """Use the Google Books tool."""
        return self.api_wrapper.run(query)
