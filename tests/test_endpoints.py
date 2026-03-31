"""Integration tests for API endpoints."""

import pytest

from tests.conftest import API_BASE, TENANT_ID


class TestHealthEndpoint:
    """Test the /api/health liveness probe."""

    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestDocumentIngestion:
    """Test POST /api/v1/dossier/{tenant_id}/documents."""

    def test_successful_ingestion(self, client, valid_ingest_payload):
        resp = client.post(API_BASE, json=valid_ingest_payload)
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "processing"
        assert data["language_detected"] in ("de", "en")
        assert len(data["document_id"]) == 36

    def test_minimal_payload(self, client, minimal_ingest_payload):
        resp = client.post(API_BASE, json=minimal_ingest_payload)
        assert resp.status_code == 202

    def test_each_ingestion_returns_unique_id(self, client, valid_ingest_payload):
        ids = set()
        for _ in range(5):
            resp = client.post(API_BASE, json=valid_ingest_payload)
            assert resp.status_code == 202
            ids.add(resp.json()["document_id"])
        assert len(ids) == 5

    def test_german_text_detected_as_de(self, client):
        payload = {
            "filename": "deutsch.pdf",
            "raw_markdown": (
                "Der Vertrag ist gueltig und die Parteien haben sich auf "
                "die folgenden Bedingungen geeinigt. Das Dokument ist bindend "
                "und nicht anfechtbar."
            ),
            "metrics": {
                "original_paragraphs": 5,
                "removed_boilerplate": 1,
                "textrank_retained": 3,
                "simhash_removed": 0,
            },
        }
        resp = client.post(API_BASE, json=payload)
        assert resp.status_code == 202
        assert resp.json()["language_detected"] == "de"

    def test_english_text_detected_as_en(self, client):
        payload = {
            "filename": "english.pdf",
            "raw_markdown": (
                "The contract has been reviewed by all parties involved. "
                "All terms and conditions have been accepted. This agreement "
                "shall be binding upon execution by both parties."
            ),
            "metrics": {
                "original_paragraphs": 5,
                "removed_boilerplate": 1,
                "textrank_retained": 3,
                "simhash_removed": 0,
            },
        }
        resp = client.post(API_BASE, json=payload)
        assert resp.status_code == 202
        assert resp.json()["language_detected"] == "en"

    def test_missing_filename_returns_422(self, client):
        payload = {
            "raw_markdown": "content",
            "metrics": {
                "original_paragraphs": 1,
                "removed_boilerplate": 0,
                "textrank_retained": 1,
                "simhash_removed": 0,
            },
        }
        resp = client.post(API_BASE, json=payload)
        assert resp.status_code == 422

    def test_missing_markdown_returns_422(self, client):
        payload = {
            "filename": "test.pdf",
            "metrics": {
                "original_paragraphs": 1,
                "removed_boilerplate": 0,
                "textrank_retained": 1,
                "simhash_removed": 0,
            },
        }
        resp = client.post(API_BASE, json=payload)
        assert resp.status_code == 422

    def test_missing_metrics_returns_422(self, client):
        payload = {
            "filename": "test.pdf",
            "raw_markdown": "content",
        }
        resp = client.post(API_BASE, json=payload)
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        resp = client.post(API_BASE, json={})
        assert resp.status_code == 422

    def test_invalid_json_returns_422(self, client):
        resp = client.post(
            API_BASE,
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_negative_metrics_returns_422(self, client):
        payload = {
            "filename": "test.pdf",
            "raw_markdown": "content",
            "metrics": {
                "original_paragraphs": -5,
                "removed_boilerplate": 0,
                "textrank_retained": 0,
                "simhash_removed": 0,
            },
        }
        resp = client.post(API_BASE, json=payload)
        assert resp.status_code == 422


class TestTenantIsolation:
    """Test tenant_id path parameter validation."""

    def test_valid_tenant_ids(self, client, valid_ingest_payload):
        for tid in ["default", "mandant-01", "TENANT_42", "a"]:
            url = f"/api/v1/dossier/{tid}/documents"
            resp = client.post(url, json=valid_ingest_payload)
            assert resp.status_code == 202, f"Failed for tenant_id={tid}"

    def test_tenant_id_with_special_chars_rejected(self, client, valid_ingest_payload):
        for tid in ["../etc", "tenant/sub", "tenant;drop", "ten ant"]:
            url = f"/api/v1/dossier/{tid}/documents"
            resp = client.post(url, json=valid_ingest_payload)
            assert resp.status_code in (404, 405, 422), f"Should reject tenant_id={tid}"

    def test_tenant_starting_with_hyphen_rejected(self, client, valid_ingest_payload):
        url = "/api/v1/dossier/-bad-tenant/documents"
        resp = client.post(url, json=valid_ingest_payload)
        assert resp.status_code == 422


class TestStaticFiles:
    """Test that frontend is served correctly."""

    def test_index_html_served(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Agentische Akte" in resp.text

    def test_css_served(self, client):
        resp = client.get("/style.css")
        assert resp.status_code == 200
        assert "--bg-primary" in resp.text

    def test_js_served(self, client):
        resp = client.get("/app.js")
        assert resp.status_code == 200
        assert "CleanDocs" in resp.text

    def test_cleandocs_js_served(self, client):
        resp = client.get("/cleandocs_pipeline.js")
        assert resp.status_code == 200

    def test_nonexistent_file_returns_404(self, client):
        resp = client.get("/does_not_exist.js")
        assert resp.status_code == 404
