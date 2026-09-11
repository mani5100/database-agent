# src/database_agent/api/routes/google_sheets.py

import re
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from google.oauth2.credentials import Credentials

from database_agent.connectors.base import SourceType
from database_agent.core.config import get_settings
from database_agent.models.connection import ConnectionResponse, GoogleSheetsConnectionRequest
from database_agent.services.connection_service import create_file_session
from database_agent.sessions.google_auth_store import google_auth_store

router = APIRouter()

_UPLOAD_DIR = Path("/tmp/database_agent_uploads")
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _extract_sheet_id(sheet_url: str) -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not match:
        raise HTTPException(status_code=400, detail="Could not extract a sheet ID from the given URL")
    return match.group(1)


async def _fetch_public(sheet_id: str) -> bytes:
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    async with httpx.AsyncClient() as client:
        response = await client.get(export_url, follow_redirects=True)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Could not fetch this sheet. Make sure it's shared as 'Anyone with the link can view'.",
        )
    return response.content


async def _fetch_authenticated(sheet_id: str, google_session_id: str) -> bytes:
    tokens = await google_auth_store.get_tokens(google_session_id)
    if tokens is None:
        raise HTTPException(status_code=404, detail="Google session not found or expired, please sign in again")

    settings = get_settings()
    credentials = Credentials(
        token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
    )
    if not credentials.valid:
        credentials.refresh(__import__("google.auth.transport.requests", fromlist=["Request"]).Request())
        await google_auth_store.update_access_token(
            google_session_id, credentials.token, credentials.expiry.isoformat() if credentials.expiry else ""
        )

    export_url = f"https://www.googleapis.com/drive/v3/files/{sheet_id}/export?mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            export_url, headers={"Authorization": f"Bearer {credentials.token}"}
        )
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Could not fetch sheet: {response.text}")
    return response.content


@router.post("/connect/google_sheets", response_model=ConnectionResponse)
async def connect_google_sheets(request: GoogleSheetsConnectionRequest) -> ConnectionResponse:
    if request.google_session_id and request.sheet_id:
        sheet_id = request.sheet_id
        content = await _fetch_authenticated(sheet_id, request.google_session_id)
    elif request.sheet_url:
        sheet_id = _extract_sheet_id(request.sheet_url)
        content = await _fetch_public(sheet_id)
    else:
        raise HTTPException(status_code=400, detail="Provide either a sheet_url or a google_session_id + sheet_id")

    dest_path = _UPLOAD_DIR / f"{uuid.uuid4()}.xlsx"
    dest_path.write_bytes(content)

    try:
        return await create_file_session(SourceType.EXCEL, str(dest_path))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {exc}")