from enum import Enum
from pydantic import BaseModel, Field


class Model(str, Enum):
    """
    Enumeration of supported language models (LLMs).
    This enum can be extended with any model listed in the LangChain chat models documentation:
    https://python.langchain.com/docs/integrations/chat/

    Note: The first model in this enum will be displayed as the default model in ReDoc,
    since ReDoc does not respect Pydantic's default settings like Swagger and uses the first enum value as default.
    """

    GPT_4O_MINI = "gpt-4o-mini"  # First model will be the default in ReDoc
    GPT_4O = "gpt-4o"
    O3_MINI = "o3-mini"
    O1 = "o1"
    O1_MINI = "o1-mini"
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-latest"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-latest"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-latest"
    GEMINI_2_0_FLASH = "google_genai:gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE = "google_genai:gemini-2.0-flash-lite"
    GEMINI_1_5_FLASH = "google_genai:gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "google_genai:gemini-1.5-flash-8b"
    GEMINI_1_5_PRO = "google_genai:gemini-1.5-pro"
    LLAMA_3_3_70B_VERSATILE = "groq:llama-3.3-70b-versatile"
    LLAMA_3_2_1B_PREVIEW = "groq:llama-3.2-1b-preview"
    LLAMA_3_1_8B_INSTANT = "groq:llama-3.1-8b-instant"
    MIXTRAL_8X7B_32768 = "groq:mixtral-8x7b-32768"
    QWEN_QWQ_32B = "groq:qwen-qwq-32b"
    QWEN_2_5_32B = "groq:qwen-2.5-32b"
    DEEPSEEK_R1_DISTILL_QWEN_32B = "groq:deepseek-r1-distill-qwen-32b"

    @classmethod
    def list(cls) -> list[str]:
        return [model.value for model in cls]


class LLMConfig(BaseModel):
    """
    The settings behind the Agent's LLM core.
    Controls the behavior and output characteristics of the language model.
    """

    model: Model = Field(
        default=Model.GPT_4O_MINI,
        description="The specific LLM model identifier to use for processing requests.",
        examples=[Model.GPT_4O_MINI],
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
