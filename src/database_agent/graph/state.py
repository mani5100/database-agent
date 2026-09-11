# src/database_agent/graph/state.py

from typing import TypedDict,Annotated
import operator

from database_agent.models.query_context import QueryContext


class AgentState(TypedDict):
    session_id: str
    question: str
    dialect: str

    query_context: QueryContext

    current_sql: str | None
    compiled_sql: str | None
    error: str | None
    retry_count: int

    result_rows: list[dict] | None
    answer: str | None
    chart_candidates: list[dict] | None
    
    conversation_history: Annotated[list[dict], operator.add]