import asyncio
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from agent_core.states import MessagesState, MessagesStateInput
from agent_core.tools.tools import TOOLS


def reset_tools_used(state: MessagesState) -> dict[str, list[AnyMessage]]:
    return {"tools_used": []}


async def call_llm(state: MessagesState) -> dict[str, list[BaseMessage]]:
    llm_config = state.llm_config

    llm = init_chat_model(
        model=llm_config.model,
        temperature=llm_config.temperature,
        max_tokens=llm_config.max_tokens,
    )
    llm_with_tools = llm.bind_tools(TOOLS)

    messages = state.messages

    # https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html#langchain.chat_models.base.init_chat_model
    try:
        response = await llm_with_tools.ainvoke(messages)
    except ValueError as e:
        raise e
    except ImportError as e:
        raise e
    except Exception as e:
        raise e

    return {"messages": [response]}


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    messages = state.messages
    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(f"Expected AIMessage in output edges, but got {type(last_message).__name__}")
    if last_message.tool_calls:
        return "tools"
    return "__end__"


def create_react_graph(name: str) -> CompiledStateGraph:
    graph = StateGraph(state_schema=MessagesState, input=MessagesStateInput)
    graph.add_node(reset_tools_used)
    graph.add_node(call_llm)
    tool_node = ToolNode(TOOLS)
    graph.add_node(tool_node)
    graph.set_entry_point("reset_tools_used")
    graph.add_edge("reset_tools_used", "call_llm")
    graph.add_conditional_edges(
        "call_llm",
        should_continue,
    )
    graph.add_edge("tools", "call_llm")
    checkpointer = InMemorySaver()
    return graph.compile(name=name, checkpointer=checkpointer)


react_graph = create_react_graph("react_graph")


if __name__ == "__main__":
    from dotenv import load_dotenv
    from rich.pretty import pprint

    load_dotenv()

    async def stream_tokens():
        async for event in react_graph.astream(
            input={
                # "messages": [HumanMessage("what is the temperature in taipei?")],
                "messages": [HumanMessage("請推薦一些關於人工智慧的書")],
                "llm_config": {
                    "model": "openai:gpt-4o-mini",
                    "temperature": 0.5,
                },
            },
            config={
                "configurable": {
                    "thread_id": "thread-123",
                },
            },
            # stream_mode=["messages", "custom"],
            stream_mode=["messages"],
        ):
            pprint(event)

    asyncio.run(stream_tokens())
