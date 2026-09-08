# src/src.database_agent/sessions/connection_registry.py

from src.database_agent.connectors.base import BaseConnector, SourceType
from src.database_agent.sessions.metadata_store import metadata_store


class ConnectionRegistry:
    """
    Holds live connector objects (pools, DuckDB instances) in this worker
    process's memory, keyed by session_id. Redis (via metadata_store) holds
    the serializable metadata needed to rebuild a connector if it's missing
    from this worker's memory, e.g. after a restart or on a different worker.
    """

    def __init__(self):
        self._live_connectors: dict[str, BaseConnector] = {}

    async def register(
        self, session_id: str, connector: BaseConnector, source_type: SourceType
    ) -> None:
        """
        Called right after a connector successfully connects.
        Stores the live object locally and the reconnect metadata in Redis.
        """
        self._live_connectors[session_id] = connector
        await metadata_store.save(
            session_id=session_id,
            source_type=source_type,
            connection_params=connector.get_reconnect_params(),
        )

    async def get(self, session_id: str) -> BaseConnector:
        """
        Returns a live connector for this session, recreating it if this
        worker doesn't have it in memory (get-or-recreate fallback).
        Raises SessionNotFoundError if the session doesn't exist in Redis
        either, meaning it truly expired or never existed.
        """
        connector = self._live_connectors.get(session_id)
        if connector is not None and await connector.is_alive():
            return connector

        # Not in this worker's memory, or the connection died. Rebuild from Redis metadata.
        metadata = await metadata_store.get(session_id)
        if metadata is None:
            raise SessionNotFoundError(session_id)

        connector = _rebuild_connector(metadata.source_type, metadata.connection_params)
        await connector.connect()
        self._live_connectors[session_id] = connector
        return connector

    async def close(self, session_id: str) -> None:
        """Explicit disconnect, e.g. user-triggered 'disconnect' action."""
        connector = self._live_connectors.pop(session_id, None)
        if connector is not None:
            await connector.disconnect()
        await metadata_store.delete(session_id)


class SessionNotFoundError(Exception):
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found or expired: {session_id}")


def _rebuild_connector(source_type: SourceType, connection_params: dict) -> BaseConnector:
    # Deferred import to avoid a circular import between this module and connectors/.
    from src.database_agent.connectors.postgres import PostgresConnector
    from src.database_agent.connectors.mysql import MySQLConnector
    from src.database_agent.connectors.duckdb_file import DuckDBFileConnector

    if source_type == SourceType.POSTGRES:
        return PostgresConnector(**connection_params)
    elif source_type == SourceType.MYSQL:
        return MySQLConnector(**connection_params)
    else:
        return DuckDBFileConnector(source_type=source_type, **connection_params)


connection_registry = ConnectionRegistry()