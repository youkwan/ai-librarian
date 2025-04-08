from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    allowed_origins: list[str] = []
