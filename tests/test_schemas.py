"""Unit tests for Pydantic schemas (request/response validation)."""

import pytest
from pydantic import ValidationError

from backend.app.models.schemas import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    ErrorDetail,
    ErrorResponse,
    IngestMetrics,
)


class TestIngestMetrics:
    """Validate CleanDocs metrics constraints."""

    def test_valid_metrics(self):
        m = IngestMetrics(
            original_paragraphs=100,
            removed_boilerplate=20,
            textrank_retained=60,
            simhash_removed=10,
            original_chars=50000,
            reduced_chars=20000,
            reduction_ratio=0.6,
        )
        assert m.original_paragraphs == 100
        assert m.reduction_ratio == 0.6

    def test_defaults_for_optional_fields(self):
        m = IngestMetrics(
            original_paragraphs=10,
            removed_boilerplate=2,
            textrank_retained=6,
            simhash_removed=1,
        )
        assert m.original_chars == 0
        assert m.reduced_chars == 0
        assert m.reduction_ratio == 0.0

    def test_negative_paragraphs_rejected(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            IngestMetrics(
                original_paragraphs=-1,
                removed_boilerplate=0,
                textrank_retained=0,
                simhash_removed=0,
            )

    def test_reduction_ratio_above_one_rejected(self):
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            IngestMetrics(
                original_paragraphs=10,
                removed_boilerplate=2,
                textrank_retained=6,
                simhash_removed=1,
                reduction_ratio=1.5,
            )

    def test_reduction_ratio_negative_rejected(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            IngestMetrics(
                original_paragraphs=10,
                removed_boilerplate=0,
                textrank_retained=10,
                simhash_removed=0,
                reduction_ratio=-0.1,
            )


class TestDocumentIngestRequest:
    """Validate document ingestion request schemas."""

    def test_valid_request(self):
        req = DocumentIngestRequest(
            filename="report.pdf",
            raw_markdown="# Report\n\nContent here.",
            metrics=IngestMetrics(
                original_paragraphs=10,
                removed_boilerplate=2,
                textrank_retained=6,
                simhash_removed=1,
            ),
        )
        assert req.filename == "report.pdf"

    def test_empty_filename_rejected(self):
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            DocumentIngestRequest(
                filename="",
                raw_markdown="content",
                metrics=IngestMetrics(
                    original_paragraphs=1,
                    removed_boilerplate=0,
                    textrank_retained=1,
                    simhash_removed=0,
                ),
            )

    def test_empty_markdown_rejected(self):
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            DocumentIngestRequest(
                filename="test.pdf",
                raw_markdown="",
                metrics=IngestMetrics(
                    original_paragraphs=1,
                    removed_boilerplate=0,
                    textrank_retained=1,
                    simhash_removed=0,
                ),
            )

    def test_path_traversal_stripped(self):
        req = DocumentIngestRequest(
            filename="../../../etc/passwd",
            raw_markdown="content",
            metrics=IngestMetrics(
                original_paragraphs=1,
                removed_boilerplate=0,
                textrank_retained=1,
                simhash_removed=0,
            ),
        )
        assert req.filename == "passwd"
        assert "/" not in req.filename
        assert ".." not in req.filename

    def test_backslash_path_traversal_stripped(self):
        req = DocumentIngestRequest(
            filename="..\\..\\windows\\system32\\config",
            raw_markdown="content",
            metrics=IngestMetrics(
                original_paragraphs=1,
                removed_boilerplate=0,
                textrank_retained=1,
                simhash_removed=0,
            ),
        )
        assert req.filename == "config"

    def test_dotfile_rejected(self):
        with pytest.raises(ValidationError, match="Invalid filename"):
            DocumentIngestRequest(
                filename=".env",
                raw_markdown="content",
                metrics=IngestMetrics(
                    original_paragraphs=1,
                    removed_boilerplate=0,
                    textrank_retained=1,
                    simhash_removed=0,
                ),
            )

    def test_filename_max_length(self):
        with pytest.raises(ValidationError, match="at most 255"):
            DocumentIngestRequest(
                filename="a" * 256 + ".pdf",
                raw_markdown="content",
                metrics=IngestMetrics(
                    original_paragraphs=1,
                    removed_boilerplate=0,
                    textrank_retained=1,
                    simhash_removed=0,
                ),
            )

    def test_unicode_filename_accepted(self):
        req = DocumentIngestRequest(
            filename="Ueberblick_Geschaeftsbericht_2024.pdf",
            raw_markdown="Inhalt",
            metrics=IngestMetrics(
                original_paragraphs=1,
                removed_boilerplate=0,
                textrank_retained=1,
                simhash_removed=0,
            ),
        )
        assert "Ueberblick" in req.filename


class TestDocumentIngestResponse:
    """Validate response model."""

    def test_response_has_uuid(self):
        resp = DocumentIngestResponse(language_detected="de")
        assert resp.document_id is not None
        assert resp.status == "processing"
        assert resp.language_detected == "de"

    def test_response_serialization(self):
        resp = DocumentIngestResponse(language_detected="en")
        data = resp.model_dump(mode="json")
        assert "document_id" in data
        assert isinstance(data["document_id"], str)
        assert len(data["document_id"]) == 36  # UUID format


class TestErrorModels:
    """Validate error response structures."""

    def test_error_detail(self):
        err = ErrorDetail(code="TEST_ERROR", message="Something failed")
        assert err.details is None

    def test_error_response_with_details(self):
        resp = ErrorResponse(
            error=ErrorDetail(
                code="DOCUMENT_TOO_LARGE",
                message="Too large",
                details={"max_size_mb": 50, "actual_size_mb": 72},
            )
        )
        assert resp.error.details["max_size_mb"] == 50
