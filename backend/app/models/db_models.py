"""Database model definitions for SQLite.

These are placeholder dataclass models for Sprint 1.
Full SQLAlchemy/aiosqlite integration comes in Sprint 3.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Document:
    """Represents a document stored in SQLite."""

    id: UUID = field(default_factory=uuid4)
    tenant_id: str = ""
    filename: str = ""
    raw_markdown: str = ""
    language: str = ""
    status: str = "pending"  # pending | processing | completed | error
    error_message: str | None = None
    ingestion_metrics: dict = field(default_factory=dict)
    chunk_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
