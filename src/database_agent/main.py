# src/src.database_agent/main.py

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from src.database_agent.api.router import router
from src.database_agent.core.config import get_settings
import logging
logging.basicConfig(level=logging.INFO)

settings = get_settings()

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