from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import SETTINGS


def setup_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=SETTINGS.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
