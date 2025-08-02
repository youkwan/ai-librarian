from contextlib import asynccontextmanager

from ai_librarian_apis.core.logger import setup_logging

# from ai_librarian_apis.core.openapi import get_injected_openapi_schema
# from ai_librarian_core.tools.tools import get_built_in_tools
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # app.state.tools = get_built_in_tools()
    # app.openapi_schema = get_injected_openapi_schema(app)
    yield
