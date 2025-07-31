from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    """Enumeration of possible message roles in a conversation.

    Follows the OpenAI chat completion API convention.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class OpenAIMessage(BaseModel):
    """OpenAI style message schema following the chat completion API format.

    Used to structure conversation messages between system, user, and assistant.
    """

    role: Role = Field(
        ...,
        description=(
            "The role of the message sender (system, user, or assistant). "
            "Determines how the message is processed and displayed."
        ),
        examples=[Role.ASSISTANT],
    )
    content: str = Field(
        ...,
        description=(
            "The actual message content or prompt text. Contains the information being exchanged in the conversation."
        ),
        examples=["Hello, who are you?"],
    )
