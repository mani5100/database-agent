# src/database_agent/graph/nodes/executor.py

from database_agent.graph.state import AgentState
from database_agent.sessions.connection_registry import connection_registry


async def executor_node(state: AgentState) -> dict:
    """
    Executes the compiled physical SQL against the session's actual
    connector. On success: stores result_rows, clears error.
    On failure (a real DB error, e.g. bad syntax for that dialect,
    a runtime constraint violation): sets error, leaves result_rows None,
    routes back to query_writer for a retry.
    """
    connector = await connection_registry.get(state["session_id"])

    try:
        rows = await connector.execute_query(state["compiled_sql"])
        return {"result_rows": rows, "error": None}

    except Exception as exc:
        return {
            "result_rows": None,
            "error": f"Query execution failed: {exc}",
        }


def executor_routing(state: AgentState) -> str:
    """
    - If result_rows is present, execution succeeded, proceed to interpreter.
    - If error is present instead, and retries remain, loop back to query_writer.
    - If retries exhausted, route to give_up.
    """
    if state.get("result_rows") is not None:
        return "interpreter"

    if state.get("retry_count", 0) >= 3:
        return "give_up"

    return "query_writer"