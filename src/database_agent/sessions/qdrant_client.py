# src/database_agent/sessions/qdrant_client.py

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from database_agent.core.config import get_settings

_NOMIC_EMBED_DIMENSION = 768  # nomic-embed-text's output vector size


def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(url=settings.qdrant_url)


async def ensure_collection_exists() -> None:
    """
    Creates the semantic layer collection if it doesn't already exist.
    Safe to call repeatedly, checks existence first.
    """
    settings = get_settings()
    client = get_qdrant_client()

    exists = await client.collection_exists(settings.qdrant_collection_name)
    if not exists:
        await client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(
                size=_NOMIC_EMBED_DIMENSION,
                distance=Distance.COSINE,
            ),
        )