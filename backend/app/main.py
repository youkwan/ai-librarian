import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

from core.config import setup_cors


def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(
        title="AI Librarian Backend",
        version="0.1.0",
    )
    setup_cors(app)
    # app.include_router(routers, prefix="/v1")
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", reload=True)
