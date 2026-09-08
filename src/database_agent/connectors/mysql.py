# src/src.database_agent/connectors/mysql.py

import aiomysql

from src.database_agent.connectors.base import (
    BaseConnector,
    ColumnInfo,
    RelationshipInfo,
    SchemaInfo,
    SourceType,
    TableInfo,
)

# Same normalized vocabulary as postgres.py: integer, float, text, boolean, date, datetime.
_MYSQL_TYPE_MAP = {
    "int": "integer",
    "bigint": "integer",
    "smallint": "integer",
    "tinyint": "integer",
    "decimal": "float",
    "float": "float",
    "double": "float",
    "varchar": "text",
    "char": "text",
    "text": "text",
    "longtext": "text",
    "boolean": "boolean",
    "tinyint(1)": "boolean",
    "date": "date",
    "datetime": "datetime",
    "timestamp": "datetime",
    "json": "text",
}


def _normalize_type(mysql_type: str) -> str:
    return _MYSQL_TYPE_MAP.get(mysql_type.lower(), "text")


class MySQLConnector(BaseConnector):
    source_type = SourceType.MYSQL

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        connection_timeout_seconds: int = 10,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection_timeout_seconds = connection_timeout_seconds
        self.pool: aiomysql.Pool | None = None

    async def connect(self) -> None:
        self.pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.database,
            minsize=1,
            maxsize=5,
            connect_timeout=self.connection_timeout_seconds,
            autocommit=True,
        )

    async def disconnect(self) -> None:
        if self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    async def is_alive(self) -> bool:
        if self.pool is None:
            return False
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
            return True
        except Exception:
            return False

    def get_reconnect_params(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "connection_timeout_seconds": self.connection_timeout_seconds,
        }

    async def extract_schema(self) -> SchemaInfo:
        assert self.pool is not None, "connect() must be called before extract_schema()"

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        c.TABLE_NAME AS table_name,
                        c.COLUMN_NAME AS column_name,
                        c.DATA_TYPE AS data_type,
                        c.IS_NULLABLE AS is_nullable,
                        c.COLUMN_KEY AS column_key
                    FROM information_schema.columns c
                    WHERE c.TABLE_SCHEMA = %s
                    ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;
                    """,
                    (self.database,),
                )
                columns_rows = await cur.fetchall()

                await cur.execute(
                    """
                    SELECT
                        TABLE_NAME AS from_table,
                        COLUMN_NAME AS from_column,
                        REFERENCED_TABLE_NAME AS to_table,
                        REFERENCED_COLUMN_NAME AS to_column
                    FROM information_schema.key_column_usage
                    WHERE TABLE_SCHEMA = %s
                        AND REFERENCED_TABLE_NAME IS NOT NULL;
                    """,
                    (self.database,),
                )
                fk_rows = await cur.fetchall()

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
                    is_primary_key=(row["column_key"] == "PRI"),
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