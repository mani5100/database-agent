# src/database_agent/models/connection.py

from pydantic import BaseModel, Field


class PostgresConnectionRequest(BaseModel):
    host: str
    port: int = 5432
    user: str
    password: str
    database: str
    schema_name: str = Field(default="public", alias="schema")


class MySQLConnectionRequest(BaseModel):
    host: str
    port: int = 3306
    user: str
    password: str
    database: str


class GoogleSheetsConnectionRequest(BaseModel):
    sheet_url: str
    # Auth details (service account / OAuth token) intentionally left out here,
    # that belongs to the Sheets-fetch step, not this schema yet.


class ColumnResponse(BaseModel):
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool


class TableResponse(BaseModel):
    name: str
    columns: list[ColumnResponse]


class RelationshipResponse(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str


class ConnectionResponse(BaseModel):
    session_id: str
    source_type: str
    tables: list[TableResponse]
    relationships: list[RelationshipResponse]
    
class GoogleSheetsConnectionRequest(BaseModel):
    sheet_url: str | None = None
    google_session_id: str | None = None
    sheet_id: str | None = None