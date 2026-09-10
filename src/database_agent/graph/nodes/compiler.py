# src/database_agent/graph/nodes/compiler.py

from database_agent.graph.state import AgentState
from database_agent.services.sql_compiler import (
    NonSelectStatementError,
    TableAliasError,
    UnknownIdentifierError,
    UnqualifiedColumnError,
    compile_to_physical_sql,
)


async def compiler_node(state: AgentState) -> dict:
    """
    Attempts to compile the LLM's business-name SQL into physical SQL.
    On success: clears any prior error, sets compiled_sql.
    On failure: sets error, leaves compiled_sql as None, so the
    conditional edge routes back to query_writer for a retry.
    """
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
    ) as exc:
        return {"compiled_sql": None, "error": f"SQL compilation failed: {exc}"}


def compiler_routing(state: AgentState) -> str:
    """
    Conditional edge function: decides where to go after compiler_node runs.
    - If compiled_sql is present, compilation succeeded, proceed to executor.
    - If error is present instead, and retries remain, loop back to query_writer.
    - If retries are exhausted, route to a give_up terminal node.
    """
    if state.get("compiled_sql"):
        return "executor"

    if state.get("retry_count", 0) >= 3:
        return "give_up"

    return "query_writer"