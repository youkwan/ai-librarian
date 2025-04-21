import asyncio
from typing import Literal, Dict, List
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langchain.chat_models import init_chat_model

from app.services.tools.tools import TOOLS
from app.models.states import MessagesState, MessagesStateInput


def reset_tools_used(state: MessagesState) -> Dict[str, List[AnyMessage]]:
    return {"tools_used": []}


async def call_llm(state: MessagesState) -> Dict[str, List[AnyMessage]]:
    llm_config = state.llm_config
    model_params = {
        "model": llm_config.model,
        "temperature": llm_config.temperature,
    }
    if llm_config.max_tokens is not None:
        model_params["max_tokens"] = llm_config.max_tokens

    llm = init_chat_model(**model_params)
    llm_with_tools = llm.bind_tools(TOOLS)

    messages = state.messages

    try:
        response = await llm_with_tools.ainvoke(messages)
    except Exception as e:
        raise e

    return {"messages": [response]}


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    messages = state.messages
    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    if last_message.tool_calls:
        return "tools"
    return "__end__"


def create_react_agent(name: str) -> StateGraph:
    workflow = StateGraph(state_schema=MessagesState, input=MessagesStateInput)
    workflow.add_node("reset_tools_used", reset_tools_used)
    workflow.add_node("agent", call_llm)
    tool_node = ToolNode(TOOLS)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("reset_tools_used")
    workflow.add_edge("reset_tools_used", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
    )
    workflow.add_edge("tools", "agent")
    checkpointer = MemorySaver()
    return workflow.compile(name=name, checkpointer=checkpointer)


react_agent = create_react_agent("react_agent")


if __name__ == "__main__":
    from rich.pretty import pprint
    from dotenv import load_dotenv

    load_dotenv()
    config = {
        "configurable": {
            "thread_id": "thread-123",
        },
    }

    async def stream_tokens():
        async for event in react_agent.astream(
            input={
                "messages": [HumanMessage("what is the temperature in taipei?")],
                "llm_config": {"model": "openai:gpt-4o-mini", "temperature": 0.5},
            },
            config=config,
            stream_mode=["messages", "custom"],
        ):
            pprint(event)

    asyncio.run(stream_tokens())
