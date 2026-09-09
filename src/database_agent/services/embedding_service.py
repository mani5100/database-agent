# src/database_agent/services/embedding_service.py

from langchain_ollama import OllamaEmbeddings

from database_agent.core.config import get_settings


def _get_embeddings_client() -> OllamaEmbeddings:
    settings = get_settings()
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