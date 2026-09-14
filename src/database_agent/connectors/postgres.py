# src/database_agent/connectors/postgres.py

import asyncpg

from database_agent.connectors.base import (
    BaseConnector,
    ColumnInfo,
    RelationshipInfo,
    SchemaInfo,
    SourceType,
    TableInfo,
)

# Normalized type vocabulary the rest of the app relies on.
# Postgres reports many variants (character varying, numeric(10,2), etc.),
# this collapses them into a small shared set.
_PG_TYPE_MAP = {
    "integer": "integer",
    "bigint": "integer",
    "smallint": "integer",
    "numeric": "float",
    "real": "float",
    "double precision": "float",
    "character varying": "text",
    "character": "text",
    "text": "text",
    "boolean": "boolean",
    "date": "date",
    "timestamp without time zone": "datetime",
    "timestamp with time zone": "datetime",
    "uuid": "text",
    "json": "text",
    "jsonb": "text",
}


def _normalize_type(pg_type: str) -> str:
    return _PG_TYPE_MAP.get(pg_type.lower(), "text")  # unknown types fall back to text


class PostgresConnector(BaseConnector):
    source_type = SourceType.POSTGRES

    def __init__(self, dsn: str, connection_timeout_seconds: int = 10, schema: str = "public"):
        self.dsn = dsn
        self.connection_timeout_seconds = connection_timeout_seconds
        self.schema = schema
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=1,
            max_size=5,
            timeout=self.connection_timeout_seconds,
        )

    async def disconnect(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    async def is_alive(self) -> bool:
        if self.pool is None:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    def get_reconnect_params(self) -> dict:
        return {
            "dsn": self.dsn,
            "connection_timeout_seconds": self.connection_timeout_seconds,
            "schema": self.schema,
        }

    async def extract_schema(self) -> SchemaInfo:
        assert self.pool is not None, "connect() must be called before extract_schema()"

        async with self.pool.acquire() as conn:
            columns_rows = await conn.fetch(
                """
                SELECT
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    COALESCE(pk.is_primary_key, false) AS is_primary_key
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        true AS is_primary_key
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema = $1
                ) pk
                    ON c.table_name = pk.table_name
                    AND c.column_name = pk.column_name
                WHERE c.table_schema = $1
                ORDER BY c.table_name, c.ordinal_position;
                """,
                self.schema,
            )

            fk_rows = await conn.fetch(
                """
                SELECT
                    tc.table_name AS from_table,
                    kcu.column_name AS from_column,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                    AND tc.table_schema = ccu.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = $1;
                """,
                self.schema,
            )

        tables: dict[str, TableInfo] = {}
        for row in columns_rows:
            table_name = row["table_name"]
            if table_name not in tables:
                tables[table_name] = TableInfo(name=table_name)
            tables[table_name].columns.append(
                ColumnInfo(
                    name=row["column_name"],
                    data_type=_normalize_type(row["data_type"]),
                    is_nullable=(row["is_nullable"] == "YES"),
                    is_primary_key=row["is_primary_key"],
                )
            )

        relationships = [
            RelationshipInfo(
                from_table=row["from_table"],
                from_column=row["from_column"],
                to_table=row["to_table"],
                to_column=row["to_column"],
            )
            for row in fk_rows
        ]

        return SchemaInfo(tables=list(tables.values()), relationships=relationships)
    
    async def get_sample_rows(self, table_name: str, limit: int = 2) -> list[dict]:
        assert self.pool is not None, "connect() must be called before get_sample_rows()"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f'SELECT * FROM "{self.schema}"."{table_name}" LIMIT $1',
                limit,
            )
        return [dict(row) for row in rows]
    
    async def execute_query(self, sql: str) -> list[dict]:
        assert self.pool is not None, "connect() must be called before execute_query()"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql)
        return [dict(row) for row in rows]