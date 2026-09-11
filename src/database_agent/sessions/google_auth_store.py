# src/database_agent/sessions/google_auth_store.py

import json
import uuid

import redis.asyncio as redis

from database_agent.core.config import get_settings


class GoogleAuthStore:
    """
    Stores Google OAuth tokens (access + refresh) keyed by a google_session_id,
    separate from database connection sessions, since a Google login is
    reusable across multiple sheet selections.
    """

    def __init__(self):
        settings = get_settings()
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._ttl_seconds = 60 * 60 * 24 * 7  # 7 days, refresh token lasts much longer

    def _key(self, google_session_id: str) -> str:
        return f"google_auth:{google_session_id}"

    async def save_tokens(self, access_token: str, refresh_token: str, expiry: str) -> str:
        google_session_id = str(uuid.uuid4())
        await self._redis.set(
            self._key(google_session_id),
            json.dumps({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expiry": expiry,
            }),
            ex=self._ttl_seconds,
        )
        return google_session_id

    async def get_tokens(self, google_session_id: str) -> dict | None:
        raw = await self._redis.get(self._key(google_session_id))
        if raw is None:
            return None
        return json.loads(raw)

    async def update_access_token(self, google_session_id: str, access_token: str, expiry: str) -> None:
        tokens = await self.get_tokens(google_session_id)
        if tokens is None:
            return
        tokens["access_token"] = access_token
        tokens["expiry"] = expiry
        await self._redis.set(
            self._key(google_session_id), json.dumps(tokens), ex=self._ttl_seconds
        )


google_auth_store = GoogleAuthStore()