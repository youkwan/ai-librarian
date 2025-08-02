from fastapi import Request
from langchain_core.tools import BaseTool

from ai_librarian_apis.core.global_vars import tools


def get_tools(request: Request) -> list[BaseTool]:
    return tools
    # return request.app.state.tools
