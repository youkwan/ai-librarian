from typing import Annotated

from ai_librarian_core.models.llmconfig import LLMConfig
from ai_librarian_core.models.used_tool import UsedTool
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


def accumulator_or_reset_used_tools(current_list: list[UsedTool], update_list: list[UsedTool]) -> list[UsedTool]:
    """Reducer that accumulates tool calls but resets if the update is an empty list."""
    if update_list == []:
        return []
    else:
        return current_list + update_list


class MessagesStateInput(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)


class MessagesState(MessagesStateInput):
    tools_used: Annotated[list[UsedTool], accumulator_or_reset_used_tools] = Field(default_factory=list)
