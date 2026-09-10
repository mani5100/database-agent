# src/database_agent/graph/nodes/chart_decider.py
import logging

logger = logging.getLogger(__name__)

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from database_agent.core.config import get_settings
from database_agent.graph.prompts import CHART_DECIDER_PROMPT
from database_agent.graph.state import AgentState


class ChartCandidate(BaseModel):
    chart_id: str = Field(description="A short, stable identifier for this chart option, e.g. 'bar_customer_revenue'")
    chart_type: str = Field(description="'bar', 'line', or 'scatter'")
    x_column: str
    y_columns: list[str]
    label: str = Field(description="Short human-readable label for this chart option, shown in a checkbox list")
    is_default: bool = Field(description="True for exactly one candidate, the one shown by default")


class ChartDecisionResponse(BaseModel):
    candidates: list[ChartCandidate]


def _get_llm() -> ChatOllama:
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )


def _is_numeric(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


async def chart_decider_node(state: AgentState) -> dict:
    logger.info("chart_decider: START, incoming chart_candidates = %s", state.get("chart_candidates"))

    rows = state["result_rows"]

    if not rows or len(rows) == 1:
        logger.info("chart_decider: skipping, %d row(s)", len(rows) if rows else 0)
        return {"chart_candidates": []}

    columns = list(rows[0].keys())
    logger.info("chart_decider: %d rows, columns=%s", len(rows), columns)

    llm = _get_llm().with_structured_output(ChartDecisionResponse)
    chain = CHART_DECIDER_PROMPT | llm

    response: ChartDecisionResponse = await chain.ainvoke(
        {"columns": columns, "sample_rows": rows[:5]}
    )
    logger.info("chart_decider: LLM returned %d candidate(s): %s", len(response.candidates), response.candidates)

    result = {"chart_candidates": [c.model_dump() for c in response.candidates]}
    logger.info("chart_decider: RETURNING = %s", result)
    return result