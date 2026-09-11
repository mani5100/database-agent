# src/database_agent/api/routes/agent.py

from fastapi import APIRouter, HTTPException

from database_agent.connectors.base import SourceType
from database_agent.graph.builder import get_agent_graph
from database_agent.models.agent import AskRequest, AskResponse
from database_agent.services.query_context_builder import build_query_context
from database_agent.sessions.connection_registry import (
    connection_registry,
    SessionNotFoundError,
)
from database_agent.services.input_guardrail import check_question
from guardrails.errors import ValidationError
import logging
from database_agent.sessions.chat_store import chat_store

logger = logging.getLogger(__name__)

router = APIRouter()

_DIALECT_BY_SOURCE_TYPE = {
    SourceType.POSTGRES: "postgres",
    SourceType.MYSQL: "mysql",
    SourceType.CSV: "duckdb",
    SourceType.EXCEL: "duckdb",
}


@router.post("/session/{session_id}/ask", response_model=AskResponse)
async def ask_route(session_id: str, request: AskRequest) -> AskResponse:
    try:
        check_question(request.question)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        connector = await connection_registry.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    dialect = _DIALECT_BY_SOURCE_TYPE.get(connector.source_type)
    if dialect is None:
        raise HTTPException(
            status_code=400,
            detail=f"Querying is not supported for source type '{connector.source_type.value}'",
        )

    query_context = await build_query_context(session_id, request.question)
    if not query_context.tables:
        raise HTTPException(
            status_code=400,
            detail="No relevant schema found for this question, has the semantic layer been assembled and indexed?",
        )

    graph = get_agent_graph()

    initial_state = {
        "session_id": session_id,
        "question": request.question,
        "dialect": dialect,
        "query_context": query_context,
        "current_sql": None,
        "compiled_sql": None,
        "error": None,
        "retry_count": 0,
        "result_rows": None,
        "answer": None,
        "chart_candidates": None,
        "conversation_history": [],
    }

    final_state = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": request.chat_id}},
    )

    await chat_store.add_message(
        chat_id=request.chat_id,
        question=request.question,
        sql=final_state.get("current_sql"),
        answer=final_state["answer"],
        result_rows=final_state.get("result_rows"),
        chart_candidates=final_state.get("chart_candidates"),
    )

    return AskResponse(
        session_id=session_id,
        question=request.question,
        sql=final_state.get("current_sql"),
        answer=final_state["answer"],
        result_rows=final_state.get("result_rows"),
        chart_candidates=final_state.get("chart_candidates") or [],
    )