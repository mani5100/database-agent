# src/database_agent/services/semantic_naming_service.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from database_agent.core.config import get_settings
from database_agent.models.semantic_layer import (
    ColumnDetail,
    TableDetailResponse,
    TableNamingResponse,
)
from database_agent.services.name_sanitizer import sanitize_and_deduplicate


class NamingValidationError(Exception):
    """Raised when the LLM's response doesn't match the input tables/columns exactly."""
    pass


def _get_llm() -> ChatOllama:
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )


# --- Phase 1: table naming ---

_TABLE_NAMING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are helping build a semantic layer for a database. For each "
            "table given, suggest a short, human-friendly business name.\n"
            "If the physical table name is already clear and commonly "
            "understood (e.g. 'customers', 'orders', 'products'), keep the "
            "business name the same or very close to it, do not rename it "
            "just to be different. Only propose a meaningfully different "
            "name when the physical name is genuinely unclear, abbreviated, "
            "or overly technical (e.g. 'cust_v2', 'ord_tbl').\n"
            "Return the exact physical_name unchanged alongside your suggestion.",
        ),
        ("human", "{tables_block}"),
    ]
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

    tables_block = "\n\n".join(
        f"Table: {physical_name}\nSample rows: {sample_rows}"
        for physical_name, sample_rows in tables_with_samples
    )

    chain = _TABLE_NAMING_PROMPT | _get_llm().with_structured_output(TableNamingResponse)
    response: TableNamingResponse = await chain.ainvoke({"tables_block": tables_block})

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


# --- Phase 2: per-table detail generation ---

_TABLE_DETAIL_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are helping build a semantic layer for a database. Given one "
            "table's columns and sample data, write a one-to-two sentence "
            "description of the table, a few synonyms for it, and for each "
            "column: a short business name, a one-sentence description, and "
            "a few synonyms.\n"
            "If a column's physical name is already clear and commonly "
            "understood, keep its business name the same or very close to "
            "it, do not rename it just to be different. Only propose a "
            "meaningfully different name when the physical name is "
            "genuinely unclear, abbreviated, or technical.\n"
            "Return the exact physical_name for each column unchanged.",
        ),
        ("human", "{table_block}"),
    ]
)


async def generate_table_details(
    physical_table_name: str,
    business_table_name: str,
    columns: list[tuple[str, str]],  # (physical_column_name, data_type)
    sample_rows: list[dict],
) -> TableDetailResponse:
    """
    Generates description, synonyms, and per-column details for one table.
    business_table_name is the FIXED name from Phase 1, passed in as a given,
    never regenerated here.
    """
    expected_columns = {name for name, _ in columns}

    column_lines = "\n".join(f"- {name} ({data_type})" for name, data_type in columns)
    table_block = (
        f"Table physical name: {physical_table_name}\n"
        f"Table business name (already decided, do not change): {business_table_name}\n\n"
        f"Columns:\n{column_lines}\n\n"
        f"Sample rows: {sample_rows}"
    )

    chain = _TABLE_DETAIL_PROMPT | _get_llm().with_structured_output(TableDetailResponse)
    response: TableDetailResponse = await chain.ainvoke({"table_block": table_block})

    returned_columns = {c.physical_name for c in response.columns}
    if returned_columns != expected_columns:
        missing = expected_columns - returned_columns
        unexpected = returned_columns - expected_columns
        raise NamingValidationError(
            f"LLM column response mismatch. Missing: {missing}, Unexpected: {unexpected}"
        )

    # Sanitize column business names, scoped to this table only.
    ordered_physical = [name for name, _ in columns]
    business_by_physical = {c.physical_name: c.business_name for c in response.columns}
    raw_names_in_order = [business_by_physical[name] for name in ordered_physical]
    sanitized_names = sanitize_and_deduplicate(raw_names_in_order)

    sanitized_columns = []
    for physical_name, sanitized_name in zip(ordered_physical, sanitized_names):
        original = next(c for c in response.columns if c.physical_name == physical_name)
        sanitized_columns.append(
            ColumnDetail(
                physical_name=physical_name,
                business_name=sanitized_name,
                description=original.description,
                synonyms=original.synonyms,
            )
        )

    return TableDetailResponse(
        description=response.description,
        synonyms=response.synonyms,
        columns=sanitized_columns,
    )