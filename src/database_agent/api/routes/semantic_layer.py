# src/database_agent/api/routes/semantic_layer.py

from fastapi import APIRouter, HTTPException

from database_agent.models.semantic_layer import TableNamesResponse
from database_agent.services.semantic_naming_service import (
    generate_table_names,
    NamingValidationError,
)
from database_agent.sessions.connection_registry import (
    connection_registry,
    SessionNotFoundError,
)
from database_agent.sessions.semantic_layer_cache import semantic_layer_cache

router = APIRouter()


@router.post("/session/{session_id}/generate_table_names", response_model=TableNamesResponse)
async def generate_table_names_route(session_id: str) -> TableNamesResponse:
    try:
        connector = await connection_registry.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    schema_info = await connector.extract_schema()

    tables_with_samples = []
    for table in schema_info.tables:
        sample_rows = await connector.get_sample_rows(table.name, limit=2)
        tables_with_samples.append((table.name, sample_rows))

    try:
        table_names = await generate_table_names(tables_with_samples)
    except NamingValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM returned an inconsistent naming response: {exc}",
        )

    await semantic_layer_cache.save_table_names(session_id, table_names)

    return TableNamesResponse(session_id=session_id, table_names=table_names)