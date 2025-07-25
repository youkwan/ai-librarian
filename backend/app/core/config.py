from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.llmconfig import Model

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DOTENV_PATH = BASE_DIR / ".env"

if not DOTENV_PATH.is_file():
    raise FileNotFoundError(f".env file not found at expected location: {DOTENV_PATH}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(DOTENV_PATH),
        env_ignore_empty=True,
        extra="ignore",
    )

    # API settings
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: list[str] | None = Field(default_factory=list)

    # Default llm to use in agent
    default_llm: Model = Model.GPT_4O_MINI
    default_temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    default_max_tokens: int | None = None

    # LLM API keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    groq_api_key: str | None = None

    # Langsmith settings
    langsmith_tracing: bool = False
    langsmith_project: str | None = None
    langsmith_api_key: str | None = None

    # DuckDuckGo setting
    max_web_search_results: int = Field(default=5, gt=0)

    # Google Books setting
    google_books_api_key: str | None = None
    max_google_books_search_results: int = Field(default=5, gt=0)

    # Arxiv setting
    top_k_results: int = 3
    arxiv_max_query_length: int = 300
    continue_on_failure: bool = False
    load_max_docs: int = 100
    load_all_available_meta: bool = False
    doc_content_chars_max: int = 40000

    # Wikipedia setting
    wikipedia_lang: str = "en"
    wikipedia_top_k_results: int = 3
    wikipedia_load_all_available_meta: bool = False
    wikipedia_doc_content_chars_max: int = 4000

    @model_validator(mode="after")
    def check_at_least_one_llm_api_key(self) -> "Settings":
        if all(
            key is None
            for key in [
                self.openai_api_key,
                self.anthropic_api_key,
                self.google_api_key,
                self.groq_api_key,
            ]
        ):
            raise ValueError(
                "At least one LLM API key must be provided (one of: openai_api_key, anthropic_api_key, google_api_key, groq_api_key)"
            )
        return self

    @model_validator(mode="after")
    def check_langsmith_settings(self) -> "Settings":
        if self.langsmith_tracing and self.langsmith_api_key is None:
            raise ValueError(
                "langsmith_api_key is required when langsmith_tracing is enabled."
            )
        return self


settings = Settings()


if __name__ == "__main__":
    from rich.pretty import pprint

    pprint(settings)
