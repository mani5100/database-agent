# src/database_agent/sessions/semantic_layer_cache.py

import json

import redis.asyncio as redis

from database_agent.core.config import get_settings


class SemanticLayerCache:
    """
    Caches intermediate semantic-layer generation results (Phase 1 table
    names, later Phase 2 per-table results) against a session_id. Separate
    from metadata_store since this holds generation state, not connection
    reconnect info, and may need a different TTL policy later.
    """

    def __init__(self):
        settings = get_settings()
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._ttl_seconds = settings.redis_session_ttl_seconds

    def _table_names_key(self, session_id: str) -> str:
        return f"semantic:table_names:{session_id}"

    async def save_table_names(self, session_id: str, table_names: dict[str, str]) -> None:
        await self._redis.set(
            self._table_names_key(session_id),
            json.dumps(table_names),
            ex=self._ttl_seconds,
        )

    async def get_table_names(self, session_id: str) -> dict[str, str] | None:
        raw = await self._redis.get(self._table_names_key(session_id))
        if raw is None:
            return None
        return json.loads(raw)


semantic_layer_cache = SemanticLayerCache()