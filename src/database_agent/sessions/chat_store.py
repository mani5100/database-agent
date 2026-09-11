# src/database_agent/sessions/chat_store.py

import json
import uuid

import asyncpg
from fastapi.encoders import jsonable_encoder

from database_agent.core.config import get_settings


class ChatStore:
    """
    Postgres-backed storage for chats and their full message history
    (including result_rows and chart_candidates for frontend redisplay).
    Lives in the same checkpoint-postgres database as LangGraph's own
    checkpoints, since both represent durable agent-conversation state,
    not ephemeral session data (that stays in Redis).
    """

    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        settings = get_settings()
        self._pool = await asyncpg.create_pool(dsn=settings.checkpoint_db_uri)

    async def create_tables(self) -> None:
        assert self._pool is not None, "connect() must be called first"
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id UUID PRIMARY KEY,
                    session_id UUID NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    chat_id UUID NOT NULL REFERENCES chats(chat_id),
                    question TEXT NOT NULL,
                    sql TEXT,
                    answer TEXT NOT NULL,
                    result_rows JSONB,
                    chart_candidates JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

    async def create_chat(self, session_id: str, title: str) -> str:
        assert self._pool is not None
        chat_id = str(uuid.uuid4())
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO chats (chat_id, session_id, title) VALUES ($1, $2, $3)",
                chat_id, session_id, title,
            )
        return chat_id

    async def list_chats(self, session_id: str) -> list[dict]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT chat_id, title, created_at FROM chats WHERE session_id = $1 ORDER BY created_at ASC",
                session_id,
            )
        return [dict(row) for row in rows]

    async def add_message(
        self,
        chat_id: str,
        question: str,
        sql: str | None,
        answer: str,
        result_rows: list[dict] | None,
        chart_candidates: list[dict] | None,
    ) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO chat_messages (chat_id, question, sql, answer, result_rows, chart_candidates)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                chat_id, question, sql, answer,
                json.dumps(jsonable_encoder(result_rows)) if result_rows is not None else None,
                json.dumps(jsonable_encoder(chart_candidates)) if chart_candidates is not None else None,
            )

    async def get_history(self, chat_id: str) -> list[dict]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT question, sql, answer, result_rows, chart_candidates, created_at "
                "FROM chat_messages WHERE chat_id = $1 ORDER BY created_at ASC",
                chat_id,
            )
        return [
            {
                "question": r["question"],
                "sql": r["sql"],
                "answer": r["answer"],
                "result_rows": json.loads(r["result_rows"]) if r["result_rows"] else None,
                "chart_candidates": json.loads(r["chart_candidates"]) if r["chart_candidates"] else None,
            }
            for r in rows
        ]


chat_store = ChatStore()