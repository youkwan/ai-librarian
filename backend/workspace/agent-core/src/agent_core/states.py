from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from agent_core.models.llmconfig import LLMConfig
from agent_core.models.toolcall import ToolCall


def tool_accumulator_or_reset(current_list: list[ToolCall], new_update_list: list[ToolCall]) -> list[ToolCall]:
    """Reducer that accumulates tool calls but resets if the update is an empty list."""
    if new_update_list == []:
        return []
    else:
        return current_list + new_update_list


class MessagesStateInput(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)


class MessagesState(MessagesStateInput):
    tools_used: Annotated[list[ToolCall], tool_accumulator_or_reset] = Field(default_factory=list)
