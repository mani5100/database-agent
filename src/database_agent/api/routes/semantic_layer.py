# src/database_agent/api/routes/semantic_layer.py

from fastapi import APIRouter, HTTPException

from database_agent.models.semantic_layer import (
    AssembleYamlRequest,
    AssembleYamlResponse,
    TableDetailResponse,
    TableNamesResponse,
)
from database_agent.services.semantic_layer_assembly import assemble_semantic_layer_yaml
from database_agent.services.semantic_naming_service import (
    generate_table_details,
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


@router.post(
    "/session/{session_id}/generate_table_details/{table_name}",
    response_model=TableDetailResponse,
)
async def generate_table_details_route(session_id: str, table_name: str) -> TableDetailResponse:
    try:
        connector = await connection_registry.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    table_names = await semantic_layer_cache.get_table_names(session_id)
    if table_names is None or table_name not in table_names:
        raise HTTPException(
            status_code=400,
            detail="Table names not found for this session, run generate_table_names first",
        )
    business_table_name = table_names[table_name]

    schema_info = await connector.extract_schema()
    table_info = next((t for t in schema_info.tables if t.name == table_name), None)
    if table_info is None:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found in schema")

    columns = [(col.name, col.data_type) for col in table_info.columns]
    sample_rows = await connector.get_sample_rows(table_name, limit=2)

    try:
        result = await generate_table_details(
            physical_table_name=table_name,
            business_table_name=business_table_name,
            columns=columns,
            sample_rows=sample_rows,
        )
    except NamingValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM returned an inconsistent column response: {exc}",
        )

    await semantic_layer_cache.save_table_detail(session_id, table_name, result)

    return result


@router.post("/session/{session_id}/assemble_semantic_layer", response_model=AssembleYamlResponse)
async def assemble_semantic_layer_route(
    session_id: str, request: AssembleYamlRequest
) -> AssembleYamlResponse:
    try:
        connector = await connection_registry.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    schema_info = await connector.extract_schema()

    try:
        file_path = await assemble_semantic_layer_yaml(
            session_id=session_id,
            connector=connector,
            schema_info=schema_info,
            selected_table_names=request.selected_tables,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AssembleYamlResponse(session_id=session_id, file_path=file_path)