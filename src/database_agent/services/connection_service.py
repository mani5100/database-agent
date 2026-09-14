# src/database_agent/services/connection_service.py

import uuid

from database_agent.connectors.base import SchemaInfo, SourceType
from database_agent.connectors.postgres import PostgresConnector
from database_agent.connectors.mysql import MySQLConnector
from database_agent.connectors.duckdb_file import DuckDBFileConnector
from database_agent.models.connection import (
    ColumnResponse,
    ConnectionResponse,
    RelationshipResponse,
    TableResponse,
)
from database_agent.sessions.connection_registry import connection_registry


def _schema_info_to_response(
    session_id: str, source_type: SourceType, schema_info: SchemaInfo
) -> ConnectionResponse:
    return ConnectionResponse(
        session_id=session_id,
        source_type=source_type.value,
        tables=[
            TableResponse(
                name=table.name,
                columns=[
                    ColumnResponse(
                        name=col.name,
                        data_type=col.data_type,
                        is_nullable=col.is_nullable,
                        is_primary_key=col.is_primary_key,
                    )
                    for col in table.columns
                ],
            )
            for table in schema_info.tables
        ],
        relationships=[
            RelationshipResponse(
                from_table=rel.from_table,
                from_column=rel.from_column,
                to_table=rel.to_table,
                to_column=rel.to_column,
            )
            for rel in schema_info.relationships
        ],
    )


async def create_postgres_session(
    host: str, port: int, user: str, password: str, database: str, schema_name: str
) -> ConnectionResponse:
    connector = PostgresConnector(
        dsn=f"postgresql://{user}:{password}@{host}:{port}/{database}",
        schema=schema_name,
    )
    await connector.connect()
    schema_info = await connector.extract_schema()

    session_id = str(uuid.uuid4())
    await connection_registry.register(session_id, connector, SourceType.POSTGRES)

    return _schema_info_to_response(session_id, SourceType.POSTGRES, schema_info)


async def create_mysql_session(
    host: str, port: int, user: str, password: str, database: str
) -> ConnectionResponse:
    connector = MySQLConnector(
        host=host, port=port, user=user, password=password, database=database
    )
    await connector.connect()
    schema_info = await connector.extract_schema()

    session_id = str(uuid.uuid4())
    await connection_registry.register(session_id, connector, SourceType.MYSQL)

    return _schema_info_to_response(session_id, SourceType.MYSQL, schema_info)


async def create_file_session(
    source_type: SourceType, file_path: str
) -> ConnectionResponse:
    connector = DuckDBFileConnector(source_type=source_type, file_path=file_path)
    await connector.connect()
    schema_info = await connector.extract_schema()

    session_id = str(uuid.uuid4())
    await connection_registry.register(session_id, connector, source_type)

    return _schema_info_to_response(session_id, source_type, schema_info)