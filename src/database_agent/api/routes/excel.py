# src/src.database_agent/api/routes/excel.py

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from src.database_agent.connectors.base import SourceType
from src.database_agent.models.connection import ConnectionResponse
from src.database_agent.services.connection_service import create_file_session

router = APIRouter()

_UPLOAD_DIR = Path("/tmp/src.database_agent_uploads")
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/connect/excel", response_model=ConnectionResponse)
async def connect_excel(file: UploadFile) -> ConnectionResponse:
    filename_lower = file.filename.lower()
    if filename_lower.endswith(".xls"):
        raise HTTPException(
            status_code=400,
            detail="Legacy .xls files are not supported, only .xlsx",
        )
    if not filename_lower.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Expected a .xlsx file")

    dest_path = _UPLOAD_DIR / f"{uuid.uuid4()}.xlsx"
    with dest_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        return await create_file_session(SourceType.EXCEL, str(dest_path))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {exc}")