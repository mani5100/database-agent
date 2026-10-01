# src/database_agent/services/embedding_service.py

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from database_agent.core.config import get_settings


def _get_embeddings_client() -> Embeddings:
    settings = get_settings()
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("EMBEDDING_PROVIDER=openai requires OPENAI_API_KEY to be set")
        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
    return OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )


async def embed_text(text: str) -> list[float]:
    """Embeds a single piece of text, returns its vector."""
    client = _get_embeddings_client()
    return await client.aembed_query(text)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeds multiple texts in one call, more efficient than looping embed_text."""
    client = _get_embeddings_client()
    return await client.aembed_documents(texts)
