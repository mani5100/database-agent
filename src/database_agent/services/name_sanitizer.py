# src/database_agent/services/name_sanitizer.py

import re

# Words that would break as SQL identifiers or clash with a future metrics
# expression DSL. Kept intentionally small and specific rather than a huge
# generic SQL-reserved-word list, since over-blocking common business terms
# (e.g. "order", "group") would be more annoying than helpful here.
_RESERVED_WORDS = {
    "select", "from", "where", "join", "order", "group", "by",
    "having", "union", "insert", "update", "delete", "table",
    "and", "or", "not", "as", "on", "case", "when", "then", "else",
}


def sanitize_name(raw_name: str) -> str:
    """
    Normalizes an LLM-proposed business name into a safe snake_case
    identifier. Does NOT guarantee uniqueness, that's handled separately
    by ensure_unique_names(), since uniqueness depends on sibling names
    within the same scope (all models, or all columns within one model).
    """
    name = raw_name.strip().lower()
    name = re.sub(r"[^a-z0-9_]+", "_", name)   # anything not alnum/underscore -> _
    name = re.sub(r"_+", "_", name)              # collapse repeated underscores
    name = name.strip("_")

    if not name:
        name = "unnamed"

    if name[0].isdigit():
        name = f"_{name}"

    if name in _RESERVED_WORDS:
        name = f"{name}_field"

    return name


def ensure_unique_names(names: list[str]) -> list[str]:
    """
    Given a list of already-sanitized names (in order), returns a new list
    with duplicates resolved by appending _2, _3, etc. Order is preserved
    so callers can zip this back against their original items.
    """
    seen: dict[str, int] = {}
    result: list[str] = []

    for name in names:
        if name not in seen:
            seen[name] = 1
            result.append(name)
        else:
            seen[name] += 1
            result.append(f"{name}_{seen[name]}")

    return result


def sanitize_and_deduplicate(raw_names: list[str]) -> list[str]:
    """
    Convenience wrapper: sanitize every name, then resolve collisions.
    Use this for a full list of LLM-proposed names in one scope
    (e.g. all model names in Phase 1, or all column names within one
    table's Phase 2 result).
    """
    sanitized = [sanitize_name(n) for n in raw_names]
    return ensure_unique_names(sanitized)