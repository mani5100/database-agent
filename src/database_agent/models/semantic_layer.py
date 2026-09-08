# src/database_agent/models/semantic_layer.py

from pydantic import BaseModel, Field


class TableNameSuggestion(BaseModel):
    physical_name: str = Field(description="The exact physical table name as given in the input, unchanged")
    business_name: str = Field(description="A short, human-friendly business name for this table, e.g. 'customers', 'orders'")


class TableNamingResponse(BaseModel):
    tables: list[TableNameSuggestion]
    
class TableNamesResponse(BaseModel):
    session_id: str
    table_names: dict[str, str]