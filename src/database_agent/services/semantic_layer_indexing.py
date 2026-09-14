# src/database_agent/services/semantic_layer_indexing.py

import uuid

from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
)

from database_agent.core.config import get_settings
from database_agent.services.embedding_service import embed_texts
from database_agent.sessions.qdrant_client import ensure_collection_exists, get_qdrant_client


def _build_embedded_text(model: dict, column: dict) -> str:
    table_synonyms = ", ".join(model.get("synonyms", []))
    column_synonyms = ", ".join(column.get("synonyms", []))
    return (
        f"Table: {model['name']}. {table_synonyms}. {model['description']}\n"
        f"Column: {column['name']}. {column_synonyms}. {column['description']}"
    )


async def index_semantic_layer(session_id: str, models: list[dict]) -> int:
    """
    Indexes every column across the given models into Qdrant, scoped to
    session_id. Deletes any existing points for this session_id first,
    so re-running assembly for the same session produces a clean re-index
    rather than accumulating stale/duplicate points.

    Returns the number of points indexed.
    """
    settings = get_settings()
    await ensure_collection_exists()
    client = get_qdrant_client()

    # Clean slate for this session before inserting fresh points.
    await client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=Filter(
            must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
        ),
    )

    embedded_texts = []
    payloads = []
    for model in models:
        for column in model["columns"]:
            embedded_texts.append(_build_embedded_text(model, column))
            payloads.append(
                {
                    "session_id": session_id,
                    "table_business_name": model["name"],
                    "table_physical_name": model["physical_name"],
                    "column_business_name": column["name"],
                    "column_physical_name": column["physical_name"],
                    "column_physical_type": column["physical_type"],
                    "column_description": column["description"],
                    "column_synonyms": column["synonyms"],
                    "table_description": model["description"],
                }
            )

    if not embedded_texts:
        return 0

    vectors = await embed_texts(embedded_texts)

    points = [
        PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload)
        for vector, payload in zip(vectors, payloads)
    ]

    await client.upsert(collection_name=settings.qdrant_collection_name, points=points)

    return len(points)

async def delete_session_from_index(session_id: str) -> None:
    """
    Removes every indexed column point for this session_id from Qdrant.
    Called when a session is explicitly closed, so no orphaned vectors
    remain searchable (or just taking up storage) after the session
    that owns them no longer exists.
    """
    settings = get_settings()
    client = get_qdrant_client()
    await client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=Filter(
            must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
        ),
    )