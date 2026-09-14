# src/database_agent/services/session_cleanup.py

from database_agent.services.semantic_layer_indexing import delete_session_from_index
from database_agent.sessions.chat_store import chat_store
from database_agent.sessions.connection_registry import connection_registry


async def close_session_fully(session_id: str) -> None:
    """
    Closes a session and cleans up every store that holds data scoped to
    it: the live connector + Redis metadata (via connection_registry),
    the Qdrant index, and this session's chats/messages in Postgres.
    """
    await connection_registry.close(session_id)
    await delete_session_from_index(session_id)
    await chat_store.delete_chats_for_session(session_id)