"""Unit tests for database models."""

from datetime import datetime, timezone
from uuid import UUID

from backend.app.models.db_models import Document


class TestDocumentModel:
    """Test the Document dataclass."""

    def test_defaults(self):
        doc = Document()
        assert isinstance(doc.id, UUID)
        assert doc.tenant_id == ""
        assert doc.status == "pending"
        assert doc.error_message is None
        assert doc.chunk_count == 0
        assert isinstance(doc.created_at, datetime)

    def test_created_at_is_utc(self):
        doc = Document()
        assert doc.created_at.tzinfo == timezone.utc

    def test_unique_ids(self):
        docs = [Document() for _ in range(10)]
        ids = {str(d.id) for d in docs}
        assert len(ids) == 10

    def test_custom_values(self):
        doc = Document(
            tenant_id="t1",
            filename="report.pdf",
            status="completed",
            language="de",
            chunk_count=23,
        )
        assert doc.tenant_id == "t1"
        assert doc.filename == "report.pdf"
        assert doc.status == "completed"
        assert doc.chunk_count == 23
