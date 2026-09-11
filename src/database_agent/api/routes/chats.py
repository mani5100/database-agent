# src/database_agent/api/routes/chats.py

from fastapi import APIRouter

from database_agent.models.chat import (
    ChatHistoryResponse,
    ChatListResponse,
    ChatSummary,
    CreateChatRequest,
)
from database_agent.sessions.chat_store import chat_store

router = APIRouter()


@router.post("/session/{session_id}/chats")
async def create_chat(session_id: str, request: CreateChatRequest) -> ChatSummary:
    chat_id = await chat_store.create_chat(session_id, request.title)
    return ChatSummary(chat_id=chat_id, title=request.title)


@router.get("/session/{session_id}/chats", response_model=ChatListResponse)
async def list_chats(session_id: str) -> ChatListResponse:
    chats = await chat_store.list_chats(session_id)
    return ChatListResponse(
        chats=[ChatSummary(chat_id=str(c["chat_id"]), title=c["title"]) for c in chats]
    )


@router.get("/chats/{chat_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(chat_id: str) -> ChatHistoryResponse:
    messages = await chat_store.get_history(chat_id)
    return ChatHistoryResponse(chat_id=chat_id, messages=messages)