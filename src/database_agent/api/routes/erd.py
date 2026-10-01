# src/database_agent/api/routes/erd.py

from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from database_agent.models.entity_edit import EntityEditRequest, EntityEditResponse
from database_agent.models.erd import ErdColumn, ErdRelationship, ErdResponse, ErdTable
from database_agent.services.entity_editor import EntityEditError, update_entity
from database_agent.services.semantic_layer_indexing import index_semantic_layer

router = APIRouter()

_YAML_DIR = Path("backend/configs")


@router.get("/session/{session_id}/erd", response_model=ErdResponse)
async def get_erd(session_id: str) -> ErdResponse:
    yaml_path = _YAML_DIR / f"semantics_{session_id}.yaml"
    if not yaml_path.exists():
        raise HTTPException(status_code=404, detail="Semantic layer not found for this session")

    with yaml_path.open("r", encoding="utf-8") as f:
        document = yaml.safe_load(f)

    models = document.get("models", [])

    tables = [
        ErdTable(
            name=model["name"],
            physical_name=model["physical_name"],
            description=model.get("description", ""),
            columns=[
                ErdColumn(
                    name=col["name"],
                    physical_name=col["physical_name"],
                    description=col.get("description", ""),
                    is_primary_key=col.get("is_primary_key", False),
                    physical_type=col.get("physical_type", "text"),
                )
                for col in model["columns"]
            ],
        )
        for model in models
    ]

    # Relationships store physical column names (from DB-introspected foreign
    # keys), but ErdColumn.name above is the LLM-generated business name, so
    # look up each side's business name before handing this to the frontend.
    business_name_by_physical = {
        model["name"]: {col["physical_name"]: col["name"] for col in model["columns"]}
        for model in models
    }

    relationships = [
        ErdRelationship(
            from_table=rel["from_model"],
            from_column=business_name_by_physical[rel["from_model"]][rel["from_column"]],
            to_table=rel["to_model"],
            to_column=business_name_by_physical[rel["to_model"]][rel["to_column"]],
            type=rel["type"],
        )
        for rel in document.get("relationships", [])
    ]

    return ErdResponse(tables=tables, relationships=relationships)


@router.put("/session/{session_id}/entities/{physical_table_name}", response_model=EntityEditResponse)
async def edit_entity(
    session_id: str, physical_table_name: str, request: EntityEditRequest
) -> EntityEditResponse:
    try:
        result = update_entity(
            session_id=session_id,
            physical_table_name=physical_table_name,
            new_name=request.name,
            new_description=request.description,
            column_edits=[col.model_dump() for col in request.columns],
        )
    except EntityEditError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await index_semantic_layer(session_id, result["models"])

    return EntityEditResponse(
        physical_name=result["physical_name"],
        name=result["name"],
        description=result["description"],
        columns=result["columns"],
        relationships_updated=result["relationships_updated"],
    )