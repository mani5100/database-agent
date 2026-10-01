# src/database_agent/sessions/qdrant_client.py

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from database_agent.core.config import get_settings
from database_agent.services.embedding_service import embed_text


def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(url=settings.qdrant_url)


def get_collection_name() -> str:
    """
    Each embedding provider gets its own collection, since their vectors have
    different sizes and can't be compared with each other. Ollama keeps the
    original name so existing indexed data stays valid.
    """
    settings = get_settings()
    if settings.embedding_provider == "ollama":
        return settings.qdrant_collection_name
    return f"{settings.qdrant_collection_name}_{settings.embedding_provider}"


async def ensure_collection_exists() -> None:
    """
    Creates the semantic layer collection if it doesn't already exist.
    Safe to call repeatedly, checks existence first.
    """
    client = get_qdrant_client()
    collection_name = get_collection_name()

    exists = await client.collection_exists(collection_name)
    if not exists:
        # Size the collection from a real embedding, rather than hard-coding
        # a dimension per model that silently breaks when the model changes.
        dimension = len(await embed_text("dimension probe"))
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE,
            ),
        )
