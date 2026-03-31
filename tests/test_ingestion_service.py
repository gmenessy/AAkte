"""Unit tests for the ingestion service layer."""

import pytest

from backend.app.models.schemas import DocumentIngestRequest, IngestMetrics
from backend.app.services.ingestion_service import _detect_language, ingest_document


def _make_request(markdown: str, filename: str = "test.pdf") -> DocumentIngestRequest:
    """Helper to build a request with minimal boilerplate."""
    return DocumentIngestRequest(
        filename=filename,
        raw_markdown=markdown,
        metrics=IngestMetrics(
            original_paragraphs=10,
            removed_boilerplate=2,
            textrank_retained=6,
            simhash_removed=1,
        ),
    )


class TestLanguageDetection:
    """Test the heuristic language detection."""

    def test_german_text(self):
        assert _detect_language("Der Vertrag ist gueltig und die Parteien sind einverstanden") == "de"

    def test_english_text(self):
        assert _detect_language("The contract has been reviewed and approved by all parties") == "en"

    def test_heavy_german_text(self):
        text = (
            "Das ist ein Dokument mit vielen deutschen Woertern. "
            "Die Analyse der Daten zeigt, dass der Prozess nicht "
            "optimal ist und eine Verbesserung noetig ist."
        )
        assert _detect_language(text) == "de"

    def test_empty_text_defaults_to_en(self):
        assert _detect_language("") == "en"

    def test_single_word_defaults_to_en(self):
        assert _detect_language("hello") == "en"

    def test_mixed_text_with_german_majority(self):
        text = "Der Plan ist gut. The implementation needs work. Die Umsetzung ist wichtig."
        assert _detect_language(text) == "de"


class TestIngestDocument:
    """Test the ingest_document service function."""

    @pytest.mark.asyncio
    async def test_returns_processing_status(self):
        req = _make_request("Testinhalt")
        resp = await ingest_document("tenant-1", req)
        assert resp.status == "processing"

    @pytest.mark.asyncio
    async def test_returns_unique_document_id(self):
        req = _make_request("Testinhalt")
        ids = set()
        for _ in range(10):
            resp = await ingest_document("tenant-1", req)
            ids.add(str(resp.document_id))
        assert len(ids) == 10

    @pytest.mark.asyncio
    async def test_detects_german_language(self):
        req = _make_request("Der Vertrag ist gueltig und die Bedingungen sind klar definiert.")
        resp = await ingest_document("tenant-1", req)
        assert resp.language_detected == "de"

    @pytest.mark.asyncio
    async def test_detects_english_language(self):
        req = _make_request("This is a contract that has been reviewed by legal counsel.")
        resp = await ingest_document("tenant-1", req)
        assert resp.language_detected == "en"

    @pytest.mark.asyncio
    async def test_different_tenants_independent(self):
        req = _make_request("Inhalt")
        resp_a = await ingest_document("tenant-a", req)
        resp_b = await ingest_document("tenant-b", req)
        assert resp_a.document_id != resp_b.document_id
