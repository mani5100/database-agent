# src/src.database_agent/api/routes/csv.py

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from src.database_agent.connectors.base import SourceType
from src.database_agent.models.connection import ConnectionResponse
from src.database_agent.services.connection_service import create_file_session

router = APIRouter()

_UPLOAD_DIR = Path("/tmp/database_agent_uploads")
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/connect/csv", response_model=ConnectionResponse)
async def connect_csv(file: UploadFile) -> ConnectionResponse:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Expected a .csv file")

    dest_path = _UPLOAD_DIR / f"{uuid.uuid4()}.csv"
    with dest_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        return await create_file_session(SourceType.CSV, str(dest_path))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {exc}")