from pydantic import BaseModel, Field


class UsedTool(BaseModel):
    """Record of an external tool usage by the LLM during response generation.

    Captures both the tool name and its output result.
    """

    name: str = Field(
        ...,
        description="The identifier name of the external tool or API that was called during processing",
        examples=["get_temperature"],
    )
    output: str | int = Field(
        ...,
        description="The result or response returned by the external tool when it was called",
        examples=["The temperature in Tokyo is 20°C"],
    )
