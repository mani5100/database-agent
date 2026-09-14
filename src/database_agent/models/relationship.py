# src/database_agent/models/relationship.py

from pydantic import BaseModel


class RelationshipItem(BaseModel):
    name: str
    from_model: str
    from_column: str
    to_model: str
    to_column: str
    type: str
    description: str


class RelationshipListResponse(BaseModel):
    relationships: list[RelationshipItem]


class AddRelationshipRequest(BaseModel):
    from_model: str
    from_column: str
    to_model: str
    to_column: str
    type: str = "many_to_one"
    description: str | None = None