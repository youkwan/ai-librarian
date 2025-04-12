from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from typing import AsyncGenerator

from app.services.graph import create_react_agent
from app.services.tools import TOOLS_INFO
from app.models.schemas import AegntRequest, AgentResponse, ModelResponse, ToolResponse
from app.models.llmconfig import Model
from app.utils import format_sse

agents_router = APIRouter(prefix="/agents", tags=["agents"])
react_agent = create_react_agent("react_agent")


@agents_router.get(
    "/models", summary="list all available models", response_model=ModelResponse
)
def get_models() -> ModelResponse:
    """
    Lists the currently available models
    """
    # TODO: check if the model is available
    return ModelResponse(models=Model.list())


@agents_router.get(
    "/tools", summary="list all available tools", response_model=ToolResponse
)
def get_tools() -> ToolResponse:
    """
    Get the list of available tools.
    """
    return ToolResponse(tools=TOOLS_INFO)


@agents_router.post("/invoke", summary="invoke the agent", response_model=AgentResponse)
async def ainvoke_react_agent(request: AegntRequest) -> AgentResponse:
    try:
        response = await react_agent.ainvoke(
            input={
                "messages": request.get_langchain_messages(),
                "llm_config": request.llm_config,
                "max_steps": request.max_steps,
            },
            config=request.get_runnable_config(),
        )

        parsed_response = {
            "thread_id": request.thread_id,
            "llm_config": request.llm_config,
            "messages": [
                {
                    "role": "assistant",
                    "content": response["messages"][-1].content,
                }
            ],
            "tools_used": response["tools_used"],
        }
        return AgentResponse(**parsed_response)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        )


async def stream_tokens(request: AegntRequest) -> AsyncGenerator[str, None]:
    try:
        is_stream_started = False
        in_llm_phase = False
        llm_tokens: list[str] = []
        base_data = {
            "thread_id": request.thread_id,
            "llm_config": request.llm_config.model_dump(),
        }

        def create_sse_event(event_type: str, additional_data: dict = None) -> str:
            event_data = {"type": event_type, **base_data}
            if additional_data:
                event_data.update(additional_data)
            return format_sse(event_type, event_data)

        async for event in react_agent.astream(
            input={
                "messages": request.get_langchain_messages(),
                "llm_config": request.llm_config,
                "max_steps": request.max_steps,
            },
            config=request.get_runnable_config(),
            stream_mode=["messages", "custom"],
        ):

            event_type = event[0]

            if not is_stream_started:
                is_stream_started = True
                yield create_sse_event("stream.start")

            if event_type == "messages":
                ai_message_chunk = event[1][0]

                if ai_message_chunk.response_metadata.get("finish_reason") == "stop":
                    all_llm_tokens = "".join(llm_tokens)
                    yield create_sse_event(
                        "stream.llm_tokens.complete",
                        {"llm_tokens": all_llm_tokens},
                    )
                    in_llm_phase = False

                elif ai_message_chunk.content:
                    if not in_llm_phase:
                        in_llm_phase = True
                        llm_tokens = []
                        yield create_sse_event("stream.llm_tokens.start")

                    llm_tokens.append(ai_message_chunk.content)
                    yield create_sse_event(
                        "stream.llm_tokens.delta",
                        {"llm_tokens": ai_message_chunk.content},
                    )

            elif (
                event_type == "custom"
            ):  # This are the tool call result injected from tool nodes
                if in_llm_phase:
                    in_llm_phase = False

                event_data = event[1]
                tool_type = event_data.get("type")
                tool_name = event_data.get("tool_name")
                metadata = event_data.get("metadata")
                tool_tokens = event_data.get("tool_tokens")

                if tool_type == "start":
                    yield create_sse_event("stream.tool_call.start", event_data)
                elif tool_type == "delta":
                    yield create_sse_event("stream.tool_call.delta", event_data)
                elif tool_type == "complete":
                    yield create_sse_event("stream.tool_call.complete", event_data)

        if is_stream_started:
            yield create_sse_event("stream.completed")

    except Exception as e:
        yield format_sse("stream.error", {"error": str(e)})


@agents_router.post("/stream", summary="stream the agent")
async def stream_react_agent(request: AegntRequest):
    return StreamingResponse(
        stream_tokens(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
