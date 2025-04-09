import asyncio
from typing import Literal, Dict, List
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AnyMessage, AIMessage, SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from app.services.tools import TOOLS
from app.models.states import MessagesState, MessagesStateInput
from app.services.prompts import DEFAULT_SYSTEM_PROMPT


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
    if not any(isinstance(message, SystemMessage) for message in messages):
        messages = [SystemMessage(DEFAULT_SYSTEM_PROMPT)] + messages

    try:
        response = await llm_with_tools.ainvoke(messages)
    except Exception as e:
        raise e
    return {"messages": [response], "current_step": state.current_step + 1}


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    messages = state.messages
    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    if state.current_step >= state.max_steps:
        return "__end__"
    if last_message.tool_calls:
        state.tools_used.append(last_message.tool_calls)
        return "tools"
    return "__end__"


def create_react_agent(name: str) -> StateGraph:
    workflow = StateGraph(state_schema=MessagesState, input=MessagesStateInput)
    workflow.add_node("agent", call_llm)
    tool_node = ToolNode(TOOLS)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
    )
    workflow.add_edge("tools", "agent")
    checkpointer = MemorySaver()
    return workflow.compile(name=name, checkpointer=checkpointer)


if __name__ == "__main__":
    load_dotenv()
    react_agent = create_react_agent("react_agent")
    config = {
        "configurable": {
            "thread_id": "345",
        },
    }

    print(
        asyncio.run(
            react_agent.ainvoke(
                {"messages": [HumanMessage("請問1240+1240是多少")]},
                config,
            )
        )
    )
