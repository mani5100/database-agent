# src/database_agent/core/llm.py

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from database_agent.core.config import get_settings


def _get_ollama_llm(temperature: float) -> ChatOllama:
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=temperature,
        # Without a timeout a hung Ollama server would block forever and the
        # fallback would never get a chance to run.
        client_kwargs={"timeout": settings.llm_request_timeout_seconds},
    )


def _get_openai_llm(temperature: float) -> ChatOpenAI | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=temperature,
        timeout=settings.llm_request_timeout_seconds,
    )


def _get_ordered_llms(temperature: float) -> list[BaseChatModel]:
    """Chat models in the order they should be tried, per LLM_PROVIDER."""
    settings = get_settings()
    ollama = _get_ollama_llm(temperature)
    openai = _get_openai_llm(temperature)

    if settings.llm_provider == "openai":
        if openai is None:
            raise ValueError("LLM_PROVIDER=openai requires OPENAI_API_KEY to be set")
        return [openai, ollama]

    return [ollama] if openai is None else [ollama, openai]


def get_structured_llm(schema: type[BaseModel], temperature: float = 0) -> Runnable:
    """
    Returns a runnable producing `schema` instances. LLM_PROVIDER picks which
    model runs first; the other one is the fallback. Structured output is
    bound to each model before chaining the fallback, so a malformed response
    (not just a connection error) also falls through to the next model.
    If OPENAI_API_KEY is not set, Ollama is used on its own.
    """
    primary, *fallbacks = [llm.with_structured_output(schema) for llm in _get_ordered_llms(temperature)]
    if not fallbacks:
        return primary
    return primary.with_fallbacks(fallbacks)
