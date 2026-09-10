# src/database_agent/graph/nodes/give_up.py

from database_agent.graph.state import AgentState


async def give_up_node(state: AgentState) -> dict:
    """
    Terminal node reached when the retry limit is exhausted, either from
    repeated compilation failures or repeated execution failures. Ensures
    the graph always ends with a clear answer, never silently stopping.
    """
    return {
        "answer": (
            "I wasn't able to generate a working query for this question "
            f"after multiple attempts. Last error: {state.get('error', 'unknown error')}"
        ),
        "result_rows": None,
        "chart_candidates": [],
    }