from typing import Annotated
from pydantic import BaseModel, Field, field_validator
from langchain_core.messages import AnyMessage
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import add_messages


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
    )
    max_tokens: int | None = Field(
        default=None,
        description="Maximum number of tokens (words/word pieces) to generate in the response. None means no specific limit beyond model's context length.",
        examples=[None],
    )

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if v < 0 or v > 2:
            raise ValueError("Temperature must be between 0 and 2.")
        return v


class ChatState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages] = Field(...)
    llm_config: LLMConfig = Field(...)

    def init_model(self) -> BaseChatModel:
        return init_chat_model(**self.llm_config.model_dump(exclude_none=True))
