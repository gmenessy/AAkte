"""Application configuration from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment."""

    host: str = os.getenv("AAKTE_HOST", "0.0.0.0")
    port: int = int(os.getenv("AAKTE_PORT", "8000"))
    sqlite_path: str = os.getenv("AAKTE_SQLITE_PATH", "./data/aakte.db")
    lancedb_path: str = os.getenv("AAKTE_LANCEDB_PATH", "./data/lancedb")
    kuzu_path: str = os.getenv("AAKTE_KUZU_PATH", "./data/kuzu")
    llm_base_url: str = os.getenv("AAKTE_LLM_BASE_URL", "http://localhost:11434")
    llm_model: str = os.getenv("AAKTE_LLM_MODEL", "llama3.1:8b")
    embedding_model: str = os.getenv("AAKTE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    max_document_size_mb: int = int(os.getenv("AAKTE_MAX_DOCUMENT_SIZE_MB", "50"))
    chunk_size_tokens: int = int(os.getenv("AAKTE_CHUNK_SIZE_TOKENS", "512"))
    chunk_overlap_tokens: int = int(os.getenv("AAKTE_CHUNK_OVERLAP_TOKENS", "64"))
    log_level: str = os.getenv("AAKTE_LOG_LEVEL", "INFO")


settings = Settings()
