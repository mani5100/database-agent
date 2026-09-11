# src/database_agent/models/chat.py

from pydantic import BaseModel


class CreateChatRequest(BaseModel):
    title: str = "New chat"


class ChatSummary(BaseModel):
    chat_id: str
    title: str


class ChatListResponse(BaseModel):
    chats: list[ChatSummary]


class ChatMessage(BaseModel):
    question: str
    sql: str | None
    answer: str
    result_rows: list[dict] | None
    chart_candidates: list[dict] | None


class ChatHistoryResponse(BaseModel):
    chat_id: str
    messages: list[ChatMessage]