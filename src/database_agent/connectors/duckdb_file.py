# src/src.database_agent/connectors/duckdb_file.py

import duckdb
import openpyxl

from src.database_agent.connectors.base import (
    BaseConnector,
    ColumnInfo,
    SchemaInfo,
    SourceType,
    TableInfo,
)

# DuckDB's own type names, normalized to the shared vocabulary used across connectors.
_DUCKDB_TYPE_MAP = {
    "BIGINT": "integer",
    "INTEGER": "integer",
    "SMALLINT": "integer",
    "DOUBLE": "float",
    "FLOAT": "float",
    "DECIMAL": "float",
    "VARCHAR": "text",
    "BOOLEAN": "boolean",
    "DATE": "date",
    "TIMESTAMP": "datetime",
}


def _normalize_type(duckdb_type: str) -> str:
    # DuckDB sometimes reports parametrized types, e.g. DECIMAL(10,2), strip params.
    base_type = duckdb_type.split("(")[0].strip().upper()
    return _DUCKDB_TYPE_MAP.get(base_type, "text")


def _get_excel_sheet_names(file_path: str) -> list[str]:
    """
    DuckDB's excel extension can read a named sheet (read_xlsx(..., sheet=...))
    but has no built-in function to list sheet names in a workbook.
    openpyxl handles discovery, DuckDB handles the actual data read.
    """
    workbook = openpyxl.load_workbook(file_path, read_only=True)
    try:
        return workbook.sheetnames
    finally:
        workbook.close()


class DuckDBFileConnector(BaseConnector):
    """
    Handles CSV and Excel directly. Google Sheets is expected to already be
    fetched and written to a local file (CSV export) before this connector
    is used, that fetch step lives outside this connector, not inside it.
    """

    def __init__(self, source_type: SourceType, file_path: str, memory_limit: str = "1GB"):
        assert source_type in (SourceType.CSV, SourceType.EXCEL, SourceType.GOOGLE_SHEETS)
        self.source_type = source_type
        self.file_path = file_path
        self.memory_limit = memory_limit
        self.conn: duckdb.DuckDBPyConnection | None = None
        self._table_names: list[str] = []

    async def connect(self) -> None:
        self.conn = duckdb.connect(database=":memory:")
        self.conn.execute(f"SET memory_limit='{self.memory_limit}'")
        self.conn.execute("INSTALL excel")
        self.conn.execute("LOAD excel")

        if self.source_type in (SourceType.CSV, SourceType.GOOGLE_SHEETS):
            # Google Sheets arrives here already exported to CSV by the fetch step.
            table_name = "data"
            self.conn.execute(
                f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto(?)",
                [self.file_path],
            )
            self._table_names = [table_name]

        elif self.source_type == SourceType.EXCEL:
            sheet_names = _get_excel_sheet_names(self.file_path)
            self._table_names = []
            for sheet_name in sheet_names:
                safe_table_name = f"sheet_{sheet_name}".replace(" ", "_")
                self.conn.execute(
                    f"CREATE TABLE {safe_table_name} AS "
                    f"SELECT * FROM read_xlsx(?, sheet=?)",
                    [self.file_path, sheet_name],
                )
                self._table_names.append(safe_table_name)

    async def disconnect(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    async def is_alive(self) -> bool:
        if self.conn is None:
            return False
        try:
            self.conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def get_reconnect_params(self) -> dict:
        return {
            "file_path": self.file_path,
            "memory_limit": self.memory_limit,
        }

    async def extract_schema(self) -> SchemaInfo:
        assert self.conn is not None, "connect() must be called before extract_schema()"

        tables: list[TableInfo] = []
        for table_name in self._table_names:
            columns_result = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
            columns = [
                ColumnInfo(
                    name=row[0],
                    data_type=_normalize_type(row[1]),
                    is_nullable=(row[2] == "YES"),
                    is_primary_key=False,  # files have no PK concept
                )
                for row in columns_result
            ]
            tables.append(TableInfo(name=table_name, columns=columns))

        return SchemaInfo(tables=tables, relationships=[])  # always empty, per project scope
    
    async def get_sample_rows(self, table_name: str, limit: int = 2) -> list[dict]:
        assert self.conn is not None, "connect() must be called before get_sample_rows()"
        result = self.conn.execute(f"SELECT * FROM {table_name} LIMIT ?", [limit])
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]