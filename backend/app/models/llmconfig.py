from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """
    The settings behind the Agent's LLM core.
    Controls the behavior and output characteristics of the language model.
    """

    model: str = Field(
        default="gpt-4o-mini",
        description="The specific LLM model identifier to use for processing requests.",
        examples=["gpt-4o-mini"],
    )
    temperature: float = Field(
        default=1,
        description="Controls randomness of outputs. Higher values (0.8-1.0) make output more random, lower values (0.2-0.5) make output more deterministic.",
        examples=[1],
        ge=0,
        le=2,
    )
    max_tokens: int | None = Field(
        default=None,
        description="Maximum number of tokens (words/word pieces) to generate in the response. None means no specific limit beyond model's context length.",
        examples=[None],
    )
