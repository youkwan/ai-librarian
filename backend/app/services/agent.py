from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
import os
import sys

from app.models.state import ChatState


def create_chat_workflow(config=None):
    config = config or {}
    workflow = StateGraph(ChatState)

    async def call_llm(state: ChatState):
        llm = state.init_model()
        response = await llm.ainvoke(state.messages)
        return {"messages": response}

    workflow.add_node("llm", call_llm)
    workflow.set_entry_point("llm")
    memory = config.get("memory", MemorySaver())
    return workflow.compile(checkpointer=memory)


if __name__ == "__main__":
    workflow = create_chat_workflow()
    print(workflow.invoke({"messages": [HumanMessage(content="你好")]}))
