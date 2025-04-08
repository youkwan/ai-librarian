from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import List
from langchain_core.messages import AnyMessage, SystemMessage, AIMessage, HumanMessage
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from app.models.llmconfig import LLMConfig, Model
from app.models.toolcall import ToolCall
from app.utils import generate_thread_id


class HealthResponse(BaseModel):
    """
    Health check response schema. Returns 'ok' status when the API endpoint is operational.
    Used for monitoring system health and availability.
    """

    status: str = Field(
        default="ok",
        description="API operational status indicator. Returns 'ok' when the system is functioning properly.",
    )


class ModelResponse(BaseModel):
    """
    Model response schema. Returns the list of available models.
    """

    models: list[Model] = Field(
        ...,
        description="The list of available models.",
        examples=[Model.list()],
    )


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
        default_factory=generate_thread_id,
        examples=["thread-ab586827-8c7c-4bf9-a6c9-fea58f43f5fc"],
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
        examples=[generate_thread_id()],
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
