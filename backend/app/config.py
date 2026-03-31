"""Application configuration from environment variables."""

import os
from dataclasses import dataclass, field


def _env(key: str, default: str) -> str:
    """Read env var at call time (not at import time)."""
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment.

    Each field reads its env var at instantiation time so that
    monkeypatching os.environ in tests works correctly.
    """

    host: str = field(default_factory=lambda: _env("AAKTE_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(_env("AAKTE_PORT", "8000")))
    sqlite_path: str = field(default_factory=lambda: _env("AAKTE_SQLITE_PATH", "./data/aakte.db"))
    lancedb_path: str = field(default_factory=lambda: _env("AAKTE_LANCEDB_PATH", "./data/lancedb"))
    kuzu_path: str = field(default_factory=lambda: _env("AAKTE_KUZU_PATH", "./data/kuzu"))
    llm_base_url: str = field(default_factory=lambda: _env("AAKTE_LLM_BASE_URL", "http://localhost:11434"))
    llm_model: str = field(default_factory=lambda: _env("AAKTE_LLM_MODEL", "llama3.1:8b"))
    embedding_model: str = field(default_factory=lambda: _env("AAKTE_EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    max_document_size_mb: int = field(default_factory=lambda: int(_env("AAKTE_MAX_DOCUMENT_SIZE_MB", "50")))
    chunk_size_tokens: int = field(default_factory=lambda: int(_env("AAKTE_CHUNK_SIZE_TOKENS", "512")))
    chunk_overlap_tokens: int = field(default_factory=lambda: int(_env("AAKTE_CHUNK_OVERLAP_TOKENS", "64")))
    log_level: str = field(default_factory=lambda: _env("AAKTE_LOG_LEVEL", "INFO"))


settings = Settings()
