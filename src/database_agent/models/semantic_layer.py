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
    
    
class ColumnDetail(BaseModel):
    physical_name: str = Field(description="Exact physical column name as given in the input, unchanged")
    business_name: str = Field(description="Short, human-friendly business name for this column")
    description: str = Field(description="One sentence describing what this column represents")
    synonyms: list[str] = Field(description="Alternative terms a user might use to refer to this column")


class TableDetailResponse(BaseModel):
    description: str = Field(description="One or two sentences describing what this table represents")
    synonyms: list[str] = Field(description="Alternative terms a user might use to refer to this table")
    columns: list[ColumnDetail]
    
    
class AssembleYamlRequest(BaseModel):
    selected_tables: list[str]


class AssembleYamlResponse(BaseModel):
    session_id: str
    file_path: str
    indexed_points: int