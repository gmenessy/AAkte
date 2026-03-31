# Agentische Akte (AAkte) - System Specification v1.0

## 1. Vision & Ziel

Die **Agentische Akte** ist ein air-gapped, privacy-first Dokumentenanalyse-System.
Dokumente werden lokal im Browser vorverarbeitet (PDF-Parsing, Text-Reduktion),
dann an ein lokales Backend gesendet, wo sie per RAG und Wissensgraph
analysiert und abgefragt werden koennen.

**Kernprinzip:** Keine Daten verlassen das lokale Netzwerk. Kein Cloud-API-Aufruf.

---

## 2. Architektur-Ueberblick

```
+---------------------------------------------------------+
|                      BROWSER                            |
|                                                         |
|  +---------------------------------------------------+ |
|  |              CleanDocs v2 Pipeline                 | |
|  |                                                    | |
|  |  PDF Upload --> pdf.js Parsing --> Markdown         | |
|  |  --> TextRank (Satz-Relevanz) --> SimHash (Dedup)  | |
|  |  --> 50-70% Textreduktion --> Clean Markdown        | |
|  +---------------------------------------------------+ |
|           |                          ^                  |
|           | POST /api/v1/...         | SSE Events       |
|           v                          |                  |
+---------------------------------------------------------+
            |                          ^
            v                          |
+---------------------------------------------------------+
|                   FastAPI Backend                        |
|                                                         |
|  +------------+  +------------+  +-----------------+    |
|  |  Ingestion |  |    RAG     |  |  Graph Builder  |    |
|  |  Service   |  |  Service   |  |    Service      |    |
|  +------+-----+  +------+-----+  +--------+--------+   |
|         |               |                  |            |
|  +------v---------------v------------------v--------+   |
|  |                 Storage Layer                     |   |
|  |                                                   |   |
|  |  SQLite        LanceDB          Kuzu             |   |
|  |  (Metadaten,   (Vektor-         (Wissensgraph:   |   |
|  |   Dokumente,    Embeddings      Entitaeten,      |   |
|  |   Tenants)      fuer RAG)       Relationen)      |   |
|  +---------------------------------------------------+  |
|                                                         |
|  +---------------------------------------------------+  |
|  |           Lokales LLM (Ollama / llama.cpp)        |  |
|  |           Embedding-Modell (lokal)                |  |
|  +---------------------------------------------------+  |
+---------------------------------------------------------+
```

---

## 3. Technologie-Stack

| Schicht       | Technologie                  | Version    | Zweck                                   |
|---------------|------------------------------|------------|-----------------------------------------|
| Frontend      | Vanilla HTML5/CSS/JS         | ES2020+    | UI, PDF-Verarbeitung, CleanDocs         |
| PDF-Parsing   | pdf.js (Mozilla)             | >= 4.0     | Browser-seitiges PDF-zu-Text            |
| Backend       | Python + FastAPI             | 3.12 / 0.115+ | REST-API, SSE, Orchestrierung        |
| Validierung   | Pydantic                     | >= 2.0     | Schema-Validierung, Serialisierung      |
| DB Relational | SQLite                       | 3.45+      | Metadaten, Dokumente, Tenants           |
| DB Vektor     | LanceDB                      | >= 0.6     | Vektor-Embeddings fuer RAG              |
| DB Graph      | Kuzu                         | >= 0.3     | Wissensgraph (Entitaeten, Relationen)   |
| LLM           | Ollama / llama.cpp           | lokal      | Textgenerierung, Analyse                |
| Embeddings    | sentence-transformers (lokal)| lokal      | Vektor-Erzeugung fuer RAG              |
| Container     | Docker + docker-compose      | >= 24.0    | Deployment, Reproduzierbarkeit          |

### 3.1 Verbotene Technologien

- **KEIN** React, Vue, Angular, Svelte oder sonstige JS-Frameworks
- **KEIN** Tailwind, PostCSS oder sonstige CSS-Build-Steps
- **KEIN** Webpack, Vite, esbuild oder sonstige JS-Bundler
- **KEINE** externen Cloud-APIs (OpenAI, Anthropic, DeepL, Google, etc.)
- **KEIN** Node.js im Backend

---

## 4. Datenmodell

### 4.1 Tenant-Isolation

Jeder Tenant hat eine strikte Datenisolation. Alle Abfragen werden
durch `tenant_id` gefiltert. Es gibt keine mandantenubergreifenden Zugriffe.

```
Tenant
  ├── id: UUID (PK)
  ├── name: str
  ├── created_at: datetime
  └── config: JSON (optionale Tenant-spezifische Einstellungen)
```

### 4.2 Dokument

```
Document
  ├── id: UUID (PK)
  ├── tenant_id: UUID (FK -> Tenant)
  ├── filename: str
  ├── raw_markdown: text          # CleanDocs-bereinigter Inhalt
  ├── language: str               # ISO 639-1 (z.B. "de", "en")
  ├── status: enum                # "pending", "processing", "completed", "error"
  ├── error_message: str | null   # Fehlerbeschreibung bei status="error"
  ├── ingestion_metrics: JSON     # CleanDocs-Metriken (siehe 4.3)
  ├── chunk_count: int            # Anzahl erzeugter Chunks
  ├── created_at: datetime
  └── updated_at: datetime
```

### 4.3 CleanDocs-Metriken

Die Metriken dokumentieren die Browser-seitige Textreduktion:

```
IngestMetrics
  ├── original_paragraphs: int    # Absaetze im Original-PDF
  ├── removed_boilerplate: int    # Entfernte Boilerplate-Absaetze (Header/Footer/etc.)
  ├── textrank_retained: int      # Durch TextRank beibehaltene Absaetze
  ├── simhash_removed: int        # Durch SimHash als Duplikate entfernte Absaetze
  ├── original_chars: int         # Zeichenanzahl vor Reduktion
  ├── reduced_chars: int          # Zeichenanzahl nach Reduktion
  └── reduction_ratio: float      # Reduktionsrate (0.0 - 1.0)
```

### 4.4 Chunk (fuer RAG)

```
Chunk
  ├── id: UUID (PK)
  ├── document_id: UUID (FK -> Document)
  ├── tenant_id: UUID             # Denormalisiert fuer schnelle Filterung
  ├── content: text               # Chunk-Text
  ├── chunk_index: int            # Position im Dokument
  ├── heading: str | null         # Ueberschrift des Abschnitts
  ├── token_count: int            # Token-Anzahl (fuer LLM-Kontext-Budgetierung)
  └── embedding: vector[384]      # Vektor-Embedding (Dimension je nach Modell)
```

### 4.5 Wissensgraph-Schema (Kuzu)

```
Node: Entity
  ├── id: UUID
  ├── tenant_id: UUID
  ├── name: str
  ├── entity_type: str            # "Person", "Organisation", "Ort", "Datum", "Konzept"
  ├── document_id: UUID           # Herkunftsdokument
  └── metadata: JSON

Edge: Relation
  ├── source_id: UUID (FK -> Entity)
  ├── target_id: UUID (FK -> Entity)
  ├── relation_type: str          # "arbeitet_bei", "erwaehnt_in", "bezieht_sich_auf", etc.
  ├── confidence: float           # 0.0 - 1.0
  ├── document_id: UUID           # Herkunftsdokument
  └── evidence: str               # Textbeleg aus dem Dokument
```

---

## 5. API-Spezifikation

### 5.1 Basis-URL

```
/api/v1/dossier/{tenant_id}
```

Alle Endpunkte sind Tenant-scoped. Der `tenant_id` Parameter ist in jedem Pfad enthalten.

### 5.2 Endpunkte

#### 5.2.1 Dokument-Ingestion

```
POST /api/v1/dossier/{tenant_id}/documents
```

**Request Body:**
```json
{
  "filename": "vertrag_2024.pdf",
  "raw_markdown": "# Vertrag\n\nDies ist ein Beispielvertrag...",
  "metrics": {
    "original_paragraphs": 142,
    "removed_boilerplate": 38,
    "textrank_retained": 67,
    "simhash_removed": 12,
    "original_chars": 48000,
    "reduced_chars": 19200,
    "reduction_ratio": 0.6
  }
}
```

**Response (202 Accepted):**
```json
{
  "document_id": "a1b2c3d4-...",
  "status": "processing",
  "language_detected": "de"
}
```

**Verarbeitung (asynchron):**
1. Sprache erkennen (lokal, z.B. langdetect)
2. Markdown in Chunks aufteilen (semantisch, ~512 Tokens)
3. Embeddings erzeugen (lokales Modell)
4. In LanceDB speichern
5. Named Entity Recognition (NER) durchfuehren
6. Entitaeten und Relationen in Kuzu speichern
7. Status auf "completed" setzen

#### 5.2.2 Dokument-Status

```
GET /api/v1/dossier/{tenant_id}/documents/{document_id}
```

**Response:**
```json
{
  "document_id": "a1b2c3d4-...",
  "filename": "vertrag_2024.pdf",
  "status": "completed",
  "language": "de",
  "chunk_count": 23,
  "ingestion_metrics": { ... },
  "created_at": "2026-03-31T10:00:00Z"
}
```

#### 5.2.3 Dokument-Liste

```
GET /api/v1/dossier/{tenant_id}/documents
```

**Query-Parameter:**
- `status` (optional): Filter nach Status
- `limit` (optional, default=50): Anzahl Ergebnisse
- `offset` (optional, default=0): Pagination-Offset

**Response:**
```json
{
  "documents": [ ... ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

#### 5.2.4 RAG-Abfrage (SSE)

```
POST /api/v1/dossier/{tenant_id}/query
Content-Type: application/json
Accept: text/event-stream
```

**Request Body:**
```json
{
  "question": "Welche Kuendigungsfristen sind in den Vertraegen definiert?",
  "document_ids": ["a1b2c3d4-..."],
  "top_k": 5,
  "include_graph_context": true
}
```

**SSE Response Stream:**
```
event: sources
data: {"chunks": [{"document_id": "...", "content": "...", "score": 0.87}]}

event: token
data: {"text": "Laut"}

event: token
data: {"text": " den"}

event: token
data: {"text": " analysierten"}

...

event: graph_context
data: {"entities": [...], "relations": [...]}

event: done
data: {"total_tokens": 342}
```

#### 5.2.5 Entitaeten abfragen

```
GET /api/v1/dossier/{tenant_id}/entities
```

**Query-Parameter:**
- `document_id` (optional): Filter nach Dokument
- `entity_type` (optional): Filter nach Typ ("Person", "Organisation", etc.)

#### 5.2.6 Graph-Traversal

```
POST /api/v1/dossier/{tenant_id}/graph/traverse
```

**Request Body:**
```json
{
  "entity_id": "...",
  "depth": 2,
  "relation_types": ["arbeitet_bei", "erwaehnt_in"]
}
```

#### 5.2.7 Dokument loeschen

```
DELETE /api/v1/dossier/{tenant_id}/documents/{document_id}
```

Loescht das Dokument, alle zugehoerigen Chunks, Embeddings und Graph-Knoten.

---

## 6. CleanDocs v2 Pipeline (Browser)

### 6.1 Verarbeitungsstufen

```
PDF-Datei
  │
  ├─ Stufe 1: PDF-Parsing (pdf.js)
  │   └── Extraktion von Text, Schriftgroessen, Positionen
  │
  ├─ Stufe 2: Strukturerkennung
  │   └── Ueberschriften, Absaetze, Listen, Tabellen identifizieren
  │
  ├─ Stufe 3: Boilerplate-Entfernung
  │   └── Header, Footer, Seitenzahlen, wiederkehrende Textbloecke entfernen
  │
  ├─ Stufe 4: TextRank-Filterung
  │   └── Satz-Relevanz-Bewertung, nur Top-Saetze behalten
  │
  ├─ Stufe 5: SimHash-Deduplizierung
  │   └── Near-Duplicate-Absaetze erkennen und entfernen
  │
  └─ Stufe 6: Markdown-Erzeugung
      └── Strukturiertes Markdown mit Ueberschriften-Hierarchie
```

### 6.2 Ziel-Reduktionsrate

- **Boilerplate-Entfernung:** 10-25% Reduktion
- **TextRank-Filterung:** 20-35% Reduktion
- **SimHash-Deduplizierung:** 5-15% Reduktion
- **Gesamt-Ziel:** 50-70% Textreduktion

### 6.3 Browser-Kompatibilitaet

- Chrome/Edge >= 90
- Firefox >= 90
- Safari >= 15
- Kein IE-Support

---

## 7. Sicherheit & Datenschutz

### 7.1 Netzwerk-Isolation

- Das System laeuft vollstaendig im lokalen Netzwerk
- Docker-Container verwenden `network_mode: bridge` (kein externer Zugang noetig)
- Content-Security-Policy Header: `default-src 'self'`

### 7.2 Tenant-Isolation

- Jede Datenbank-Abfrage filtert nach `tenant_id`
- Kein Tenant kann Daten eines anderen Tenants sehen
- `tenant_id` wird aus dem URL-Pfad extrahiert (nicht aus dem Body)

### 7.3 Input-Validierung

- Alle Eingaben werden durch Pydantic-Schemas validiert
- Maximale Dokumentgroesse: 50 MB (konfigurierbar)
- Maximale Markdown-Laenge: 2.000.000 Zeichen
- Filename-Sanitization gegen Path-Traversal

### 7.4 Keine Authentifizierung (v1)

In Version 1 gibt es keine Authentifizierung, da das System air-gapped betrieben wird.
Fuer zukuenftige Versionen ist ein API-Key-basiertes System vorgesehen.

---

## 8. Konfiguration

Alle Konfiguration erfolgt ueber Umgebungsvariablen:

| Variable                    | Default                    | Beschreibung                        |
|-----------------------------|----------------------------|-------------------------------------|
| `AAKTE_HOST`                | `0.0.0.0`                 | Server-Bind-Adresse                 |
| `AAKTE_PORT`                | `8000`                     | Server-Port                         |
| `AAKTE_SQLITE_PATH`         | `./data/aakte.db`          | Pfad zur SQLite-Datenbank           |
| `AAKTE_LANCEDB_PATH`        | `./data/lancedb`           | Pfad zum LanceDB-Verzeichnis        |
| `AAKTE_KUZU_PATH`           | `./data/kuzu`              | Pfad zur Kuzu-Datenbank             |
| `AAKTE_LLM_BASE_URL`        | `http://localhost:11434`   | Ollama-API-URL                      |
| `AAKTE_LLM_MODEL`           | `llama3.1:8b`              | LLM-Modell fuer Analyse             |
| `AAKTE_EMBEDDING_MODEL`     | `all-MiniLM-L6-v2`        | Embedding-Modell                    |
| `AAKTE_MAX_DOCUMENT_SIZE_MB`| `50`                       | Maximale Dokumentgroesse in MB      |
| `AAKTE_CHUNK_SIZE_TOKENS`   | `512`                      | Chunk-Groesse in Tokens             |
| `AAKTE_CHUNK_OVERLAP_TOKENS`| `64`                       | Chunk-Ueberlappung in Tokens        |
| `AAKTE_LOG_LEVEL`           | `INFO`                     | Log-Level (DEBUG, INFO, WARN, ERROR)|

---

## 9. Sprint-Planung

### Sprint 1: Scaffolding & Ingestion-Vertrag (aktuell)

**Ziel:** Projektstruktur, API-Vertrag, Frontend-Stub

- [x] Verzeichnisstruktur anlegen
- [x] Pydantic-Schemas definieren
- [x] FastAPI-Scaffolding mit Mock-Endpunkt
- [x] Frontend-Stub mit Datei-Upload
- [x] Docker-Konfiguration

### Sprint 2: CleanDocs v2 Pipeline

**Ziel:** Vollstaendige Browser-seitige PDF-Verarbeitung

- [ ] pdf.js Integration und PDF-Parsing
- [ ] Strukturerkennung (Ueberschriften, Absaetze, Tabellen)
- [ ] Boilerplate-Entfernung (Header/Footer-Erkennung)
- [ ] TextRank-Implementierung (Satz-Relevanz)
- [ ] SimHash-Deduplizierung
- [ ] Markdown-Generator
- [ ] Metriken-Berechnung und Anzeige
- [ ] Fortschrittsanzeige waehrend der Verarbeitung

### Sprint 3: Storage Layer & Chunking

**Ziel:** Persistenz und Dokumenten-Chunking

- [ ] SQLite-Schema anlegen und Migrationen
- [ ] Dokument-CRUD in SQLite
- [ ] Semantisches Chunking (Markdown-Ueberschriften-basiert)
- [ ] Token-Zaehlung pro Chunk
- [ ] LanceDB-Tabelle fuer Embeddings anlegen
- [ ] Lokales Embedding-Modell integrieren (sentence-transformers)
- [ ] Chunks mit Embeddings in LanceDB speichern
- [ ] Dokument-Status-Management (pending -> processing -> completed/error)

### Sprint 4: RAG-Pipeline

**Ziel:** Retrieval-Augmented Generation mit SSE-Streaming

- [ ] Vektor-Suche in LanceDB implementieren
- [ ] Re-Ranking der Ergebnisse
- [ ] Ollama/llama.cpp Anbindung
- [ ] Prompt-Template fuer RAG-Antworten (Deutsch/Englisch)
- [ ] SSE-Streaming fuer Token-Ausgabe
- [ ] Quellen-Anzeige im Frontend
- [ ] Konversations-Historie (optional, in-memory)

### Sprint 5: Wissensgraph

**Ziel:** Entitaeten-Extraktion und Graph-Abfragen

- [ ] NER mittels LLM (lokale Extraktion)
- [ ] Kuzu-Schema anlegen
- [ ] Entitaeten und Relationen speichern
- [ ] Graph-Traversal-API
- [ ] Graph-Kontext in RAG-Antworten integrieren
- [ ] Graph-Visualisierung im Frontend (Canvas/SVG)

### Sprint 6: UI & Polish

**Ziel:** Vollstaendige Benutzeroberflaeche

- [ ] Dokumenten-Uebersicht (Liste mit Status)
- [ ] Dokumenten-Detailansicht (Chunks, Entitaeten)
- [ ] Chat-Interface fuer RAG-Abfragen
- [ ] Graph-Explorer (interaktiv)
- [ ] Dark/Light-Theme
- [ ] Responsive Design
- [ ] Fehlerbehandlung und Benutzerhinweise
- [ ] Tastaturnavigation und Barrierefreiheit

---

## 10. Verzeichnisstruktur

```
/AAkte
  ├── SPEC.md                         # Diese Spezifikation
  ├── README.md                       # Projekt-Uebersicht und Setup
  ├── .gitignore
  ├── Dockerfile
  ├── docker-compose.yml
  ├── requirements.txt                # Python-Abhaengigkeiten
  │
  ├── /backend
  │   └── /app
  │       ├── __init__.py
  │       ├── main.py                 # FastAPI-Einstiegspunkt
  │       ├── config.py               # Konfiguration aus Umgebungsvariablen
  │       ├── /api
  │       │   ├── __init__.py
  │       │   └── endpoints.py        # API-Routen
  │       ├── /models
  │       │   ├── __init__.py
  │       │   ├── schemas.py          # Pydantic-Schemas (Request/Response)
  │       │   └── db_models.py        # Datenbank-Modelle
  │       └── /services
  │           ├── __init__.py
  │           ├── ingestion_service.py # Dokument-Verarbeitungspipeline
  │           ├── rag_service.py       # RAG-Abfrage-Logik (Sprint 4)
  │           └── graph_service.py     # Graph-Operationen (Sprint 5)
  │
  ├── /frontend
  │   ├── index.html                  # Haupt-HTML
  │   ├── style.css                   # Globale Styles
  │   ├── app.js                      # Hauptanwendungs-Logik
  │   └── cleandocs_pipeline.js       # CleanDocs v2 Pipeline
  │
  └── /data                           # Laufzeitdaten (in .gitignore)
      ├── aakte.db                    # SQLite-Datenbank
      ├── /lancedb                    # LanceDB-Verzeichnis
      └── /kuzu                       # Kuzu-Graph-Datenbank
```

---

## 11. Fehlerbehandlung

### 11.1 API-Fehlerformat

Alle Fehler werden als JSON zurueckgegeben:

```json
{
  "error": {
    "code": "DOCUMENT_TOO_LARGE",
    "message": "Document exceeds maximum size of 50 MB",
    "details": {
      "max_size_mb": 50,
      "actual_size_mb": 72.3
    }
  }
}
```

### 11.2 Fehlercodes

| Code                    | HTTP-Status | Beschreibung                         |
|-------------------------|-------------|--------------------------------------|
| `TENANT_NOT_FOUND`      | 404         | Tenant existiert nicht               |
| `DOCUMENT_NOT_FOUND`    | 404         | Dokument existiert nicht             |
| `DOCUMENT_TOO_LARGE`    | 413         | Dokument ueberschreitet Max-Groesse  |
| `INVALID_MARKDOWN`      | 422         | Markdown-Inhalt ungueltig/leer       |
| `PROCESSING_FAILED`     | 500         | Fehler bei der Verarbeitung          |
| `LLM_UNAVAILABLE`       | 503         | Lokales LLM nicht erreichbar         |

---

## 12. Beziehung zu 8man

Die Agentische Akte ist als Schwester-Projekt zu **8man** (Expertenrat-Simulator) konzipiert.
In einer zukuenftigen Integration koennen Dokumente aus der Agentischen Akte
als Kontext fuer 8man-Beratungen verwendet werden:

```
Dokument-Upload --> AAkte (Analyse, RAG, Graph)
                        │
                        └──> 8man (Expertenrat-Beratung mit Dokumenten-Kontext)
```

Diese Integration ist nicht Teil der aktuellen Spezifikation.
