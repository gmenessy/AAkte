"""Pydantic schemas for request/response validation."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class IngestMetrics(BaseModel):
    """Metrics from the CleanDocs v2 browser-side text reduction pipeline."""

    original_paragraphs: int = Field(..., ge=0, description="Paragraphs in original PDF")
    removed_boilerplate: int = Field(..., ge=0, description="Boilerplate paragraphs removed")
    textrank_retained: int = Field(..., ge=0, description="Paragraphs retained by TextRank")
    simhash_removed: int = Field(..., ge=0, description="Near-duplicates removed by SimHash")
    original_chars: int = Field(0, ge=0, description="Character count before reduction")
    reduced_chars: int = Field(0, ge=0, description="Character count after reduction")
    reduction_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Reduction ratio (0.0-1.0)")


class DocumentIngestRequest(BaseModel):
    """Request body for document ingestion after CleanDocs processing."""

    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original PDF filename",
    )
    raw_markdown: str = Field(
        ...,
        min_length=1,
        max_length=2_000_000,
        description="Cleaned Markdown text from CleanDocs pipeline",
    )
    metrics: IngestMetrics = Field(
        ...,
        description="CleanDocs processing metrics",
    )

    @field_validator("filename")
    @classmethod
    def sanitize_filename(cls, v: str) -> str:
        """Prevent path traversal in filenames."""
        # Strip directory components — only keep the basename
        sanitized = v.replace("\\", "/").split("/")[-1]
        if not sanitized or sanitized.startswith("."):
            raise ValueError("Invalid filename")
        return sanitized


class DocumentIngestResponse(BaseModel):
    """Response after accepting a document for ingestion."""

    document_id: UUID = Field(default_factory=uuid4)
    status: str = Field(default="processing", description="processing | completed | error")
    language_detected: str = Field(..., description="ISO 639-1 language code")


class DocumentDetail(BaseModel):
    """Full document details for GET responses."""

    document_id: UUID
    tenant_id: str
    filename: str
    status: str
    language: str
    chunk_count: int = 0
    ingestion_metrics: IngestMetrics
    created_at: datetime


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    documents: list[DocumentDetail] = []
    total: int = 0
    limit: int = 50
    offset: int = 0


class ErrorDetail(BaseModel):
    """Structured API error response."""

    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    """Wrapper for error responses."""

    error: ErrorDetail
