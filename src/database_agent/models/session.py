from pydantic import BaseModel


class SessionSummary(BaseModel):
    session_id: str
    source_type: str
    created_at: float


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]