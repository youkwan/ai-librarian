from importlib import metadata

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from ai_librarian_apis.core.cors import setup_cors
from ai_librarian_apis.core.lifespan import lifespan
from ai_librarian_apis.core.settings import settings
from ai_librarian_apis.routes.system import system_router
from ai_librarian_apis.routes.tools import tools_router


def create_app() -> FastAPI:
    load_dotenv()
    __version__ = metadata.version("ai-librarian-apis")
    app = FastAPI(title="AI Librarian APIs", version=__version__, lifespan=lifespan)
    setup_cors(app)

    app.include_router(system_router, prefix="/v1")
    app.include_router(tools_router, prefix="/v1")
    # app.include_router(agents_router, prefix="/v1")

    @app.get("/", include_in_schema=False)
    async def redirect_root() -> RedirectResponse:
        return RedirectResponse(url="/redoc")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
