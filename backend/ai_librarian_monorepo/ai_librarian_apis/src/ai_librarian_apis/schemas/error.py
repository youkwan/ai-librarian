from pydantic import BaseModel, Field


class BaseError(BaseModel):
    detail: str | None = Field(
        description="The message of the error.",
        default="Internal server error.",
        examples=["Internal server error."],
    )
