# src/database_agent/api/router.py

from fastapi import APIRouter

from database_agent.api.routes import csv, erd, excel, google_sheets, mysql, postgres, semantic_layer, session, agent, google_auth, chats, relationships

router = APIRouter()
router.include_router(postgres.router, tags=["connections"])
router.include_router(mysql.router, tags=["connections"])
router.include_router(csv.router, tags=["connections"])
router.include_router(excel.router, tags=["connections"])
router.include_router(google_sheets.router, tags=["connections"])
router.include_router(session.router, tags=["sessions"])
router.include_router(semantic_layer.router, tags=["semantic_layer"])
router.include_router(agent.router, tags=["agent"])
router.include_router(erd.router, tags=["erd"])
router.include_router(google_auth.router, tags=["google_auth"])
router.include_router(chats.router, tags=["chats"])
router.include_router(relationships.router, tags=["relationships"])