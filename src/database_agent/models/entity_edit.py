# src/database_agent/models/entity_edit.py

from pydantic import BaseModel


class ColumnEditRequest(BaseModel):
    """
    One column's edit, keyed by physical_name so the match is stable even
    though the column's business name is one of the fields being changed.
    """
    physical_name: str
    name: str
    description: str


class EntityEditRequest(BaseModel):
    name: str
    description: str
    columns: list[ColumnEditRequest]


class ColumnEditResponse(BaseModel):
    physical_name: str
    name: str
    description: str


class EntityEditResponse(BaseModel):
    physical_name: str
    name: str
    description: str
    columns: list[ColumnEditResponse]
    relationships_updated: int