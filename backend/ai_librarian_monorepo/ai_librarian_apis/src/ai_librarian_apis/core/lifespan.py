from contextlib import asynccontextmanager

from ai_librarian_apis.core.logger import setup_logging
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield
