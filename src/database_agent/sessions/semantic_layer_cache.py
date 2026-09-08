# src/database_agent/sessions/semantic_layer_cache.py

import json

import redis.asyncio as redis

from database_agent.core.config import get_settings
from database_agent.models.semantic_layer import TableDetailResponse


class SemanticLayerCache:
    """
    Caches intermediate semantic-layer generation results (Phase 1 table
    names, Phase 2 per-table details) against a session_id. Separate from
    metadata_store since this holds generation state, not connection
    reconnect info, and may need a different TTL policy later.
    """

    def __init__(self):
        settings = get_settings()
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._ttl_seconds = settings.redis_session_ttl_seconds

    def _table_names_key(self, session_id: str) -> str:
        return f"semantic:table_names:{session_id}"

    def _table_detail_key(self, session_id: str, table_name: str) -> str:
        return f"semantic:table_detail:{session_id}:{table_name}"

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

    async def save_table_detail(
        self, session_id: str, table_name: str, detail: TableDetailResponse
    ) -> None:
        await self._redis.set(
            self._table_detail_key(session_id, table_name),
            detail.model_dump_json(),
            ex=self._ttl_seconds,
        )

    async def get_table_detail(
        self, session_id: str, table_name: str
    ) -> TableDetailResponse | None:
        raw = await self._redis.get(self._table_detail_key(session_id, table_name))
        if raw is None:
            return None
        return TableDetailResponse.model_validate_json(raw)

    async def get_all_table_details(
        self, session_id: str, table_names: list[str]
    ) -> dict[str, TableDetailResponse]:
        """
        Fetches every cached Phase 2 result for the given tables at once.
        Used by the YAML assembly step, which needs all selected tables'
        details together, not one at a time.
        """
        results: dict[str, TableDetailResponse] = {}
        for table_name in table_names:
            detail = await self.get_table_detail(session_id, table_name)
            if detail is not None:
                results[table_name] = detail
        return results


semantic_layer_cache = SemanticLayerCache()