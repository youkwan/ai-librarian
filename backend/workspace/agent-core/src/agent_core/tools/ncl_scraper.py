import asyncio
import logging  # Consider using logging instead of print
import urllib.parse
from urllib.parse import urlparse, urlunparse

from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.async_api import (
    async_playwright,
)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class NCLScraper:
    """
    A scraper for the National Central Library (NCL) catalog using Playwright.
    Designed to perform advanced searches and extract book information.
    """

    ncl_entry_url: str = "https://aleweb.ncl.edu.tw/F"

    def __init__(self, headless_mode: bool = True):
        """
        Initializes the NCLScraper.

        Args:
            headless_mode: Run the browser in background (True) or visibly (False).
        """
        self.headless_mode = headless_mode

    async def _handle_route(self, route):
        """Blocks non-essential network resources."""
        resource_type = route.request.resource_type
        if resource_type in ["image", "stylesheet", "font", "media"]:
            try:
                await route.abort()
            except Exception:
                pass  # Ignore errors during abort
        else:
            try:
                await route.continue_()
            except Exception:
                pass  # Ignore errors during continue

    async def search(self, search_criteria: list) -> list:
        """
        Scrapes NCL using Advanced Search with specified field codes and terms.

        Args:
            search_criteria: List of tuples: (field_code, query_term). Max 3.

        Returns:
            List of dictionaries with scraped book info, or empty list on error/no results.
        """
        results_data = []
        query_repr = "; ".join([f"{code}={term}" for code, term in search_criteria])
        logger.info(f"--- Starting NCL Search: {query_repr} (Headless: {self.headless_mode}) ---")

        if not search_criteria or len(search_criteria) > 3:
            logger.error("Search criteria list is empty or exceeds 3 entries.")
            return []

        async with async_playwright() as p:
            browser = None
            context = None
            page = None
            try:
                # 1. Launch Browser
                logger.info("Launching browser...")
                browser = await p.chromium.launch(headless=self.headless_mode)
                context = await browser.new_context(
                    ignore_https_errors=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                )
                page = await context.new_page()
                logger.info("Browser context and page created.")

                # 2. Enable Request Blocking
                await page.route("**/*", self._handle_route)
                logger.info("Request blocking enabled.")

                # 3. Navigate to entry point & stabilize
                logger.info(f"Navigating to entry point: {self.ncl_entry_url}")
                await page.goto(self.ncl_entry_url, wait_until="load", timeout=90000)
                logger.info("Initial page load event fired, waiting for potential JS redirect...")
                landing_page_input_selector = 'input[name="request"]'
                try:
                    logger.info(f"Waiting for landing page element '{landing_page_input_selector}'...")
                    await page.locator(landing_page_input_selector).first.wait_for(state="visible", timeout=90000)
                    session_url = page.url
                    logger.info(f"JS redirect likely complete. Current URL: {session_url}")
                except PlaywrightTimeoutError:
                    logger.error(f"Timed out waiting for landing page element '{landing_page_input_selector}'.")
                    # Consider saving screenshot within the method if needed for debugging tools
                    # await page.screenshot(path="error_landing_page_timeout.png")
                    return []  # Return empty on failure

                # 4. Check for login page redirection
                try:
                    page_content_after_wait = await page.content()
                    if (
                        "func=login" in session_url
                        or "使用者登入" in page_content_after_wait
                        or "User login" in page_content_after_wait
                    ):
                        logger.error("Error: Redirected to login page.")
                        # Consider saving screenshot within the method if needed for debugging tools
                        # await page.screenshot(path="error_login_redirect.png")
                        return []
                except Exception as content_error:
                    logger.warning(f"Warning: Could not get page content after wait: {content_error}")

                # 5. Construct and Navigate to Advanced Search URL
                parsed_url = urlparse(session_url)
                base_session_path = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", ""))
                if base_session_path.endswith("/") and not parsed_url.path.endswith("/"):
                    base_session_path = base_session_path[:-1]

                # Ensure base_session_path doesn't end with the file part like 'start.do'
                # A safer way might be to always reconstruct from the base URL extracted earlier
                # Or ensure 'start.do' is removed if present. Let's refine this:
                if parsed_url.path and not parsed_url.path.endswith("/"):
                    base_path_parts = parsed_url.path.split("/")
                    # Assuming the structure is like /F/start.do or /F/
                    if len(base_path_parts) > 2 and "." in base_path_parts[-1]:  # Check if last part looks like a file
                        base_session_path = urlunparse(
                            (
                                parsed_url.scheme,
                                parsed_url.netloc,
                                "/".join(base_path_parts[:-1]),
                                "",
                                "",
                                "",
                            )
                        )
                    # Ensure it ends with a '/' if it's not just the root
                    if not base_session_path.endswith("/") and parsed_url.path != "/":
                        base_session_path += "/"

                advanced_search_url = (
                    f"{base_session_path}?func=find-d-0"  # Corrected logic for base path might be needed
                )
                logger.info(f"Constructed Advanced Search URL: {advanced_search_url}")
                await page.goto(advanced_search_url, wait_until="domcontentloaded", timeout=90000)
                logger.info(f"Navigated to Advanced Search page: {page.url}")

                # 6. Interact with the Advanced Search form
                adv_search_code_selector = 'select[name="find_code"]'
                adv_search_input_selector = 'input[name="request"]'
                adv_search_button_selector = 'input[type="image"][alt=" Go "]'  # Verify this selector if needed

                logger.info("Waiting for Advanced Search form elements...")
                await page.locator(adv_search_code_selector).first.wait_for(state="visible", timeout=60000)
                await page.locator(adv_search_input_selector).first.wait_for(state="visible", timeout=60000)
                await page.locator(adv_search_button_selector).first.wait_for(state="visible", timeout=60000)
                logger.info("Advanced Search form elements found.")

                logger.info("Filling Advanced Search criteria...")
                for i, (field_code, query_term) in enumerate(search_criteria):
                    if i >= 3:
                        break
                    logger.info(f"  - Setting row {i + 1}: Field='{field_code}', Term='{query_term}'")
                    await page.locator(adv_search_code_selector).nth(i).select_option(value=field_code)
                    await page.locator(adv_search_input_selector).nth(i).fill(query_term)
                    await page.wait_for_timeout(200)
                num_criteria = len(search_criteria)
                if num_criteria < 3:
                    for i in range(num_criteria, 3):
                        await page.locator(adv_search_code_selector).nth(i).select_option(index=0)
                        await page.locator(adv_search_input_selector).nth(i).fill("")

                logger.info(
                    f"Clicking Advanced Search submit button ('{adv_search_button_selector}') and waiting for navigation..."
                )
                async with page.expect_navigation(wait_until="domcontentloaded", timeout=90000):
                    await page.locator(adv_search_button_selector).first.click(timeout=60000)
                logger.info("Advanced Search submitted, navigation complete.")

                # 7. Handle potential intermediate page and RELOAD
                logger.info("Checking page after search submission...")
                results_link_selector = 'tr:has-text("查詢結果:") a[href*="func=short-0"]'
                list_view_row_selector = 'tr[valign="baseline"]'

                try:
                    # Check briefly for the intermediate link
                    logger.info(f"Checking for intermediate results link '{results_link_selector}' (short wait)...")
                    await page.locator(results_link_selector).first.wait_for(state="visible", timeout=15000)
                    logger.info("Intermediate link found. Clicking it and waiting for navigation...")
                    async with page.expect_navigation(wait_until="domcontentloaded", timeout=90000):
                        await page.locator(results_link_selector).first.click(timeout=30000)
                    logger.info("Intermediate link clicked, navigation complete.")
                except PlaywrightTimeoutError:
                    # Intermediate link not found, assume we are already on the destination page
                    logger.info("Intermediate link not found or timed out. Proceeding...")

                # === MODIFICATION: Unconditionally Reload ===
                logger.info("Reloading page to ensure list view format...")
                try:
                    await page.reload(wait_until="domcontentloaded", timeout=60000)
                    logger.info("Page reloaded successfully.")
                except PlaywrightTimeoutError:
                    logger.error("Error: Timed out during page reload.")
                    # Consider if we should attempt to proceed or fail here
                    # await page.screenshot(path="error_reload_timeout.png") # Optional screenshot
                    return []  # Fail if reload times out

                # 8. Wait for List View AFTER reload
                logger.info(f"Waiting for list view element '{list_view_row_selector}' after reload...")
                results_page_confirmed = False
                try:
                    await page.locator(list_view_row_selector).first.wait_for(state="visible", timeout=60000)
                    logger.info("List view element confirmed after reload.")
                    results_page_confirmed = True
                except PlaywrightTimeoutError:
                    # If list view isn't found even after reload, then likely no results or error
                    logger.error(f"Error: List view element ('{list_view_row_selector}') not found after reload.")
                    try:
                        page_content_final = await page.content()
                        if "查無資料" in page_content_final or "查不到" in page_content_final:
                            logger.info("Search returned no results.")
                        elif "使用者登入" in page_content_final or "User login" in page_content_final:
                            logger.error("Error: Page shows login prompt.")
                        else:
                            logger.info("Unknown page state after reload.")
                        # Consider saving screenshot within the method if needed for debugging tools
                        # await page.screenshot(path="error_final_results_unconfirmed.png")
                    except Exception as final_check_error:
                        logger.error(f"Error during final page check: {final_check_error}")
                    # results_page_confirmed remains False

                # 9. ***** Scrape results table ONLY if results page was confirmed *****
                if results_page_confirmed:
                    logger.info("Reached results list page. Scraping results data...")
                    current_url = page.url
                    item_selector = list_view_row_selector
                    list_items = await page.query_selector_all(item_selector)
                    logger.info(f"Found {len(list_items)} item rows.")

                    # --- Extraction Loop (remains the same) ---
                    for item_row in list_items:
                        # ... (Extraction logic is identical to previous version) ...
                        try:
                            title_element = await item_row.query_selector("td:nth-child(3) a.brieftit")
                            title = (await title_element.inner_text()).strip() if title_element else "N/A"
                            link_relative = await title_element.get_attribute("href") if title_element else None
                            link_absolute = urllib.parse.urljoin(current_url, link_relative) if link_relative else "N/A"
                            author_element = await item_row.query_selector("td:nth-child(4)")
                            author = (await author_element.inner_text()).strip() if author_element else "N/A"
                            publisher_element = await item_row.query_selector("td:nth-child(5)")
                            publisher = (
                                (await publisher_element.inner_text()).strip().removesuffix(",")
                                if publisher_element
                                else "N/A"
                            )
                            year_element = await item_row.query_selector("td:nth-child(6)")
                            year_full_text = await year_element.inner_text() if year_element else ""
                            year_str = (
                                "".join(filter(str.isdigit, year_full_text.splitlines()[-1])) if year_full_text else ""
                            )
                            year = year_str if year_str else "N/A"
                            callno_element = await item_row.query_selector("td:nth-child(7)")
                            call_number_raw = (await callno_element.inner_text()).strip() if callno_element else ""
                            call_number = call_number_raw if call_number_raw and call_number_raw != "<br>" else "N/A"
                            location_element = await item_row.query_selector("td:nth-child(8)")
                            location_texts = []
                            if location_element:
                                location_links = await location_element.query_selector_all("a")
                                if location_links:
                                    for link_loc in location_links:
                                        location_texts.append((await link_loc.inner_text()).strip())
                                else:
                                    raw_loc_text = (await location_element.inner_text()).strip()
                                    if raw_loc_text != "<br>":
                                        location_texts.append(raw_loc_text)
                            location = " | ".join(location_texts) if location_texts else "N/A"

                            if title != "N/A":
                                results_data.append(
                                    {
                                        "title": title,
                                        "author": author,
                                        "publisher": publisher,
                                        "year": year,
                                        "call_number": call_number,
                                        "location": location,
                                        "link": link_absolute,
                                    }
                                )
                        except Exception as item_error:
                            logger.warning(f"  - Error scraping one list item row: {item_error}")
                            continue
                    if not results_data and list_items:
                        logger.warning("Warning: Found item rows but failed to parse data from any of them.")

                else:
                    logger.info("Skipping scraping as results page could not be confirmed after reload attempt.")

            # --- Error Handling & Cleanup ---
            except PlaywrightTimeoutError as te:
                logger.error(f"Operation timed out: {te}")
                # if page and not page.is_closed():
                # Optional screenshot saving
                # await page.screenshot(path="error_timeout.png")

                logger.info("Timeout error screenshot saved.")
            except Exception as e:
                logger.error(f"An unexpected error occurred during scraping: {e}", exc_info=True)  # Log stack trace
                # if page and not page.is_closed():
                # Optional screenshot saving
                # await page.screenshot(path="error_general.png")
                logger.info("General error screenshot saved.")
            finally:
                if context:
                    await context.close()
                if browser and browser.is_connected():
                    await browser.close()
                logger.info("Browser closed.")

        logger.info(f"--- Search Finished: {query_repr} - Found {len(results_data)} results ---")
        return results_data


# --- Example Usage (Outside the class, for testing or integration) ---
async def run_ncl_search():
    scraper = NCLScraper(headless_mode=False)
    search_criteria_list = [
        ("WTI", "人工智慧來了"),
        ("WAU", "李開復"),
    ]
    results = await scraper.search(search_criteria_list)

    if results:
        print("\n--- === Scraped Results === ---")
        for i, book in enumerate(results):
            print(f"{i + 1}. Title: {book.get('title', 'N/A')}")
            # ... print other fields ...
            print("-" * 20)
    else:
        print("\n--- === No results were extracted === ---")


if __name__ == "__main__":
    asyncio.run(run_ncl_search())
