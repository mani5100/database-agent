# src/database_agent/graph/nodes/compiler.py

from database_agent.graph.state import AgentState
from database_agent.services.sql_compiler import (
    NonSelectStatementError,
    TableAliasError,
    UndeclaredCrossTableAccessError,
    UnknownIdentifierError,
    UnqualifiedColumnError,
    compile_to_physical_sql,
)


async def compiler_node(state: AgentState) -> dict:
    try:
        compiled_sql = compile_to_physical_sql(
            business_sql=state["current_sql"],
            context=state["query_context"],
            dialect=state["dialect"],
        )
        return {"compiled_sql": compiled_sql, "error": None}

    except (
        NonSelectStatementError,
        TableAliasError,
        UnqualifiedColumnError,
        UnknownIdentifierError,
        UndeclaredCrossTableAccessError,
    ) as exc:
        return {"compiled_sql": None, "error": f"SQL compilation failed: {exc}"}


def compiler_routing(state: AgentState) -> str:
    if state.get("compiled_sql"):
        return "executor"
    if state.get("retry_count", 0) >= 3:
        return "give_up"
    return "query_writer"