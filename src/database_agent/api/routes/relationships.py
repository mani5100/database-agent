# src/database_agent/api/routes/relationships.py

from fastapi import APIRouter, HTTPException

from database_agent.models.relationship import (
    AddRelationshipRequest,
    RelationshipItem,
    RelationshipListResponse,
)
from database_agent.services.relationship_editor import (
    add_relationship,
    assert_editable_source,
    delete_relationship,
    get_relationships,
    RelationshipEditError,
    update_relationship,
)
from database_agent.sessions.connection_registry import connection_registry, SessionNotFoundError

router = APIRouter()


@router.get("/session/{session_id}/relationships", response_model=RelationshipListResponse)
async def list_relationships(session_id: str) -> RelationshipListResponse:
    try:
        relationships = get_relationships(session_id)
    except RelationshipEditError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return RelationshipListResponse(relationships=[RelationshipItem(**r) for r in relationships])


@router.post("/session/{session_id}/relationships", response_model=RelationshipItem)
async def create_relationship(session_id: str, request: AddRelationshipRequest) -> RelationshipItem:
    try:
        connector = await connection_registry.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    try:
        assert_editable_source(connector.source_type)
        new_rel = add_relationship(
            session_id=session_id,
            from_model=request.from_model,
            from_column=request.from_column,
            to_model=request.to_model,
            to_column=request.to_column,
            rel_type=request.type,
            description=request.description,
        )
    except RelationshipEditError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return RelationshipItem(**new_rel)


@router.delete("/session/{session_id}/relationships/{relationship_name}")
async def remove_relationship(session_id: str, relationship_name: str) -> dict:
    try:
        connector = await connection_registry.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    try:
        assert_editable_source(connector.source_type)
        delete_relationship(session_id, relationship_name)
    except RelationshipEditError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"status": "deleted", "name": relationship_name}


@router.put("/session/{session_id}/relationships/{relationship_name}", response_model=RelationshipItem)
async def edit_relationship(
    session_id: str, relationship_name: str, request: AddRelationshipRequest
) -> RelationshipItem:
    try:
        connector = await connection_registry.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    try:
        assert_editable_source(connector.source_type)
        updated = update_relationship(
            session_id=session_id,
            relationship_name=relationship_name,
            from_model=request.from_model,
            from_column=request.from_column,
            to_model=request.to_model,
            to_column=request.to_column,
            rel_type=request.type,
            description=request.description,
        )
    except RelationshipEditError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return RelationshipItem(**updated)