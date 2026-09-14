# src/database_agent/services/relationship_editor.py

from pathlib import Path

import yaml

from database_agent.connectors.base import SourceType

_YAML_DIR = Path("backend/configs")

_EDITABLE_SOURCE_TYPES = {SourceType.POSTGRES, SourceType.MYSQL}


class RelationshipEditError(Exception):
    pass


def _yaml_path(session_id: str) -> Path:
    return _YAML_DIR / f"semantics_{session_id}.yaml"


def _load_document(session_id: str) -> dict:
    path = _yaml_path(session_id)
    if not path.exists():
        raise RelationshipEditError("Semantic layer not found for this session")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_document(session_id: str, document: dict) -> None:
    path = _yaml_path(session_id)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(document, f, sort_keys=False, allow_unicode=True)


def assert_editable_source(source_type: SourceType) -> None:
    if source_type not in _EDITABLE_SOURCE_TYPES:
        raise RelationshipEditError(
            "Relationship editing is only available for PostgreSQL and MySQL connections"
        )


def get_relationships(session_id: str) -> list[dict]:
    document = _load_document(session_id)
    return document.get("relationships", [])


def _find_model(document: dict, business_name: str) -> dict:
    for model in document.get("models", []):
        if model["name"] == business_name:
            return model
    raise RelationshipEditError(f"Table '{business_name}' not found in the semantic layer")


def _resolve_physical_column(model: dict, column_name: str) -> str:
    """
    column_name is the BUSINESS name, as given by the frontend (the UI
    never shows physical names to the user). Relationships are stored
    using PHYSICAL column names throughout this project, matching how
    auto-extracted foreign keys are stored in semantic_layer_assembly.py
    and how erd.py expects to read them back. This translates the given
    business name to its physical name before anything gets saved.
    """
    for col in model["columns"]:
        if col["name"] == column_name:
            return col["physical_name"]
    raise RelationshipEditError(
        f"Column '{column_name}' not found on table '{model['name']}'"
    )


def add_relationship(
    session_id: str,
    from_model: str,
    from_column: str,
    to_model: str,
    to_column: str,
    rel_type: str,
    description: str | None,
) -> dict:
    document = _load_document(session_id)

    from_table = _find_model(document, from_model)
    to_table = _find_model(document, to_model)
    from_physical_column = _resolve_physical_column(from_table, from_column)
    to_physical_column = _resolve_physical_column(to_table, to_column)

    base_name = f"{from_model}_{from_column}_to_{to_model}_{to_column}"
    existing_names = {r["name"] for r in document.get("relationships", [])}
    name = base_name
    suffix = 2
    while name in existing_names:
        name = f"{base_name}_{suffix}"
        suffix += 1

    new_relationship = {
        "name": name,
        "from_model": from_model,
        "from_column": from_physical_column,
        "to_model": to_model,
        "to_column": to_physical_column,
        "type": rel_type,
        "description": description or f"Each {from_model} relates to {to_model}",
    }

    document.setdefault("relationships", []).append(new_relationship)
    _save_document(session_id, document)
    return new_relationship


def delete_relationship(session_id: str, relationship_name: str) -> None:
    document = _load_document(session_id)
    relationships = document.get("relationships", [])
    updated = [r for r in relationships if r["name"] != relationship_name]

    if len(updated) == len(relationships):
        raise RelationshipEditError(f"Relationship '{relationship_name}' not found")

    document["relationships"] = updated
    _save_document(session_id, document)


def update_relationship(
    session_id: str,
    relationship_name: str,
    from_model: str,
    from_column: str,
    to_model: str,
    to_column: str,
    rel_type: str,
    description: str | None,
) -> dict:
    document = _load_document(session_id)
    relationships = document.get("relationships", [])

    existing = next((r for r in relationships if r["name"] == relationship_name), None)
    if existing is None:
        raise RelationshipEditError(f"Relationship '{relationship_name}' not found")

    from_table = _find_model(document, from_model)
    to_table = _find_model(document, to_model)
    from_physical_column = _resolve_physical_column(from_table, from_column)
    to_physical_column = _resolve_physical_column(to_table, to_column)

    base_name = f"{from_model}_{from_column}_to_{to_model}_{to_column}"
    other_names = {r["name"] for r in relationships if r["name"] != relationship_name}
    name = base_name
    suffix = 2
    while name in other_names:
        name = f"{base_name}_{suffix}"
        suffix += 1

    updated_relationship = {
        "name": name,
        "from_model": from_model,
        "from_column": from_physical_column,
        "to_model": to_model,
        "to_column": to_physical_column,
        "type": rel_type,
        "description": description or f"Each {from_model} relates to {to_model}",
    }

    document["relationships"] = [
        updated_relationship if r["name"] == relationship_name else r
        for r in relationships
    ]
    _save_document(session_id, document)
    return updated_relationship