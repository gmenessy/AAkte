"""AAkte — Agentische Akte: Privacy-first document analysis system.

FastAPI application entry point.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import router as dossier_router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Agentische Akte (AAkte)",
    description="Air-gapped, privacy-first document analysis with RAG and knowledge graphs.",
    version="0.1.0",
)

# Register API routes
app.include_router(dossier_router)

# Serve the frontend as static files at root
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
