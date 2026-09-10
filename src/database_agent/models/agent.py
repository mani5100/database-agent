# src/database_agent/models/agent.py

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str


class ChartCandidateResponse(BaseModel):
    chart_id: str
    chart_type: str
    x_column: str
    y_columns: list[str]
    label: str
    is_default: bool


class AskResponse(BaseModel):
    session_id: str
    question: str
    sql: str | None
    answer: str
    result_rows: list[dict] | None
    chart_candidates: list[ChartCandidateResponse]
    
