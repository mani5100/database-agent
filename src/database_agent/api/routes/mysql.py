# src/database_agent/api/routes/mysql.py

from fastapi import APIRouter, HTTPException

from database_agent.models.connection import ConnectionResponse, MySQLConnectionRequest
from database_agent.services.connection_service import create_mysql_session

router = APIRouter()


@router.post("/connect/mysql", response_model=ConnectionResponse)
async def connect_mysql(request: MySQLConnectionRequest) -> ConnectionResponse:
    try:
        return await create_mysql_session(
            host=request.host,
            port=request.port,
            user=request.user,
            password=request.password,
            database=request.database,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {exc}")