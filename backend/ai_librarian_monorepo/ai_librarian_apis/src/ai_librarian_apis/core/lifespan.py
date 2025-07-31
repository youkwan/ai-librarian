from contextlib import asynccontextmanager

from ai_librarian_apis.core.settings import Settings
from fastapi import FastAPI
from rich import print


@asynccontextmanager
async def lifespan(the_app):
    settings = Settings()
    try:
        yield
    finally:
        print("shutdown things")


app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=5000, log_level="info", timeout_graceful_shutdown=3)
