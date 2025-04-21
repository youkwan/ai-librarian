from duckduckgo_search import DDGS

from app.core.settings import SETTINGS

# result = DDGS().text("What is the capital of France?", max_results=5)
# print(result)


result = DDGS().news(
    "誰是台灣總統?",
    max_results=SETTINGS.max_web_search_results,
    region="tw-tzh",
)
print(result)
