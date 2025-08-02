from ai_librarian_apis.core.logger import logger
from ai_librarian_apis.deps import get_tools
from ai_librarian_apis.schemas.error import BaseError
from ai_librarian_apis.schemas.tools import ToolArg, ToolInfo, ToolListResponse, ToolRunRequest, ToolRunResponse
from fastapi import APIRouter, Depends, HTTPException
from langchain_core.tools import BaseTool

tools_router = APIRouter(prefix="/tools", tags=["tools"])


@tools_router.get("", responses={500: {"model": BaseError}})
def list_tools(tools: list[BaseTool] = Depends(get_tools)) -> ToolListResponse:
    """Provides a list of tools that the agent can potentially use during its
    execution to perform actions or retrieve information.
    """
    try:
        tools_info = []
        for tool in tools:
            args_list = []
            if tool.args_schema:
                json_schema = tool.args_schema.model_json_schema()
                properties = json_schema.get("properties", {})
                required_args = json_schema.get("required", [])

                for arg_name, arg_details in properties.items():
                    args_list.append(
                        ToolArg(
                            arg=arg_name,
                            type=arg_details.get("type", "string"),  # Default to 'string' if type is not specified
                            description=arg_details.get("description"),
                            required=arg_name in required_args,
                        )
                    )

            tools_info.append(
                ToolInfo(
                    name=tool.name,
                    description=tool.description,
                    args_schema=args_list,
                )
            )
        return ToolListResponse(tools=tools_info)
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(500, f"Error listing tools: {e}")


@tools_router.post(
    "/run",
    responses={
        404: {"model": BaseError, "description": "Tool not found."},
        500: {"model": BaseError},
    },
)
async def run_tool(request: ToolRunRequest, tools: list[BaseTool] = Depends(get_tools)):
    """Runs a tool with the given name and input."""
    try:
        selected_tool = next((tool for tool in tools if tool.name == request.tool_name), None)
        if not selected_tool:
            raise HTTPException(404, f"Tool {request.tool_name} not found")
        tool_input = request.args
        tool_input_dict = {arg.name: arg.value for arg in tool_input}
        return ToolRunResponse(
            tool_name=request.tool_name, args=request.args, output=selected_tool.run(tool_input_dict)
        )
    except Exception as e:
        logger.error(f"Error running tool: {e}")
        raise HTTPException(500, f"Error running tool: {e}")
