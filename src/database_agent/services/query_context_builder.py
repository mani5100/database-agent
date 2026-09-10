# src/database_agent/services/query_context_builder.py

from pathlib import Path

import yaml
from qdrant_client.models import FieldCondition, Filter, MatchValue

from database_agent.core.config import get_settings
from database_agent.models.query_context import ColumnMapping, QueryContext, TableMapping
from database_agent.services.embedding_service import embed_text
from database_agent.sessions.qdrant_client import get_qdrant_client

_YAML_DIR = Path("backend/configs")


async def _search_relevant_columns(session_id: str, question: str, top_k: int = 10) -> list[dict]:
    settings = get_settings()
    client = get_qdrant_client()
    query_vector = await embed_text(question)

    response = await client.query_points(
        collection_name=settings.qdrant_collection_name,
        query=query_vector,
        query_filter=Filter(
            must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
        ),
        limit=top_k,
    )
    return [point.payload for point in response.points]


async def _get_all_columns_for_table(session_id: str, table_business_name: str) -> list[dict]:
    """
    Fetches every indexed column payload for one table, not just the ones
    that ranked in the top_k search, since a query needs the table's full
    shape, not just the columns that happened to match the question text.
    """
    settings = get_settings()
    client = get_qdrant_client()

    results, _ = await client.scroll(
        collection_name=settings.qdrant_collection_name,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="session_id", match=MatchValue(value=session_id)),
                FieldCondition(key="table_business_name", match=MatchValue(value=table_business_name)),
            ]
        ),
        limit=100,  # generous ceiling, a single table won't realistically exceed this
    )
    return [point.payload for point in results]


def _load_relationships(session_id: str, relevant_table_names: set[str]) -> list[dict]:
    """
    Reads the assembled YAML file for this session and returns only the
    relationships where both sides are among the relevant tables.
    """
    yaml_path = _YAML_DIR / f"semantics_{session_id}.yaml"
    if not yaml_path.exists():
        return []

    with yaml_path.open("r", encoding="utf-8") as f:
        document = yaml.safe_load(f)

    all_relationships = document.get("relationships", [])
    return [
        rel
        for rel in all_relationships
        if rel["from_model"] in relevant_table_names and rel["to_model"] in relevant_table_names
    ]


async def build_query_context(session_id: str, question: str, top_k: int = 10) -> QueryContext:
    """
    Given a user's question, retrieves the relevant subset of the semantic
    layer: top_k matching columns, expanded to their full parent tables,
    plus relationships connecting those tables.
    """
    top_matches = await _search_relevant_columns(session_id, question, top_k)

    relevant_table_names = {match["table_business_name"] for match in top_matches}

    tables = []
    for table_business_name in relevant_table_names:
        all_columns = await _get_all_columns_for_table(session_id, table_business_name)
        if not all_columns:
            continue

        table_physical_name = all_columns[0]["table_physical_name"]
        columns = [
            ColumnMapping(
                business_name=col["column_business_name"],
                physical_name=col["column_physical_name"],
                data_type=col.get("column_physical_type", "text"),
            )
            for col in all_columns
        ]
        tables.append(
            TableMapping(
                business_name=table_business_name,
                physical_name=table_physical_name,
                columns=columns,
            )
        )

    relationships = _load_relationships(session_id, relevant_table_names)

    return QueryContext(tables=tables, relationships=relationships)