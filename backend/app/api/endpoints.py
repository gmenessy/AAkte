"""API route definitions for AAkte."""

from fastapi import APIRouter, Path

from app.models.schemas import DocumentIngestRequest, DocumentIngestResponse
from app.services.ingestion_service import ingest_document

router = APIRouter(prefix="/api/v1/dossier", tags=["dossier"])


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
    tenant_id: str = Path(..., min_length=1, max_length=64, description="Tenant identifier"),
) -> DocumentIngestResponse:
    """Accept a document for ingestion into the tenant's dossier."""
    return await ingest_document(tenant_id, request)
