# src/database_agent/api/routes/postgres.py

from fastapi import APIRouter, HTTPException

from database_agent.models.connection import ConnectionResponse, PostgresConnectionRequest
from database_agent.services.connection_service import create_postgres_session

router = APIRouter()


@router.post("/connect/postgres", response_model=ConnectionResponse)
async def connect_postgres(request: PostgresConnectionRequest) -> ConnectionResponse:
    try:
        return await create_postgres_session(
            host=request.host,
            port=request.port,
            user=request.user,
            password=request.password,
            database=request.database,
            schema_name=request.schema_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {exc}")