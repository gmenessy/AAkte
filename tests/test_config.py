"""Unit tests for application configuration."""

import os

from backend.app.config import Settings


class TestSettings:
    """Test configuration defaults and overrides."""

    def test_default_values(self):
        s = Settings()
        assert s.port == 8000
        assert s.log_level == "INFO"
        assert s.max_document_size_mb == 50
        assert s.chunk_size_tokens == 512
        assert s.chunk_overlap_tokens == 64

    def test_defaults_contain_expected_paths(self):
        s = Settings()
        assert "aakte.db" in s.sqlite_path
        assert "lancedb" in s.lancedb_path
        assert "kuzu" in s.kuzu_path

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("AAKTE_PORT", "9999")
        monkeypatch.setenv("AAKTE_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("AAKTE_MAX_DOCUMENT_SIZE_MB", "100")
        s = Settings()
        assert s.port == 9999
        assert s.log_level == "DEBUG"
        assert s.max_document_size_mb == 100

    def test_settings_are_frozen(self):
        s = Settings()
        try:
            s.port = 1234
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass
