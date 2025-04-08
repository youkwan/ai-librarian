import operator
from typing import Annotated, List
from pydantic import BaseModel, Field
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage

from app.models.llmconfig import LLMConfig
from app.models.toolcall import ToolCall


class MessagesStateInput(BaseModel):
    messages: Annotated[List[AnyMessage], add_messages] = Field(default_factory=list)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    max_steps: int = Field(default=10, ge=1)


class MessagesState(MessagesStateInput):
    current_step: int = Field(default=0)
    tools_used: Annotated[List[ToolCall], operator.add] = Field(default_factory=list)
