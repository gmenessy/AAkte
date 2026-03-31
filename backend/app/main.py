"""AAkte — Agentische Akte: Privacy-first document analysis system.

FastAPI application entry point.
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from backend.app.api.endpoints import router as dossier_router
from backend.app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentische Akte (AAkte)",
    description="Air-gapped, privacy-first document analysis with RAG and knowledge graphs.",
    version="0.1.0",
)

# CORS — permissive for local development, locked down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
async def validation_error_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    """Map Pydantic validation errors to the structured error format."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected errors — never leak stack traces."""
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )


@app.get("/api/health", tags=["system"])
async def health_check() -> dict:
    """Liveness probe for Docker and monitoring."""
    return {"status": "ok", "version": "0.1.0"}


# Register API routes
app.include_router(dossier_router)

# Serve the frontend as static files at root
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
