"""Document ingestion service.

Sprint 1: Mock implementation — language detection returns "de",
no actual chunking or embedding happens yet.
"""

import logging
from uuid import UUID, uuid4

from backend.app.models.schemas import DocumentIngestRequest, DocumentIngestResponse

logger = logging.getLogger(__name__)


async def ingest_document(tenant_id: str, request: DocumentIngestRequest) -> DocumentIngestResponse:
    """Accept a cleaned document and start async processing.

    Sprint 1: Returns mock response with hardcoded language detection.
    Sprint 3+: Will chunk, embed, and store the document.
    """
    document_id = uuid4()

    # Log ingestion metrics for observability
    m = request.metrics
    logger.info(
        "Ingesting document=%s tenant=%s | "
        "paragraphs: %d original, %d boilerplate removed, "
        "%d retained (TextRank), %d deduped (SimHash) | "
        "reduction_ratio=%.1f%%",
        request.filename,
        tenant_id,
        m.original_paragraphs,
        m.removed_boilerplate,
        m.textrank_retained,
        m.simhash_removed,
        m.reduction_ratio * 100,
    )

    # TODO (Sprint 3): Detect language with langdetect
    language = _detect_language(request.raw_markdown)

    # TODO (Sprint 3): Persist to SQLite, chunk, embed, build graph
    return DocumentIngestResponse(
        document_id=document_id,
        status="processing",
        language_detected=language,
    )


def _detect_language(text: str) -> str:
    """Detect the language of the given text.

    Sprint 1: Returns "de" as a placeholder.
    Sprint 3: Will use langdetect or similar local library.
    """
    # Simple heuristic as a placeholder until langdetect is integrated
    german_indicators = ["der", "die", "das", "und", "ist", "ein", "eine", "nicht", "mit", "auf"]
    words = text.lower().split()[:200]
    german_count = sum(1 for w in words if w in german_indicators)

    if german_count > len(words) * 0.05:
        return "de"
    return "en"
