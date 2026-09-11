# src/database_agent/api/routes/google_auth.py

import uuid

import redis.asyncio as redis
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from database_agent.core.config import get_settings
from database_agent.sessions.google_auth_store import google_auth_store

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from database_agent.core.config import get_settings

router = APIRouter()

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

_redis = redis.from_url(get_settings().redis_url, decode_responses=True)


def _build_flow(state: str | None = None) -> Flow:
    settings = get_settings()
    client_config = {
        "web": {
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_oauth_redirect_uri],
        }
    }
    return Flow.from_client_config(
        client_config, scopes=_SCOPES, redirect_uri=settings.google_oauth_redirect_uri, state=state
    )


@router.get("/auth/google/login")
async def google_login():
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    # Persist this flow's code_verifier, keyed by its state param, so the
    # callback (a separate request) can rebuild an equivalent Flow with the
    # SAME verifier, required for PKCE token exchange to succeed.
    await _redis.set(f"oauth_verifier:{state}", flow.code_verifier, ex=600)

    return {"auth_url": auth_url}


@router.get("/auth/google/callback")
async def google_callback(code: str, state: str):
    code_verifier = await _redis.get(f"oauth_verifier:{state}")
    if code_verifier is None:
        raise HTTPException(status_code=400, detail="OAuth state expired or invalid, please try logging in again")

    flow = _build_flow(state=state)
    flow.code_verifier = code_verifier

    try:
        flow.fetch_token(code=code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code for tokens: {exc}")

    credentials = flow.credentials
    google_session_id = await google_auth_store.save_tokens(
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        expiry=credentials.expiry.isoformat() if credentials.expiry else "",
    )

    await _redis.delete(f"oauth_verifier:{state}")

    return RedirectResponse(url=f"http://localhost:5173?google_session_id={google_session_id}")



async def _get_credentials(google_session_id: str) -> Credentials:
    tokens = await google_auth_store.get_tokens(google_session_id)
    if tokens is None:
        raise HTTPException(status_code=404, detail="Google session not found or expired, please sign in again")

    settings = get_settings()
    return Credentials(
        token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
    )


@router.get("/auth/google/sheets")
async def search_sheets(google_session_id: str, query: str = ""):
    credentials = await _get_credentials(google_session_id)
    drive_service = build("drive", "v3", credentials=credentials)

    q = "mimeType='application/vnd.google-apps.spreadsheet'"
    if query:
        q += f" and name contains '{query}'"

    results = drive_service.files().list(
        q=q, pageSize=15, fields="files(id, name)"
    ).execute()

    return {"sheets": results.get("files", [])}