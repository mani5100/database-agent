# src/src.database_agent/main.py

from fastapi import FastAPI

from src.database_agent.api.router import router
from src.database_agent.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.environment}