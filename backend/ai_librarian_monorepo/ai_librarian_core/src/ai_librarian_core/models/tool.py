from __future__ import annotations

from pydantic import BaseModel, Field


class Tool(BaseModel):
    """Tool schema. Returns the name and description of a tool."""

    tool_name: str = Field(..., description="The name of the tool.", examples=["get_temperature"])
    tool_description: str = Field(
        ...,
        description="The description of the tool.",
        examples=["Get the temperature in a given location"],
    )
