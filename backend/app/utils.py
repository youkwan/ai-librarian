import json
import uuid


def generate_thread_id(prefix: str = "thread") -> str:
    return f"{prefix}-{uuid.uuid4()}"


def format_sse(event_name: str, data: dict) -> str:
    json_data = json.dumps(data)
    return f"event: {event_name}\ndata: {json_data}\n\n"
