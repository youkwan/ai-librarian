import uuid


def generate_thread_id(prefix: str = "thread") -> str:
    return f"{prefix}-{uuid.uuid4()}"
