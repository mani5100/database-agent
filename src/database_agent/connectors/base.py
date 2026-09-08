# src/src.database_agent/connectors/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class SourceType(str, Enum):
    POSTGRES = "postgres"
    MYSQL = "mysql"
    CSV = "csv"
    EXCEL = "excel"
    GOOGLE_SHEETS = "google_sheets"


@dataclass
class ColumnInfo:
    name: str
    data_type: str          # normalized type string, e.g. "integer", "text", "date"
    is_nullable: bool = True
    is_primary_key: bool = False


@dataclass
class RelationshipInfo:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    # Postgres/MySQL only. Stays empty for file-based sources per project scope.


@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo] = field(default_factory=list)


@dataclass
class SchemaInfo:
    tables: list[TableInfo] = field(default_factory=list)
    relationships: list[RelationshipInfo] = field(default_factory=list)


class BaseConnector(ABC):
    """
    Every source-type connector (Postgres, MySQL, DuckDB-file) implements this.
    Routes/services depend on this interface only, never on a concrete
    connector class, so adding a new source type never touches calling code.
    """

    source_type: SourceType

    @abstractmethod
    async def connect(self) -> None:
        """Open the underlying connection/pool or DuckDB instance."""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the underlying connection/pool or DuckDB instance cleanly."""
        raise NotImplementedError

    @abstractmethod
    async def extract_schema(self) -> SchemaInfo:
        """
        Return tables, columns, and (where applicable) relationships.
        File-based connectors return relationships=[] always, per project scope.
        """
        raise NotImplementedError

    @abstractmethod
    async def is_alive(self) -> bool:
        """
        Health check for the underlying connection. Used by connection_registry
        before reusing a cached connection, to avoid handing back a dead one.
        """
        raise NotImplementedError

    @abstractmethod
    def get_reconnect_params(self) -> dict:
        """
        Returns exactly the constructor kwargs needed to rebuild this
        connector later (used when Redis metadata exists but this worker
        has no live connector object in memory). Must not include the live
        pool/connection object itself, only serializable primitives.
        """
        raise NotImplementedError
    @abstractmethod
    async def get_sample_rows(self, table_name: str, limit: int = 2) -> list[dict]:
        """
        Returns up to `limit` rows from the given table as plain dicts
        (column_name -> value). Used to give the semantic-layer LLM calls
        concrete data context, not just column names/types.
        """
        raise NotImplementedError