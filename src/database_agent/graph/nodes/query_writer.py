# src/database_agent/graph/nodes/query_writer.py

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from database_agent.core.config import get_settings
from database_agent.graph.prompts import QUERY_RETRY_PROMPT, QUERY_WRITER_PROMPT
from database_agent.graph.state import AgentState
from database_agent.models.query_context import QueryContext


class SQLWriteResponse(BaseModel):
    sql: str = Field(description="The SQL query, written using business names, fully qualified columns, no table aliases")


def _get_llm() -> ChatOllama:
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )

def _format_history(history: list[dict]) -> str:
    if not history:
        return "No previous questions in this session."
    lines = []
    for turn in history[-5:]:  # last 5 turns, keeps prompt size bounded
        lines.append(f"Q: {turn['question']}\nA: {turn['answer']}")
    return "\n\n".join(lines)


def _format_context(context: QueryContext) -> str:
    lines = []
    for table in context.tables:
        lines.append(f"Table: {table.business_name}")
        for col in table.columns:
            lines.append(f"  - {col.business_name} ({col.data_type})")
    if context.relationships:
        lines.append("\nRelationships:")
        for rel in context.relationships:
            lines.append(
                f"  - {rel['from_model']}.{rel['from_column']} -> "
                f"{rel['to_model']}.{rel['to_column']}"
            )
    return "\n".join(lines)


async def query_writer_node(state: AgentState) -> dict:
    schema_context = _format_context(state["query_context"])
    llm = _get_llm().with_structured_output(SQLWriteResponse)

    conversation_history = _format_history(state.get("conversation_history", []))

    if state.get("error") and state.get("current_sql"):
        chain = QUERY_RETRY_PROMPT | llm
        response: SQLWriteResponse = await chain.ainvoke(
            {
                "schema_context": schema_context,
                "question": state["question"],
                "previous_sql": state["current_sql"],
                "error": state["error"],
                "conversation_history": conversation_history,
            }
        )
    else:
        chain = QUERY_WRITER_PROMPT | llm
        response: SQLWriteResponse = await chain.ainvoke(
            {
                "schema_context": schema_context,
                "question": state["question"],
                "conversation_history": conversation_history,
            }
        )

    return {
        "current_sql": response.sql,
        "retry_count": state.get("retry_count", 0) + (1 if state.get("error") else 0),
    }