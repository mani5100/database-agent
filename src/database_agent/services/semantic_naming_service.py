# src/database_agent/services/semantic_naming_service.py

from langchain_ollama import ChatOllama

from database_agent.core.config import get_settings
from database_agent.models.semantic_layer import TableNamingResponse
from database_agent.services.name_sanitizer import sanitize_and_deduplicate


class NamingValidationError(Exception):
    """Raised when the LLM's response doesn't match the input tables exactly."""
    pass


def _get_llm() -> ChatOllama:
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )


async def generate_table_names(
    tables_with_samples: list[tuple[str, list[dict]]]
) -> dict[str, str]:
    """
    tables_with_samples: list of (physical_table_name, sample_rows) pairs.
    Returns: dict mapping physical_table_name -> sanitized, unique business_name.
    Raises NamingValidationError if the LLM's response doesn't cover exactly
    the same set of physical table names that were sent in.
    """
    expected_names = {name for name, _ in tables_with_samples}

    prompt_sections = []
    for physical_name, sample_rows in tables_with_samples:
        prompt_sections.append(
            f"Table: {physical_name}\nSample rows: {sample_rows}"
        )
    prompt = (
        "For each table below, suggest a short, human-friendly business name.\n"
        "If the physical table name is already clear and commonly understood "
        ", keep the business name the "
        "same or very close to it, do not rename it just to be different. "
        "Only propose a meaningfully different name when the physical name is "
        "genuinely unclear, abbreviated, or overly technical (e.g. 'cust_v2', 'ord_tbl').\n"
        "Return the exact physical_name unchanged alongside your suggestion.\n\n"
        + "\n\n".join(prompt_sections)
    )

    structured_llm = _get_llm().with_structured_output(TableNamingResponse)
    response: TableNamingResponse = await structured_llm.ainvoke(prompt)

    returned_names = {t.physical_name for t in response.tables}
    if returned_names != expected_names:
        missing = expected_names - returned_names
        unexpected = returned_names - expected_names
        raise NamingValidationError(
            f"LLM response physical_name mismatch. Missing: {missing}, Unexpected: {unexpected}"
        )

    # Preserve input order rather than trusting the LLM's output order,
    # since with_structured_output doesn't guarantee ordering is retained.
    business_name_by_physical = {t.physical_name: t.business_name for t in response.tables}
    ordered_physical_names = [name for name, _ in tables_with_samples]
    raw_business_names = [business_name_by_physical[name] for name in ordered_physical_names]

    sanitized_names = sanitize_and_deduplicate(raw_business_names)

    return dict(zip(ordered_physical_names, sanitized_names))