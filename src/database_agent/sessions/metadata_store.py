# src/database_agent/sessions/metadata_store.py

import json
import time

import redis.asyncio as redis

from database_agent.connectors.base import SourceType
from database_agent.core.config import get_settings


class SessionMetadata:
    def __init__(self, source_type: SourceType, connection_params: dict, created_at: float):
        self.source_type = source_type
        self.connection_params = connection_params
        self.created_at = created_at

    def to_json(self) -> str:
        return json.dumps(
            {
                "source_type": self.source_type.value,
                "connection_params": self.connection_params,
                "created_at": self.created_at,
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> "SessionMetadata":
        data = json.loads(raw)
        return cls(
            source_type=SourceType(data["source_type"]),
            connection_params=data["connection_params"],
            created_at=data["created_at"],
        )


class MetadataStore:
    """
    Redis-backed session metadata store. Handles create/get/delete, with
    Redis's native key expiry (TTL) covering idle-session cleanup, no
    separate sweep job needed.

    NOTE: connection_params may include raw credentials (e.g. Postgres
    password) and are stored as plain JSON in Redis. Acceptable for local/
    research use, needs encryption before any non-local deployment.
    """

    def __init__(self):
        settings = get_settings()
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._ttl_seconds = settings.redis_session_ttl_seconds

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def save(
        self, session_id: str, source_type: SourceType, connection_params: dict
    ) -> None:
        metadata = SessionMetadata(
            source_type=source_type,
            connection_params=connection_params,
            created_at=time.time(),
        )
        await self._redis.set(
            self._key(session_id), metadata.to_json(), ex=self._ttl_seconds
        )

    async def get(self, session_id: str) -> SessionMetadata | None:
        raw = await self._redis.get(self._key(session_id))
        if raw is None:
            return None
        # Reading refreshes the TTL, an active session shouldn't expire mid-use.
        await self._redis.expire(self._key(session_id), self._ttl_seconds)
        return SessionMetadata.from_json(raw)

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))
        
        
    async def list_sessions(self) -> list[dict]:
        """
        Scans Redis for all active session metadata keys and returns their
        session_id, source_type, and created_at. Used by the frontend's
        connection-switcher UI.
        """
        sessions = []
        async for key in self._redis.scan_iter(match="session:*"):
            raw = await self._redis.get(key)
            if raw is None:
                continue
            metadata = SessionMetadata.from_json(raw)
            session_id = key.split(":", 1)[1]
            sessions.append(
                {
                    "session_id": session_id,
                    "source_type": metadata.source_type.value,
                    "created_at": metadata.created_at,
                }
            )
        return sessions


metadata_store = MetadataStore()