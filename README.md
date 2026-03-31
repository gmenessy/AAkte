# AAkte — Agentische Akte

Air-gapped, privacy-first Dokumentenanalyse mit RAG und Wissensgraph.

## Quick Start

```bash
# Lokal (Python 3.12+)
pip install -r requirements.txt
uvicorn backend.app.main:app --reload

# Docker
docker compose up --build
```

Oeffne http://localhost:8000 im Browser.

## Architektur

- **Frontend:** Vanilla HTML/CSS/JS — kein Framework, kein Build-Step
- **CleanDocs v2:** Browser-seitige PDF-Verarbeitung (pdf.js, TextRank, SimHash)
- **Backend:** Python 3.12 + FastAPI
- **Storage:** SQLite (Metadaten) + LanceDB (Vektoren) + Kuzu (Graph)
- **LLM:** Ollama / llama.cpp (lokal)

Siehe [SPEC.md](SPEC.md) fuer die vollstaendige Spezifikation.

## Status

Sprint 1 (Scaffolding & Ingestion-Vertrag) — implementiert.
