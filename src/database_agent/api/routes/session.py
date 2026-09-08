# src/database_agent/api/routes/session.py

from fastapi import APIRouter, HTTPException

from database_agent.models.connection import ConnectionResponse
from database_agent.services.connection_service import _schema_info_to_response
from database_agent.sessions.connection_registry import (
    connection_registry,
    SessionNotFoundError,
)

router = APIRouter()


@router.get("/session/{session_id}/schema", response_model=ConnectionResponse)
async def get_session_schema(session_id: str) -> ConnectionResponse:
    try:
        connector = await connection_registry.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    schema_info = await connector.extract_schema()
    return _schema_info_to_response(session_id, connector.source_type, schema_info)


@router.delete("/session/{session_id}")
async def close_session(session_id: str) -> dict:
    await connection_registry.close(session_id)
    return {"status": "closed", "session_id": session_id}