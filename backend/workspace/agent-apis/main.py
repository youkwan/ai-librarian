from importlib import metadata

import uvicorn
from core.config import settings
from core.cors import setup_cors
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from routes.agents import agents_router
from routes.sys import sys_router


def create_app() -> FastAPI:
    load_dotenv()
    __version__ = metadata.version("agent-apis")
    app = FastAPI(
        title="AI Librarian Backend",
        version=__version__,
    )
    setup_cors(app)
    app.include_router(sys_router, prefix="/v1")
    app.include_router(agents_router, prefix="/v1")

    @app.get("/", include_in_schema=False)
    async def redirect_root() -> RedirectResponse:  # type: ignore
        return RedirectResponse(url="/redoc")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
