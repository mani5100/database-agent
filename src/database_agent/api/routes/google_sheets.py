# src/src.database_agent/api/routes/google_sheets.py

from fastapi import APIRouter, HTTPException

from src.database_agent.models.connection import ConnectionResponse, GoogleSheetsConnectionRequest

router = APIRouter()


@router.post("/connect/google_sheets", response_model=ConnectionResponse)
async def connect_google_sheets(request: GoogleSheetsConnectionRequest) -> ConnectionResponse:
    # Not implemented yet: this route needs a fetch step (auth + pulling the
    # sheet, writing it to a local CSV) before create_file_session() can be
    # called the same way csv.py/excel.py do. That fetch step, and how auth
    # is supplied, hasn't been designed yet, flagging rather than stubbing
    # something that would silently look functional.
    raise HTTPException(
        status_code=501,
        detail="Google Sheets connector not yet implemented",
    )