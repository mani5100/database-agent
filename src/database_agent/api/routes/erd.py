from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from database_agent.models.erd import ErdColumn, ErdRelationship, ErdResponse, ErdTable

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
            columns=[
                ErdColumn(
                    name=col["name"],
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