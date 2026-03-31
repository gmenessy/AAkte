"""Shared test fixtures for AAkte."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.fixture
def client():
    """Synchronous TestClient-like fixture using httpx."""
    from starlette.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture
def valid_ingest_payload():
    """A valid document ingestion request body."""
    return {
        "filename": "vertrag_2024.pdf",
        "raw_markdown": "# Vertrag\n\nDer Vertrag ist gueltig und bindend.",
        "metrics": {
            "original_paragraphs": 42,
            "removed_boilerplate": 8,
            "textrank_retained": 28,
            "simhash_removed": 4,
            "original_chars": 12000,
            "reduced_chars": 4800,
            "reduction_ratio": 0.6,
        },
    }


@pytest.fixture
def minimal_ingest_payload():
    """Minimal valid ingestion payload (only required fields)."""
    return {
        "filename": "test.pdf",
        "raw_markdown": "Inhalt",
        "metrics": {
            "original_paragraphs": 1,
            "removed_boilerplate": 0,
            "textrank_retained": 1,
            "simhash_removed": 0,
        },
    }


TENANT_ID = "test-tenant"
API_BASE = f"/api/v1/dossier/{TENANT_ID}/documents"
