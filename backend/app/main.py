import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from importlib import metadata
from fastapi.responses import RedirectResponse

from app.core.cors import setup_cors
from app.apis.sys import sys_router
from app.apis.agents import agents_router
from app.core.config import settings


def create_app() -> FastAPI:
    load_dotenv()
    __version__ = metadata.version("app")
    app = FastAPI(
        title="AI Librarian Backend",
        version=__version__,
    )
    setup_cors(app)
    app.include_router(sys_router, prefix="/v1")
    app.include_router(agents_router, prefix="/v1")

    @app.get("/", include_in_schema=False)
    async def redirect_root():
        return RedirectResponse(url="/redoc")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app", host=settings.host, port=settings.port, reload=settings.debug
    )
