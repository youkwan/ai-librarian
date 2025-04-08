from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
from typing import List
from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
    AIMessage,
    HumanMessage,
)
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from app.models.llmconfig import LLMConfig
from app.models.toolcall import ToolCall


class HealthResponse(BaseModel):
    """
    Health check response schema. Returns 'ok' status when the API endpoint is operational.
    Used for monitoring system health and availability.
    """

    status: str = Field(
        default="ok",
        description="API operational status indicator. Returns 'ok' when the system is functioning properly.",
    )


# class Model(str, Enum):
#     """
#     Enumeration of supported language models (LLMs).
#     This enum can be extended with any model listed in the LangChain chat models documentation:
#     https://python.langchain.com/docs/integrations/chat/
#     """

#     O3_MINI = "o3-mini"
#     O1 = "o1"
#     O1_MINI = "o1-mini"
#     GPT_4O = "gpt-4o"
#     GPT_4O_MINI = "gpt-4o-mini"
#     CLAUDE_3_7_SONNET = "claude-3-7-sonnet-latest"
#     CLAUDE_3_5_HAIKU = "claude-3-5-haiku-latest"
#     CLAUDE_3_5_SONNET = "claude-3-5-sonnet-latest"
#     GEMINI_2_0_FLASH = "google_genai:gemini-2.0-flash"
#     GEMINI_2_0_FLASH_LITE = "google_genai:gemini-2.0-flash-lite"
#     GEMINI_1_5_FLASH = "google_genai:gemini-1.5-flash"
#     GEMINI_1_5_FLASH_8B = "google_genai:gemini-1.5-flash-8b"
#     GEMINI_1_5_PRO = "google_genai:gemini-1.5-pro"
#     LLAMA_3_3_70B_VERSATILE = "groq:llama-3.3-70b-versatile"
#     LLAMA_3_2_1B_PREVIEW = "groq:llama-3.2-1b-preview"
#     LLAMA_3_1_8B_INSTANT = "groq:llama-3.1-8b-instant"
#     MIXTRAL_8X7B_32768 = "groq:mixtral-8x7b-32768"
#     QWEN_QWQ_32B = "groq:qwen-qwq-32b"
#     QWEN_2_5_32B = "groq:qwen-2.5-32b"
#     DEEPSEEK_R1_DISTILL_QWEN_32B = "groq:deepseek-r1-distill-qwen-32b"


class Role(str, Enum):
    """
    Enumeration of possible message roles in a conversation.
    Follows the OpenAI chat completion API convention.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class OpenAIMessage(BaseModel):
    """
    OpenAI style message schema following the chat completion API format.
    Used to structure conversation messages between system, user, and assistant.
    """

    role: Role = Field(
        ...,
        description="The role of the message sender (system, user, or assistant). Determines how the message is processed and displayed.",
        examples=[Role.ASSISTANT],
    )
    content: str = Field(
        ...,
        description="The actual message content or prompt text. Contains the information being exchanged in the conversation.",
        examples=["Hello, who are you?"],
    )


class AegntRequest(BaseModel):
    """
    Chat request schema defining the structure of incoming chat API requests.
    Contains all parameters needed to process a conversation with the Agent.
    """

    thread_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        examples=["ab586827-8c7c-4bf9-a6c9-fea58f43f5fc"],
        description="Unique identifier to track and maintain conversation state. If provided, the existing conversation will be continued. If not provided, a new conversation thread will be created automatically.",
    )
    messages: List[OpenAIMessage] = Field(
        default_factory=list,
        description="Array of conversation messages between user, assistant and system used to generate a contextual response. Can include multiple sequential messages to maintain conversation history.",
        examples=[
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Tell me about the weather in Tokyo."},
            ]
        ],
    )
    llm_config: LLMConfig = Field(
        default_factory=LLMConfig,
        description="Configuration settings for the Large Language Model processing the request. Controls model selection and generation parameters.",
    )
    max_steps: int = Field(
        default=20,
        ge=1,
        description="Maximum number of internal LLM reasoning steps or API calls allowed for processing this request. Prevents infinite loops. Default is 10 means it will try to solve problem within 10 steps or less. Increase this value if you want the agent to be able to handle more complex or multi-step requests.",
    )

    def get_langchain_messages(self) -> List[AnyMessage]:
        langchain_messages = []
        for openai_message in self.messages:
            if openai_message.role == "system":
                langchain_messages.append(
                    SystemMessage(
                        content=openai_message.content,
                        additional_kwargs={"__openai_role__": "developer"},
                    )
                )
            elif openai_message.role == "assistant":
                langchain_messages.append(AIMessage(content=openai_message.content))
            else:
                langchain_messages.append(HumanMessage(content=openai_message.content))
        return langchain_messages

    def get_runnable_config(self) -> dict:
        return {"configurable": {"thread_id": self.thread_id}}

    def init_model(self) -> BaseChatModel:
        return init_chat_model(**self.llm_config.model_dump(exclude_none=True))


class AgentResponse(BaseModel):
    """
    Agent response schema defining the structure of outgoing agent API responses.
    Contains the generated message and metadata about the interaction.
    """

    thread_id: str = Field(
        ...,
        description="Unique identifier of the conversation thread. Can be supplied in subsequent requests to continue this conversation context.",
        examples=[str(uuid.uuid4())],
    )
    llm_config: LLMConfig = Field(
        ...,
        description="Configuration settings for the Large Language Model processing the request. Controls model selection and generation parameters.",
        examples=[LLMConfig()],
    )
    messages: List[OpenAIMessage] = Field(
        ...,
        description="Array of messages generated by the LLM in response to the request. Usually contains one assistant response message.",
        examples=[
            [
                {
                    "role": "assistant",
                    "content": "The weather in Tokyo is sunny and warm.",
                }
            ]
        ],
    )
    tools_used: List[ToolCall] = Field(
        default_factory=list,
        description="Array of external tools or APIs that were called by the Agent during response generation. Empty if no tools were used.",
        examples=[
            [
                ToolCall(
                    name="get_temperature", output="The temperature in Tokyo is 20°C"
                ),
                ToolCall(name="get_humidity", output="The humidity in Tokyo is 50%"),
            ]
        ],
    )
