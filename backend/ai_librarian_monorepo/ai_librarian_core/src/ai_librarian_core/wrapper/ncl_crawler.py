import urllib.parse
from dataclasses import dataclass

from playwright.sync_api import BrowserContext, Page, TimeoutError, sync_playwright
from pydantic import BaseModel, Field

NCL_ENTRY_URL = "https://aleweb.ncl.edu.tw/F"


class NCLCrawlerCookieTimeoutError(Exception):
    pass


@dataclass
class NCLCrawlerSessionIdNotFoundError(Exception):
    pass


@dataclass
class NCLCrawlerSearchTimeoutError(Exception):
    pass


@dataclass
class NCLCrawlerSearchNoResultsError(Exception):
    pass


class NCLCrawler(BaseModel):
    """A crawler for the National Central Library (NCL) catalog."""

    top_k_results: int = Field(default=10, ge=1, le=20)
    cookie_timeout: int = Field(default=10000, ge=1000)
    search_timeout: int = Field(default=10000, ge=1000)

    def _process_workflow(self, query: str) -> list[dict[str, str]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "stylesheet", "font", "media"]
                    or "google-analytics.com" in route.request.url
                    else route.continue_()
                ),
            )
            session_id = self._get_session_id(context, page)
            results = self._search_ncl_results(query, session_id, page)
            return results

    def _get_session_id(self, context: BrowserContext, page: Page) -> str:
        page.goto(NCL_ENTRY_URL)
        try:
            page.wait_for_function("() => document.cookie.includes('ALEPH_SESSION_ID')", timeout=self.cookie_timeout)
        except TimeoutError as e:
            raise NCLCrawlerCookieTimeoutError() from e

        all_cookies = context.cookies()

        for cookie in all_cookies:
            if cookie["name"] == "ALEPH_SESSION_ID":
                return cookie["value"]
        raise NCLCrawlerSessionIdNotFoundError()

    def _encode_query(self, query: str) -> str:
        return urllib.parse.quote(query)

    def _search_ncl_results(self, query: str, session_id: str, page: Page) -> list[dict[str, str]]:
        encoded_query = self._encode_query(query)

        try:
            page.goto(
                f"{NCL_ENTRY_URL}/{session_id}?func=find-b&request={encoded_query}&find_code=WTI&adjacent=Y&local_base=&x=0&y=0&filter_code_1=WLN&filter_request_1=&filter_code_2=WYR&filter_request_2=&filter_code_3=WYR&filter_request_3=&filter_code_4=WMY&filter_request_4=&filter_code_5=WSL&filter_request_5="
            )
            page.wait_for_selector('tr[valign="baseline"] td:nth-child(3) a.brieftit', timeout=self.search_timeout)
        except TimeoutError as e:
            raise NCLCrawlerSearchTimeoutError() from e

        result_rows_locator = page.locator('tr[valign="baseline"]')
        num_rows = result_rows_locator.count()
        if num_rows <= 0:
            raise NCLCrawlerSearchNoResultsError()

        results = []
        count = 0

        for i in range(num_rows):
            row_locator = result_rows_locator.nth(i)
            title_link_locator = row_locator.locator("td:nth-child(3) a.brieftit")

            book_title = None
            book_link = None

            if title_link_locator.count() > 0:
                book_title = title_link_locator.text_content()
                book_link = title_link_locator.get_attribute("href")

            author_locator = row_locator.locator("td:nth-child(4)")
            author = author_locator.text_content()

            if book_title:
                book_title = book_title.strip()
            if book_link:
                if not book_link.startswith("http"):
                    book_link = page.url.split("/F/")[0] + book_link
                book_link = book_link.strip()
            if author:
                author = author.strip()

            if book_title and book_link:
                results.append({"title": book_title, "author": author, "link": book_link})
                count += 1
                if count >= self.top_k_results:
                    break
        return results

    def run(self, query: str) -> str:
        results = self._process_workflow(query)
        return "\n".join(
            [f"{i + 1}. {result['title']} ({result['author']}) - {result['link']}" for i, result in enumerate(results)]
        )
