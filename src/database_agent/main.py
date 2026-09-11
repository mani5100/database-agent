# src/src.database_agent/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database_agent.core.config import get_settings

settings = get_settings()

os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing).lower()
os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project

from src.database_agent.api.router import router
import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.environment}