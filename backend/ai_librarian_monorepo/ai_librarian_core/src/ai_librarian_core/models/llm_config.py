from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Model(StrEnum):
    """Enumeration of supported language models (LLMs).

    This enum can be extended with any model listed in the LangChain chat models documentation:
    https://python.langchain.com/docs/integrations/chat/

    Note: The first model in this enum will be displayed as the default model in ReDoc,
    since ReDoc does not respect Pydantic's default settings like Swagger and uses the first enum value as default.
    """

    # OpenAI
    GPT_4O_MINI = "openai:gpt-4o-mini"  # First model will be the default in ReDoc
    GPT_4O = "openai:gpt-4o"
    GPT_4_5_PREVIEW = "openai:gpt-4.5-preview"
    O3_MINI = "openai:o3-mini"
    O1_MINI = "openai:o1-mini"
    O1 = "openai:o1"

    # Anthropic
    CLAUDE_3_7_SONNET = "anthropic:claude-3-7-sonnet-latest"
    CLAUDE_3_5_HAIKU = "anthropic:claude-3-5-haiku-latest"
    CLAUDE_3_5_SONNET_V2 = "anthropic:claude-3-5-sonnet-latest"
    CLAUDE_3_5_SONNET = "anthropic:claude-3-5-sonnet-20240620"

    # Google GenAI
    GEMINI_2_5_PRO_EXP_03_25 = "google_genai:gemini-2.5-pro-exp-03-25"
    GEMINI_2_0_FLASH = "google_genai:gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE = "google_genai:gemini-2.0-flash-lite"
    GEMINI_1_5_FLASH = "google_genai:gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "google_genai:gemini-1.5-flash-8b"
    GEMINI_1_5_PRO = "google_genai:gemini-1.5-pro"

    # Groq
    LLAMA_4_SCOUT_17B_16E_INSTRUCT = "groq:meta-llama/llama-4-scout-17b-16e-instruct"
    LLAMA_3_3_70B_VERSATILE = "groq:llama-3.3-70b-versatile"
    LLAMA_3_3_70B_SPECDEC = "groq:llama-3.3-70b-specdec"
    LLAMA_3_2_1B_PREVIEW = "groq:llama-3.2-1b-preview"
    LLAMA_3_2_3B_PREVIEW = "groq:llama-3.2-3b-preview"
    LLAMA_3_1_8B_INSTANT = "groq:llama-3.1-8b-instant"
    MISTRAL_SABA_24B = "groq:mistral-saba-24b"
    QWEN_QWQ_32B = "groq:qwen-qwq-32b"
    QWEN_2_5_CODER_32B = "groq:qwen-2.5-coder-32b"
    QWEN_2_5_32B = "groq:qwen-2.5-32b"
    DEEPSEEK_R1_DISTILL_QWEN_32B = "groq:deepseek-r1-distill-qwen-32b"
    DEEPSEEK_R1_DISTILL_LLAMA_70B = "groq:deepseek-r1-distill-llama-70b"

    @classmethod
    def list(cls) -> list[str]:
        return [model.value for model in cls]


class LLMConfig(BaseModel):
    """The settings behind the Agent's LLM core.

    Controls the behavior and output characteristics of the language model.
    """

    model: Model = Field(
        default=Model.GPT_4O_MINI,
        description="The specific LLM model identifier to use for processing requests.",
        examples=[Model.GPT_4O_MINI],
    )
    temperature: float = Field(
        default=1,
        description=(
            "Controls randomness of outputs. "
            "Higher values make output more random, lower values make output more deterministic."
        ),
        examples=[1],
        ge=0,
        le=2,
    )
    max_tokens: int | None = Field(
        default=None,
        description=(
            "Maximum number of tokens (words/word pieces) to generate in the response. "
            "None means no specific limit beyond model's context length."
        ),
        examples=[None],
    )

    model_config = ConfigDict(frozen=True)
