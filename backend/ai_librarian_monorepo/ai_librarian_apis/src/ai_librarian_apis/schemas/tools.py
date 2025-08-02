from typing import Any

from pydantic import BaseModel, Field


class ToolArg(BaseModel):
    """The arguments schema of the tool."""

    arg: str = Field(description="The name of the argument.")
    type: str = Field(description="The type of the argument.")
    description: str | None = Field(description="The description of the argument.")
    required: bool = Field(description="Whether the arguments are required.")
    description: str | None = Field(description="The description of the arguments.")


class ToolInfo(BaseModel):
    """eturns the name and description of the tool."""

    name: str = Field(description="The name of the tool.")
    description: str = Field(description="The description of the tool.")
    args_schema: list[ToolArg] = Field(description="The JSON schema of the arguments for the tool.")


class ToolListResponse(BaseModel):
    """Returns the list of available tools info with their names and descriptions."""

    tools: list[ToolInfo] = Field(description="The list of available tools info with their names and descriptions.")


class ToolRunArg(BaseModel):
    """The argument of the tool."""

    name: str = Field(description="The name of the argument.")
    value: Any = Field(description="The value of the argument.")


class ToolRunRequest(BaseModel):
    """The input of the tool."""

    tool_name: str = Field(description="The name of the tool.", examples=["google_search"])
    args: list[ToolRunArg] = Field(
        description="The arguments of the tool.", examples=[[ToolRunArg(name="query", value="Python")]]
    )


class ToolRunResponse(BaseModel):
    """Returns the result of running a tool.
    The result is a dictionary with the following keys:
    - "output": The output of the tool.
    - "tool_name": The name of the tool.
    - "args": The arguments of the tool.
    """

    tool_name: str = Field(description="The name of the tool.")
    args: list[ToolRunArg] = Field(description="The arguments of the tool.")
    output: str = Field(description="The output of the tool.")
