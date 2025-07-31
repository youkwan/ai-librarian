from collections.abc import AsyncGenerator

from agent_core.graphs import in_memory_react_graph as react_graph
from agent_core.models.llmconfig import Model
from agent_core.tools.tools import TOOLS_INFO
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from schemas import (
    AegntRequest,
    AgentResponse,
    ModelResponse,
    ToolResponse,
)
from utils import format_sse

agents_router = APIRouter(prefix="/agents", tags=["agents"])


@agents_router.get("/models", summary="list all available models")
def get_models() -> ModelResponse:
    """Retrieves a list of the LLMs currently configured
    and available for use with the agent endpoints (`/invoke` and `/stream`).
    """
    return ModelResponse(models=list(Model))


@agents_router.get("/tools", summary="list all available tools")
def get_tools() -> ToolResponse:
    """Provides a list of tools that the agent can potentially use during its
    execution to perform actions or retrieve information.
    """
    return ToolResponse(tools=TOOLS_INFO)


@agents_router.post("/invoke", summary="invoke the agent")
async def ainvoke_react_agent(request: AegntRequest) -> AgentResponse:
    """Processes the request by invoking the agent synchronously and returns the final
    response once the agent execution is complete. This endpoint is suitable for
    applications where real-time feedback is not required, and only the final result is needed.

    **Conversation Management:**
    - **Continuing a Conversation:** To continue an existing conversation, provide the *same* `thread_id` in your request. You only need to include the *new* user message(s) in the `messages` array. The backend automatically retrieves and appends to the existing conversation history associated with that `thread_id`.
    - **Starting a New Conversation:** To start a new conversation, either:
        - Provide a *new, unique* `thread_id`.
        - Omit the `thread_id` field entirely. The backend will generate a new unique `thread_id` for the conversation.
    """
    try:
        response = await react_graph.ainvoke(
            input={
                "messages": request.get_langchain_messages(),
                "llm_config": request.llm_config.model_dump(),
            },
            config=request.get_runnable_config(),
        )

        return AgentResponse(
            {
                "thread_id": request.thread_id,
                "llm_config": request.llm_config,
                "messages": [
                    {
                        "role": "assistant",
                        "content": response["messages"][-1].content,
                    }
                ],
                "used_tools": response["used_tools"],
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        )


async def stream_tokens(request: AegntRequest) -> AsyncGenerator[str]:
    try:
        is_stream_started = False
        in_llm_phase = False
        llm_tokens = []

        def create_sse_event(event_type: str, additional_data: dict | None = None) -> str:
            base_data = {
                "type": event_type,
                "thread_id": request.thread_id,
                "llm_config": request.llm_config.model_dump(),
            }
            if additional_data:
                return format_sse(event_type, base_data | additional_data)
            else:
                return format_sse(event_type, base_data)

        async for event in react_graph.astream(
            input={
                "messages": request.get_langchain_messages(),
                "llm_config": request.llm_config.model_dump(),
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
                        "stream.llm_tokens.completed",
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
            elif event_type == "custom":
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
                elif tool_type == "completed":
                    yield create_sse_event("stream.tool_call.completed", event_data)

        if is_stream_started:
            yield create_sse_event("stream.completed")

    except Exception as e:
        yield format_sse("stream.error", {"error": str(e)})


@agents_router.post("/stream", summary="stream the agent")
async def stream_react_agent(request: AegntRequest):
    """Initiates a streaming connection to the agent based on the provided request parameters.
    This endpoint uses Server-Sent Events (SSE) to push updates from the agent's execution
    process in real-time. It's suitable for applications requiring immediate feedback or
    observing the agent's thought process, including LLM token generation and tool call results.

    **Conversation Management:**
    - **Continuing a Conversation:** To continue an existing conversation, provide the *same* `thread_id` in your request. You only need to include the *new* user message(s) in the `messages` array. The backend automatically retrieves and appends to the existing conversation history associated with that `thread_id`.
    - **Starting a New Conversation:** To start a new conversation, either:
        - Provide a *new, unique* `thread_id`.
        - Omit the `thread_id` field entirely. The backend will generate a new unique `thread_id` for the conversation.

    **Streaming Format:**
    The server pushes events formatted according to the SSE standard (`text/event-stream`).
    Each event has an `event` field indicating the type and a `data` field containing a JSON payload.
    Possible event types include:
    - `stream.start`: Indicates the stream has successfully started.
    - `stream.llm_tokens.start`: Signals the beginning of LLM token generation.
    - `stream.llm_tokens.delta`: Contains a chunk of newly generated LLM tokens.
    - `stream.llm_tokens.completed`: Signals the end of LLM token generation for a step, providing the full sequence.
    - `stream.tool_call.start`: Indicates a tool call is about to start. Contains tool name and input.
    - `stream.tool_call.delta`: Provides intermediate output or progress from a tool call (if the tool supports it).
    - `stream.tool_call.completed`: Signals the completion of a tool call. May contain the final output.
    - `stream.completed`: Indicates the entire agent execution process has finished successfully.
    - `stream.error`: Sent if an error occurs during the streaming process. Contains error details.

    **Important Usage Note:**
    Standard OpenAPI documentation interfaces like Swagger UI typically **cannot** directly interact
    with or test SSE endpoints. To consume this stream, you must use a client library or tool
    that supports Server-Sent Events (e.g., `EventSource` in JavaScript, `httpx` in Python, Postman).
    """
    return StreamingResponse(
        stream_tokens(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
