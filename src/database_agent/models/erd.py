from pydantic import BaseModel


class ErdColumn(BaseModel):
    name: str
    is_primary_key: bool
    physical_type: str


class ErdTable(BaseModel):
    name: str
    columns: list[ErdColumn]


class ErdRelationship(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    type: str


class ErdResponse(BaseModel):
    tables: list[ErdTable]
    relationships: list[ErdRelationship]