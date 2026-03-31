"""API route definitions for AAkte."""

from fastapi import APIRouter, Path

from backend.app.models.schemas import DocumentIngestRequest, DocumentIngestResponse
from backend.app.services.ingestion_service import ingest_document

router = APIRouter(prefix="/api/v1/dossier", tags=["dossier"])

# Tenant-ID must be alphanumeric with hyphens/underscores (no path traversal)
TENANT_PATH = Path(
    ...,
    min_length=1,
    max_length=64,
    pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
    description="Tenant identifier (alphanumeric, hyphens, underscores)",
)


@router.post(
    "/{tenant_id}/documents",
    response_model=DocumentIngestResponse,
    status_code=202,
    summary="Ingest a CleanDocs-processed document",
    description=(
        "Accepts a cleaned Markdown document from the CleanDocs v2 browser pipeline "
        "and queues it for chunking, embedding, and graph extraction."
    ),
)
async def create_document(
    request: DocumentIngestRequest,
    tenant_id: str = TENANT_PATH,
) -> DocumentIngestResponse:
    """Accept a document for ingestion into the tenant's dossier."""
    return await ingest_document(tenant_id, request)
