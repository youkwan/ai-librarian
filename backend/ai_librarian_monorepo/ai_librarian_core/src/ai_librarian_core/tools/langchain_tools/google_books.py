import requests
from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, ConfigDict, model_validator

GOOGLE_BOOKS_MAX_ITEM_SIZE = 5
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"


class RobustGoogleBooksAPIWrapper(BaseModel):
    """A modified Google Books API wrapper.

    A wrapper around Google Books API that adds error handling for missing fields and empty author lists.
    Inherits from the original GoogleBooksAPIWrapper and overrides methods to add robustness.

    Original source:
        https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/utilities/google_books.py

    Modifications:
        1. Added null checks for volumeInfo fields (title, authors, description, infoLink)
        2. Fixed index out of range error when authors list is empty

    Args:
        google_api_key(str): API key for accessing Google Books API
        top_k_results(int): Maximum number of book results to return (default: 5)

    Attributes:
        google_api_key(str): API key for accessing Google Books API
        top_k_results(int): Maximum number of book results to return (default: 5)

    Returns:
        str: A formatted string containing book search results with title, authors, summary and source link

    Example:
        >>> google_books_tool = GoogleBooksQueryRun(
        ...     api_wrapper=RobustGoogleBooksAPIWrapper(
        ...         google_api_key=GOOGLE_API_KEY,
        ...         top_k_results=5
        ...     )
        ... )
    """

    google_api_key: str | None = None
    top_k_results: int = GOOGLE_BOOKS_MAX_ITEM_SIZE

    model_config = ConfigDict(
        extra="forbid",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: dict) -> dict:
        """Validate that api key exists in environment."""
        google_api_key = get_from_dict_or_env(values, "google_api_key", "GOOGLE_API_KEY")
        values["google_api_key"] = google_api_key

        return values

    def run(self, query: str) -> str:
        params = (
            ("q", query),
            ("maxResults", self.top_k_results),
            ("key", self.google_api_key),
        )

        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
        json = response.json()

        if response.status_code != 200:
            code = response.status_code
            error = json.get("error", {}).get("message", "Internal failure")
            return f"Unable to retrieve books got status code {code}: {error}"

        return self._format(query, json.get("items", []))

    def _format(self, query: str, books: list) -> str:
        if not books:
            return f"Sorry no books could be found for your query: {query}"

        start = f"Here are {len(books)} suggestions for books related to {query}:"

        results = []
        results.append(start)
        i = 1

        for book in books:
            print(book)
            volume_info = book["volumeInfo"]
            title = volume_info.get("title", "Unknown Title")
            authors = self._format_authors(volume_info.get("authors", []))
            summary = volume_info.get("description", "No summary available")
            source = volume_info.get("infoLink", "No source available")

            desc = f'{i}. "{title}" by {authors}: {summary}\n'
            desc += f"You can read more at {source}"
            results.append(desc)

            i += 1

        return "\n\n".join(results)

    def _format_authors(self, authors: list) -> str:
        if not authors:
            return "Unknown Author"
        elif len(authors) == 1:
            return authors[0]
        else:
            return "{} and {}".format(", ".join(authors[:-1]), authors[-1])
