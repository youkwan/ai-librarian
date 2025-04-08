from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings


def setup_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
