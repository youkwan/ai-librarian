from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define the path to the .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOTENV_PATH = BASE_DIR / ".env"

if not DOTENV_PATH.is_file():
    raise FileNotFoundError(f".env file not found at expected location: {DOTENV_PATH}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(DOTENV_PATH), env_ignore_empty=True)

    # API settings
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: list[str] | None = Field(default_factory=list)

    # Default llm to use in agent
    default_llm: str = "gpt-4o-mini"
    default_temperature: float = 1.0
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
