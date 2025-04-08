from fastapi.responses import RedirectResponse
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

from app.core.cors import setup_cors
from app.apis.sys import router as sys_router
from app.apis.agent import router as agent_router


def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(
        title="AI Librarian Backend",
        version="0.1.0",
    )
    setup_cors(app)
    app.include_router(sys_router, prefix="/v1")
    app.include_router(agent_router, prefix="/v1")

    @app.get("/", include_in_schema=False)
    async def root_redirect():  # noqa
        return RedirectResponse(url="/docs")

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
