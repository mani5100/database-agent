# src/database_agent/models/query_context.py

from pydantic import BaseModel


class ColumnMapping(BaseModel):
    business_name: str
    physical_name: str
    data_type: str


class TableMapping(BaseModel):
    business_name: str
    physical_name: str
    columns: list[ColumnMapping]


class QueryContext(BaseModel):
    """
    The resolved set of tables/columns available for one question, built
    from Qdrant retrieval (expanded to full parent tables) plus relevant
    relationships pulled from the assembled YAML.
    """
    tables: list[TableMapping]
    relationships: list[dict]  # from_model, from_column, to_model, to_column, type