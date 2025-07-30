from dataclasses import dataclass
from typing import Annotated, Literal

from ai_librarian_core.models.llmconfig import LLMConfig
from langchain.chat_models import init_chat_model
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from pydantic import Field


class WorkflowError(Exception):
    pass


class InvalidChatModelError(WorkflowError):
    pass


class ChatModelImportError(WorkflowError):
    pass


class AIMessageMissingError(WorkflowError):
    pass


@dataclass
class MessagesState:
    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)


@dataclass
class ReactWorkflow:
    tools: list[BaseTool]
    name: str = "react_workflow"
    checkpointer: BaseCheckpointSaver = InMemorySaver()

    def __post_init__(self):
        self._llm_cache: dict[LLMConfig, BaseChatModel] = {}
        self.state_schema: MessagesState = MessagesState
        self.workflow: CompiledStateGraph = self._init_workflow()

    def _init_llm(self, llm_config: LLMConfig) -> BaseChatModel:
        if llm_config in self._llm_cache:
            return self._llm_cache[llm_config]

        try:
            llm = init_chat_model(
                model=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
            )
            llm_with_tools = llm.bind_tools(self.tools)
            self._llm_cache[llm_config] = llm_with_tools
            return llm_with_tools
        except ValueError as e:
            raise InvalidChatModelError("Model_provider cannot be inferred or isn’t supported.") from e
        except ImportError as e:
            raise ChatModelImportError("Model provider integration package is not installed.") from e
        except Exception as e:
            raise WorkflowError("An unexpected error occurred while trying to initialize the chat model.") from e

    def _call_llm(self, state: MessagesState) -> dict[str, list[BaseMessage]]:
        llm_config = state.llm_config
        llm = self._init_llm(llm_config)
        messages = state.messages

        try:
            response = llm.invoke(messages)
            return {"messages": [response]}
        # TODO(youkwan): Handle specific errors (couldn't find any docs)
        except Exception as e:
            raise WorkflowError("An unexpected error occurred while trying to invoke the chat model.") from e

    def _should_continue(self, state: MessagesState) -> Literal["tools", "__end__"]:
        messages = state.messages
        last_message = messages[-1]
        if not isinstance(last_message, AIMessage):
            raise AIMessageMissingError(f"Expected AIMessage in output edges, but got {type(last_message).__name__}")
        if last_message.tool_calls:
            return "tools"
        return "__end__"

    def _init_workflow(self) -> CompiledStateGraph:
        workflow = StateGraph(self.state_schema)
        call_llm = self._call_llm
        workflow.add_node("call_llm", call_llm)
        tool_node = ToolNode(self.tools)
        workflow.add_node("tools", tool_node)
        workflow.set_entry_point("call_llm")
        workflow.add_conditional_edges(
            "call_llm",
            self._should_continue,
        )
        workflow.add_edge("tools", "call_llm")
        return workflow.compile(name=self.name, checkpointer=self.checkpointer)

    def invoke(self, messages: list[AnyMessage], llm_config: LLMConfig) -> dict[str, list[BaseMessage]]:
        state = MessagesState(messages=messages, llm_config=llm_config)
        return self.workflow.invoke(state, config={"configurable": {"thread_id": "123"}})


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    from ai_librarian_core.tools.date_time import DateTimeTool

    workflow = ReactWorkflow(tools=[DateTimeTool()])
    print(
        workflow.invoke(
            [HumanMessage(content="What is the current time?")],
            LLMConfig(model="openai:gpt-4o-mini", temperature=0.0, max_tokens=1000),
        )
    )
