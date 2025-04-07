import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from typing import AsyncGenerator

from app.services.graph import create_react_agent
from app.models.schema import AegntRequest, AgentResponse

router = APIRouter(prefix="/agents", tags=["agents"])
react_agent = create_react_agent("react_agent")


@router.post("/invoke", response_model=AgentResponse)
async def ainvoke_react_agent(request: AegntRequest):
    try:
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
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request: {str(e)}",
            )
        except TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Processing request timeout",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LLM call failed: {str(e)}",
            )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Request validation failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}",
        )


def format_sse(event_name: str, data: dict) -> str:
    json_data = json.dumps(data)  # Convert dict to JSON string
    return f"event: {event_name}\ndata: {json_data}\n\n"


async def stream_tokens(request: AegntRequest) -> AsyncGenerator[str, None]:
    llm_tokens: list[str] = []
    base_data = {
        "thread_id": request.thread_id,
        "llm_config": request.llm_config.model_dump(),
    }

    try:

        def create_sse_event(event_type: str, additional_data: dict = None) -> str:
            event_data = {"type": event_type, **base_data}
            if additional_data:
                event_data.update(additional_data)
            return format_sse(event_type, event_data)

        is_beginning = True

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

            if event_type == "messages":
                ai_message_chunk = event[1][0]
                metadata = event[1][1]

                if is_beginning:
                    is_beginning = False
                    yield create_sse_event("stream.created")

                elif ai_message_chunk.response_metadata.get("finish_reason") == "stop":
                    full_llm_tokens = "".join(llm_tokens)

                    yield create_sse_event(
                        "stream.llm_tokens.done", {"llm_tokens": full_llm_tokens}
                    )
                    yield create_sse_event("stream.completed")

                elif ai_message_chunk.content:
                    llm_tokens.append(ai_message_chunk.content)

                    yield create_sse_event(
                        "stream.llm_tokens.delta",
                        {"llm_tokens": ai_message_chunk.content},
                    )

                if ai_message_chunk.tool_call_chunks:
                    tool_call = ai_message_chunk.tool_call_chunks[0]
                    tool_name = tool_call.get("name") if tool_call else None

                    if tool_name:
                        yield create_sse_event(
                            "stream.tool_call.created", {"tool_name": tool_name}
                        )

            elif event_type == "custom":  # tool call result inject from tool node
                event_data = event[1]

                yield create_sse_event(
                    "stream.tool_call.done",
                    {
                        "tool_name": event_data.get("name"),
                        "tool_output": event_data.get("output"),
                    },
                )
    except Exception as e:
        yield format_sse("error", {"error": str(e)})
        yield format_sse("end", {"status": "error"})


@router.post("/stream")
async def stream_chat(request: AegntRequest):
    return StreamingResponse(
        stream_tokens(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
