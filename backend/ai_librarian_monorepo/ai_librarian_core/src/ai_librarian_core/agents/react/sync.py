from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

from ai_librarian_core.agents.react.base import BaseReactAgent, MissingAIMessageError, ReactAgentError
from ai_librarian_core.agents.react.state import MessagesState
from ai_librarian_core.agents.utils import get_thread_id
from ai_librarian_core.models.llm_config import LLMConfig
from ai_librarian_core.models.used_tool import UsedTool
from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode


@dataclass
class ReactAgent(BaseReactAgent):
    def __post_init__(self):
        super().__post_init__()

    @property
    def workflow(self) -> CompiledStateGraph:
        return self._init_workflow()

    def _clear_used_tools(self, state: MessagesState) -> dict[str, list[UsedTool]]:
        return {"used_tools": []}

    def _invoke_llm(self, state: MessagesState) -> dict[str, list[BaseMessage]]:
        llm_config = state.llm_config
        llm = self._init_llm(llm_config)
        messages = state.messages

        try:
            response = llm.invoke(messages)
            return {"messages": [response]}
        # TODO(youkwan): Handle specific errors (couldn't find docs).
        except Exception as e:
            raise ReactAgentError("An unexpected error occurred while trying to invoke the chat model.") from e

    def _route(self, state: MessagesState) -> Literal["tools", "__end__"]:
        messages = state.messages
        last_message = messages[-1]
        if not isinstance(last_message, AIMessage):
            raise MissingAIMessageError(f"Expected AIMessage in output edges, but got {type(last_message).__name__}")
        if last_message.tool_calls:
            return "tools"
        return "__end__"

    def _catch_tool_massage(self, state: MessagesState) -> dict[str, list[UsedTool]]:
        messages = state.messages
        used_tools = [
            UsedTool(name=msg.name, output=msg.content) for msg in reversed(messages) if isinstance(msg, ToolMessage)
        ]
        if used_tools:
            used_tools.reverse()
            return {"used_tools": used_tools}

    def _init_workflow(self) -> CompiledStateGraph:
        workflow = StateGraph(state_schema=self.state_schema)
        invoke_llm = self._invoke_llm
        workflow.add_node("clear_used_tools", self._clear_used_tools)
        workflow.add_node("invoke_llm", invoke_llm)
        tool_node = ToolNode(self.tools)
        workflow.add_node("catch_tool_massage", self._catch_tool_massage)
        workflow.add_node("tools", tool_node)
        workflow.set_entry_point("clear_used_tools")
        workflow.add_edge("clear_used_tools", "invoke_llm")
        workflow.add_conditional_edges(
            "invoke_llm",
            self._route,
        )
        workflow.add_edge("catch_tool_massage", "invoke_llm")
        workflow.add_edge("tools", "catch_tool_massage")
        workflow.add_edge("catch_tool_massage", "invoke_llm")
        return workflow.compile(name=self.name, checkpointer=self.checkpointer)

    def run(
        self, messages: list[AnyMessage], thread_id: str | None = None, llm_config: LLMConfig = LLMConfig()
    ) -> tuple[AIMessage, list[UsedTool]]:
        state = MessagesState(messages=messages, llm_config=llm_config)
        result = self.workflow.invoke(state, config={"configurable": {"thread_id": thread_id or get_thread_id()}})
        return result["messages"][-1], result["used_tools"]

    def stream(
        self, messages: list[AnyMessage], thread_id: str | None = None, llm_config: LLMConfig = LLMConfig()
    ) -> Iterator[dict[str, list[BaseMessage]]]:
        state = MessagesState(messages=messages, llm_config=llm_config)
        return self.workflow.stream(
            state,
            stream_mode="messages",
            config={"configurable": {"thread_id": thread_id or get_thread_id()}},
        )


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    from ai_librarian_core.tools.tools import init_built_in_tools

    tools = init_built_in_tools()

    agent = ReactAgent(tools=tools)
    messages, used_tools = agent.run([HumanMessage(content="請問現在幾號，幫我查今天發生什麼新聞")], thread_id="test-5")
    print(type(messages), messages)
    print(type(used_tools), used_tools)

    result = agent.stream([HumanMessage(content="請問現在幾點")], thread_id="test")
    for r in result:
        print(type(r), r)
