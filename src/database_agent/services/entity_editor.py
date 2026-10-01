# src/database_agent/services/entity_editor.py

from pathlib import Path

import yaml

_YAML_DIR = Path("backend/configs")


class EntityEditError(Exception):
    pass


def _yaml_path(session_id: str) -> Path:
    return _YAML_DIR / f"semantics_{session_id}.yaml"


def _load_document(session_id: str) -> dict:
    path = _yaml_path(session_id)
    if not path.exists():
        raise EntityEditError("Semantic layer not found for this session")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_document(session_id: str, document: dict) -> None:
    path = _yaml_path(session_id)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(document, f, sort_keys=False, allow_unicode=True)


def _find_model_by_physical_name(document: dict, physical_table_name: str) -> dict:
    for model in document.get("models", []):
        if model["physical_name"] == physical_table_name:
            return model
    raise EntityEditError(f"Table '{physical_table_name}' not found in the semantic layer")


def _assert_name_not_taken(document: dict, new_name: str, physical_table_name: str) -> None:
    for model in document.get("models", []):
        if model["physical_name"] != physical_table_name and model["name"] == new_name:
            raise EntityEditError(
                f"Business name '{new_name}' is already used by another table"
            )


def update_entity(
    session_id: str,
    physical_table_name: str,
    new_name: str,
    new_description: str,
    column_edits: list[dict],
) -> dict:
    """
    Renames/redescribes a table and its columns in place.

    column_edits: list of {"physical_name": ..., "name": ..., "description": ...}

    Table business names are referenced elsewhere in the YAML (relationships
    store from_model/to_model as business names, and query_writer/sql_compiler/
    query_context_builder all match joins on those same business names). So a
    table rename is cascaded into every relationship that points at this table,
    keeping the rest of the pipeline consistent. Column business names are NOT
    referenced that way (relationships store columns by physical_name), so
    column renames need no cascading.
    """
    document = _load_document(session_id)

    model = _find_model_by_physical_name(document, physical_table_name)
    _assert_name_not_taken(document, new_name, physical_table_name)

    columns_by_physical = {col["physical_name"]: col for col in model["columns"]}
    for edit in column_edits:
        column = columns_by_physical.get(edit["physical_name"])
        if column is None:
            raise EntityEditError(
                f"Column '{edit['physical_name']}' not found on table '{physical_table_name}'"
            )
        column["name"] = edit["name"]
        column["description"] = edit["description"]

    old_name = model["name"]
    model["name"] = new_name
    model["description"] = new_description

    relationships_updated = 0
    if old_name != new_name:
        for rel in document.get("relationships", []):
            changed = False
            if rel["from_model"] == old_name:
                rel["from_model"] = new_name
                changed = True
            if rel["to_model"] == old_name:
                rel["to_model"] = new_name
                changed = True
            if changed:
                relationships_updated += 1

    _save_document(session_id, document)

    return {
        "physical_name": model["physical_name"],
        "name": model["name"],
        "description": model["description"],
        "columns": [
            {
                "physical_name": col["physical_name"],
                "name": col["name"],
                "description": col["description"],
            }
            for col in model["columns"]
        ],
        "relationships_updated": relationships_updated,
        "models": document.get("models", []),  # handed to the route for re-indexing
    }