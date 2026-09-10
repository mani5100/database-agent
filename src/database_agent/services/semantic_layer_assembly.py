# src/database_agent/services/semantic_layer_assembly.py

from pathlib import Path

import yaml

from database_agent.connectors.base import BaseConnector, SchemaInfo
from database_agent.sessions.semantic_layer_cache import semantic_layer_cache

_OUTPUT_DIR = Path("backend/configs")
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _relationship_description(from_model: str, to_model: str) -> str:
    # Deterministic, no LLM needed, matches the style of your original skeleton.
    return f"Each {from_model} belongs to one {to_model}"


async def assemble_semantic_layer_yaml(
    session_id: str,
    connector: BaseConnector,
    schema_info: SchemaInfo,
    selected_table_names: list[str],
) -> str:
    """
    Combines Phase 1 table names, Phase 2 per-table details, and the
    schema's already-extracted relationships (filtered to only the
    selected tables) into one semantic layer YAML document, writes it
    to disk, and returns the file path.
    """
    table_names = await semantic_layer_cache.get_table_names(session_id)
    if table_names is None:
        raise ValueError("No table names found for this session, run generate_table_names first")

    table_details = await semantic_layer_cache.get_all_table_details(
        session_id, selected_table_names
    )
    missing = set(selected_table_names) - set(table_details.keys())
    if missing:
        raise ValueError(
            f"Missing generated details for tables: {missing}. "
            "Run generate_table_details for each selected table first."
        )

    schema_tables_by_name = {t.name: t for t in schema_info.tables}

    models = []
    for physical_table_name in selected_table_names:
        business_name = table_names[physical_table_name]
        detail = table_details[physical_table_name]
        table_info = schema_tables_by_name.get(physical_table_name)
        if table_info is None:
            raise ValueError(f"Table '{physical_table_name}' not found in current schema")

        column_type_by_name = {c.name: c.data_type for c in table_info.columns}

        columns = [
            {
                "name": col.business_name,
                "physical_name": col.physical_name,
                "physical_type": column_type_by_name.get(col.physical_name, "text"),
                "is_primary_key": next(
                    (c.is_primary_key for c in table_info.columns if c.name == col.physical_name),
                    False,
                ),
                "description": col.description,
                "synonyms": col.synonyms,
            }
            for col in detail.columns
        ]

        models.append(
            {
                "name": business_name,
                "source": connector.source_type.value,
                "physical_name": physical_table_name,
                "description": detail.description,
                "synonyms": detail.synonyms,
                "columns": columns,
            }
        )

    # Relationships: only keep ones where BOTH sides were selected.
    selected_set = set(selected_table_names)
    relationships = []
    for rel in schema_info.relationships:
        if rel.from_table in selected_set and rel.to_table in selected_set:
            from_business = table_names[rel.from_table]
            to_business = table_names[rel.to_table]
            relationships.append(
                {
                    "name": f"{from_business}_to_{to_business}",
                    "from_model": from_business,
                    "from_column": rel.from_column,
                    "to_model": to_business,
                    "to_column": rel.to_column,
                    "type": "many_to_one",  # FK direction always implies this for our extraction
                    "description": _relationship_description(from_business, to_business),
                }
            )

    document = {
        "version": 1,
        "models": models,
        "relationships": relationships,
        # metrics intentionally omitted, per earlier scoping decision
    }

    output_path = _OUTPUT_DIR / f"semantics_{session_id}.yaml"
    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(document, f, sort_keys=False, allow_unicode=True)

    return str(output_path), models