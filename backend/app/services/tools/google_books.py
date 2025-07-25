import httpx
from typing import List
from pydantic import BaseModel

from app.core.settings import settings

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"


class GoogleBooksClient(BaseModel):
    """Wrapper around Google Books API.
    This wrapper will use the Google Books API to conduct searches and
    fetch books based on a query passed in by the agents. By default,
    it will return the top-k results.

    The response for each book will contain the book title, author name, summary, and
    a source link.
    """

    google_books_api_key: str = settings.google_books_api_key
    top_k_results: int = settings.max_google_books_search_results

    async def arun(self, query: str) -> str:
        params = {
            "q": query,
            "maxResults": self.top_k_results,
            "key": self.google_books_api_key,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(GOOGLE_BOOKS_API_URL, params=params)
                response.raise_for_status()
                json_response = response.json()
            except httpx.RequestError as exc:
                return f"An error occurred while requesting {exc.request.url!r}: {exc}"
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                try:
                    error_details = exc.response.json()
                    error = error_details.get("error", {}).get(
                        "message", f"HTTP error {code}"
                    )
                except Exception:
                    error = f"HTTP error {code}"
                return f"Unable to retrieve books, received status code {code}: {error}"

        return self._format(query, json_response.get("items", []))

    def _format(self, query: str, books: List) -> str:
        if not books:
            return f"Sorry no books could be found for your query: {query}"

        start = f"Here are {len(books)} suggestions for books related to {query}:"

        results = []
        results.append(start)
        i = 1

        for book in books:
            info = book.get("volumeInfo", {})
            title = info.get("title", "No title available.")
            authors = self._format_authors(info.get("authors", ["N/A"]))
            summary = info.get("description", "No description available.")
            source = info.get("infoLink", "No link available.")

            desc = f'{i}. "{title}" by {authors}: {summary}\n'
            desc += f"You can read more at {source}"
            results.append(desc)

            i += 1

        return "\n\n".join(results)

    def _format_authors(self, authors: List) -> str:
        if len(authors) == 1:
            return authors[0]
        return "{} and {}".format(", ".join(authors[:-1]), authors[-1])
