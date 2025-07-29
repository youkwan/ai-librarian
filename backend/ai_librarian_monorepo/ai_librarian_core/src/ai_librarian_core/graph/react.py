from collections.abc import Awaitable, Callable
from typing import Literal

from ai_librarian_core.graph.states import MessagesState, MessagesStateInput
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode


def init_llm_node(tools: list[BaseTool]) -> Callable[[MessagesState], Awaitable[dict[str, list[BaseMessage]]]]:
    """Initializes an LLM node for a LangGraph, binding it with specified tools.

    This function acts as a factory, creating a callable asynchronous function (`call_llm`)
    that can be used as a node within a LangGraph. The `call_llm` function takes a
    `MessagesState` as input, initializes a chat model based on the LLM configuration
    from the state, and binds the provided tools to the LLM before invoking it
    with the current messages.

    This "closure" pattern provides `tools` to `call_llm` without altering its fixed
    signature required by LangGraph nodes, enabling dependency injection.

    Args:
        tools (list[BaseTool]): A list of BaseTool objects that the language model
            will be able to use for tool calling.

    Returns:
        Callable[[MessagesState], Awaitable[dict[str, list[BaseMessage]]]]:
            An asynchronous callable function (`call_llm`) suitable for a LangGraph node.
            It takes a `MessagesState` and returns a dictionary containing a list of
            `BaseMessage` objects, representing the LLM's response.
    """

    async def call_llm(state: MessagesState) -> dict[str, list[BaseMessage]]:
        llm_config = state.llm_config

        # https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html#langchain.chat_models.base.init_chat_model
        llm = init_chat_model(
            model=llm_config.model,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
        )
        llm_with_tools = llm.bind_tools(tools)

        messages = state.messages

        try:
            response = await llm_with_tools.ainvoke(messages)
        except ValueError as e:
            raise e
        except ImportError as e:
            raise e
        except Exception as e:
            raise e

        return {"messages": [response]}

    return call_llm


async def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    messages = state.messages
    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(f"Expected AIMessage in output edges, but got {type(last_message).__name__}")
    if last_message.tool_calls:
        return "tools"
    return "__end__"


def init_react_graph(
    name: str,
    tools: list[BaseTool],
    checkpointer: BaseCheckpointSaver,
) -> CompiledStateGraph:
    graph = StateGraph(state_schema=MessagesState, input_schema=MessagesStateInput)
    call_llm = init_llm_node(tools)
    graph.add_node(call_llm)
    tool_node = ToolNode(tools)
    graph.add_node(tool_node)
    graph.set_entry_point("call_llm")
    graph.add_conditional_edges(
        "call_llm",
        should_continue,
    )
    graph.add_edge("tools", "call_llm")
    return graph.compile(name=name, checkpointer=checkpointer)
