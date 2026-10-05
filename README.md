# Engineering Document Intelligence & CAD Knowledge Copilot

A production-grade intelligent copilot platform designed for engineering teams to parse, index, search, and reason over complex engineering documents (specifications, BOMs, standards, datasheets) and CAD models/metadata.

> **Project Status (Milestone 4 - Document Chunking & Hybrid Vector Indexing)**:
> Fully operational structural document chunking, dense vector embeddings, and hybrid retrieval engine. Features context-preserving chunking tailored for engineering texts (protects units, tolerances, part numbers, and numbered sections), a dual embedding architecture (deterministic 1536-dimensional offline mock and Azure OpenAI `text-embedding-3-large`), and a hybrid search engine combining **BM25 lexical retrieval** and **vector cosine similarity** via **Reciprocal Rank Fusion (RRF)** with metadata filtering. Chunks and embeddings are stored in PostgreSQL (`document_chunks` table) and indexed into hybrid search.

---

## 🏗️ Architecture & Tech Stack

- **Backend**: Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) (Async 2.x), [asyncpg](https://magicstack.github.io/asyncpg/), [Alembic](https://alembic.sqlalchemy.org/)
- **Document Intelligence & OCR**:
  - **PyMuPDF (`fitz`)**: Primary high-performance PDF validation, structure analysis, and native text extraction.
  - **OpenCV (`cv2`)**: Image preprocessing for scanned pages (grayscale conversion, Gaussian noise filtering, Otsu binarization).
  - **Tesseract OCR (`pytesseract`)**: Optical Character Recognition engine for scanned pages and drawing title blocks.
  - **Pillow (`PIL`)**: High-resolution page rendering and image handling.
- **Chunking & Hybrid Search Engine (Milestone 4)**:
  - **Engineering Text Chunker**: Structural chunking preserving engineering units, tolerances, part numbers, and page provenance.
  - **Embedding Providers**: Abstract provider pattern with deterministic offline `LocalMockEmbeddingProvider` (unit-normalized 1536-dim vectors) and production `AzureOpenAIEmbeddingProvider`.
  - **Search Indices**: Abstract `BaseSearchIndex` with in-process `LocalSearchIndex` (BM25 + Cosine Vector + RRF) and `AzureSearchIndex` for Azure AI Search.
- **Database**: PostgreSQL 16 (Local Windows setup at `C:\Users\admin\pgsql`; Docker Compose optional)
- **Frontend**: [React 18](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vitejs.dev/)
- **Configuration & Validation**: [Pydantic v2](https://docs.pydantic.dev/) and `pydantic-settings`
- **Testing**: [pytest](https://pytest.org/), `pytest-asyncio`, `aiosqlite` (41 hermetic automated tests)
- **Future Integrations (Configuration-Ready)**:
  - Orchestration: [LangGraph](https://python.langchain.com/docs/langgraph) / LangChain (Milestone 5)
  - LLM: Azure OpenAI (`gpt-4o`) (Milestone 5)

For an in-depth architectural breakdown and sequence diagrams, refer to [`architecture.md`](./architecture.md).

---

## 📁 Repository Structure

```text
├── .env.example              # Environment variables template with safe placeholders
├── .gitignore                 # Excludes .env, virtualenvs, caches, raw uploads
├── README.md                  # Project overview and reproduction guide
├── architecture.md            # System architecture and data flow blueprint
├── backend/                   # FastAPI application & database migrations
│   ├── alembic/               # Alembic database migration scripts & versions
│   │   ├── versions/          # Version-controlled migration files
│   │   │   ├── 20261005_1bd975fa9757_initial_schema.py
│   │   │   ├── 20261005_8404a163fb1e_add_document_pages.py
│   │   │   └── 20261005_e77ce6df94e3_add_document_chunks.py
│   │   └── env.py             # Async Alembic runner
│   ├── app/
│   │   ├── api/v1/            # Versioned API routes (health, documents, search, cad, chat)
│   │   ├── core/              # Config (Pydantic Settings), DB session, logging
│   │   ├── models/            # SQLAlchemy ORM models (Document, DocumentPage, DocumentChunk)
│   │   ├── schemas/           # Pydantic v2 schemas (document, chunk, common)
│   │   ├── services/          # Business logic layer
│   │   │   ├── document_service.py
│   │   │   ├── search_service.py   # Hybrid retrieval & query orchestration
│   │   │   ├── chunking/           # Structural engineering chunker
│   │   │   ├── embeddings/         # Embedding providers (LocalMock, Azure OpenAI)
│   │   │   ├── search/             # Hybrid search indices (LocalIndex, AzureSearchIndex)
│   │   │   └── document_processing/# PyMuPDF text extractor & OCR pipeline
│   │   ├── agents/            # LangGraph agent stubs (for future milestone)
│   │   └── integrations/      # Azure connectors (optional)
│   ├── tests/                 # Hermetic automated test suite (41 pytest tests)
│   ├── Dockerfile             # Container definition for backend
│   ├── pyproject.toml         # Python packaging and pytest configuration
│   └── requirements.txt       # Production & development dependencies
├── frontend/                  # React + TypeScript + Vite SPA
├── data/                      # Local data storage directories
│   ├── documents/             # Staged engineering PDFs (data/documents/{id}/{filename})
│   └── processed/             # Extracted artifacts and temporary files
├── scripts/                   # Automation and operational scripts
│   ├── init_db.py             # Database migration executor (alembic upgrade head)
│   ├── seed_data.py           # Sample engineering document seeder
│   ├── ingest_cad_docs.py     # Ingestion & chunking CLI with progress reporting
│   └── search_docs.py         # Keyword, vector, and hybrid search CLI
└── docker/                    # Docker Compose orchestration
```

---

## 🔍 Tesseract OCR Configuration (Windows & Linux)

Tesseract OCR is supported with automatic discovery:
1. **Configured setting**: Looks at `TESSERACT_CMD` in `.env` if provided.
2. **System PATH**: Searches for `tesseract` on PATH via `shutil.which`.
3. **Standard Windows paths fallback**: Checks `C:\Program Files\Tesseract-OCR\tesseract.exe`.

### Verification on Windows
In PowerShell:
```powershell
where.exe tesseract
# Output e.g.: C:\Program Files\Tesseract-OCR\tesseract.exe

tesseract --version
# Output: tesseract v5.x
```

If Tesseract is installed outside PATH, set in `.env`:
```ini
TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"
```
*(Note: If Tesseract is not installed, digital-text PDFs continue to process normally. When an image-only page requires OCR, a clear 503 error is returned without crashing the server).*

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

Key configuration variables:
```ini
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/engineering_copilot

# Document Storage & Ingestion Limits
DOCUMENTS_STORAGE_DIR=./data/documents
PROCESSED_STORAGE_DIR=./data/processed
MAX_UPLOAD_SIZE_MB=50
MAX_PDF_PAGES=500
PDF_MIN_NATIVE_TEXT_CHARS=50
OCR_DPI=300

# Optional Tesseract path
TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

## 🚀 Local Development Setup

### 1. Database & Migrations

#### Default: Local Windows PostgreSQL (Installed at `C:\Users\admin\pgsql`)

Start the local PostgreSQL server on port `5432` (run in background or in a separate terminal):
```powershell
& "C:\Users\admin\pgsql\bin\postgres.exe" -D "C:\Users\admin\pgsql\data"
```

If initializing for the first time, create the `engineering_copilot` database:
```powershell
$env:PGPASSWORD = "postgres"
& "C:\Users\admin\pgsql\bin\createdb.exe" -U postgres -h localhost engineering_copilot
```

#### Optional: Docker Compose (Alternative / Containerized Workflow)
If running inside a containerized Docker environment instead of the local Windows PostgreSQL installation:
```powershell
docker compose -f docker/docker-compose.dev.yml up db -d
```

#### Apply Database Migrations (Alembic)
With PostgreSQL running on port `5432`:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Verify migration status and bidirectional rollback:
```powershell
alembic downgrade -1
alembic upgrade head
```

### 2. Run Automated Test Suite

The test suite runs hermetically using in-memory SQLite (`aiosqlite`) and does not alter your PostgreSQL database:
```powershell
# From backend/ directory
pytest tests/ -v
```

Expected output:
```text
tests/test_document_processing.py::test_pdf_validation_success PASSED
tests/test_document_processing.py::test_pdf_validation_empty_file PASSED
tests/test_document_processing.py::test_pdf_validation_invalid_header PASSED
tests/test_document_processing.py::test_pdf_validation_corrupted_structure PASSED
tests/test_document_processing.py::test_text_normalization_preserves_engineering_notation PASSED
tests/test_document_processing.py::test_native_text_sufficiency_heuristic PASSED
tests/test_document_processing.py::test_process_text_pdf_page_by_page PASSED
tests/test_document_processing.py::test_opencv_preprocessing PASSED
tests/test_document_processing.py::test_tesseract_discovery PASSED
tests/test_document_processing.py::test_ocr_processing_fallback_on_scanned_pdf PASSED
tests/test_documents.py::test_create_document_metadata_success PASSED
tests/test_documents.py::test_get_document_by_id_success PASSED
tests/test_documents.py::test_get_document_not_found PASSED
tests/test_documents.py::test_list_documents_pagination_and_filter PASSED
tests/test_documents.py::test_create_document_validation_failure PASSED
tests/test_documents.py::test_upload_document_pdf_success PASSED
tests/test_documents.py::test_get_document_single_page PASSED
tests/test_documents.py::test_upload_invalid_file_extension PASSED
tests/test_documents.py::test_upload_empty_pdf_file PASSED
tests/test_documents.py::test_upload_invalid_pdf_header PASSED
tests/test_health.py::test_health_endpoint PASSED
tests/test_health.py::test_readiness_endpoint_connected PASSED
tests/test_health.py::test_readiness_endpoint_db_failure PASSED
tests/test_health.py::test_swagger_docs_accessible PASSED
============================= 24 passed in 5.14s =============================
```

### 3. Start FastAPI Server

```powershell
# From backend/ directory
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify service status:
- Health check: `http://127.0.0.1:8000/api/v1/health`
- Readiness check (DB connected): `http://127.0.0.1:8000/api/v1/health/ready`
- Swagger UI docs: `http://127.0.0.1:8000/docs`

---

## 📄 Document Intelligence Workflow & Storage

### Storage Layout & Security
Uploaded PDFs are saved to:
```text
data/documents/{document_id}/{sanitized_filename}
```
- Filenames are sanitized using path basename isolation to prevent directory traversal (`../../`).
- Absolute filesystem paths are never exposed in API responses or errors.

### OCR Fallback Heuristic
1. Every page is first inspected natively using PyMuPDF.
2. Printable non-whitespace characters are counted.
3. If non-whitespace characters >= `PDF_MIN_NATIVE_TEXT_CHARS` (default: 50):
   - Page is marked `extraction_method: "text"`, `ocr_used: false`.
4. If non-whitespace characters < `PDF_MIN_NATIVE_TEXT_CHARS`:
   - Page is identified as scanned / diagram-heavy.
   - Rendered to high-resolution image (300 DPI).
   - Preprocessed with OpenCV (grayscale, Gaussian noise filter, Otsu binarization).
   - OCR is executed via Tesseract.
   - Page is marked `extraction_method: "ocr"`, `ocr_used: true`.

---

---

## 🛠️ CLI Ingestion & Search Tools

### Ingest and Index Engineering PDFs
Ingest a single engineering PDF with automatic structural chunking and vector indexing:
```powershell
python scripts/ingest_cad_docs.py data/sample_pump_spec.pdf --document-type "SPECIFICATION" --part-number "CFP-402-316L" --revision "D"
```

Ingest without chunking:
```powershell
python scripts/ingest_cad_docs.py data/sample_pump_spec.pdf --no-chunk
```

Ingest an entire directory of PDFs:
```powershell
python scripts/ingest_cad_docs.py --source-dir data/documents/
```

Example Output:
```text
============================================================
  DOCUMENT INGESTION & INDEXING REPORT
============================================================
  Document ID       : 51826aca-8497-47b5-939b-edc76c0a522e
  Filename          : sample_pump_spec.pdf
  Document Type     : SPECIFICATION
  Part Number       : CFP-402-316L
  Revision          : D
  Total Pages       : 3
  Processed Pages   : 3
  Native Text Pages : 2
  OCR Pages         : 1
  Document Status   : DocumentStatus.PROCESSED
  Chunks Created    : 5
  Embeddings Made   : 5
  Indexed into Search: 5
  Indexing Status   : completed
============================================================
```

### Search Engineering Chunks via CLI
Query engineering specifications using keyword, vector, or hybrid retrieval:

1. **Hybrid Retrieval (RRF default)**:
```powershell
python scripts/search_docs.py "bearing journal tolerance ISO h6" --mode hybrid
```

2. **Exact Keyword Match**:
```powershell
python scripts/search_docs.py "CFP-402-316L" --mode keyword
```

3. **Dense Vector Search**:
```powershell
python scripts/search_docs.py "maximum discharge pressure and operating temperature" --mode vector
```

4. **Filtered Search**:
```powershell
python scripts/search_docs.py "torque" --mode hybrid --part-number "CFP-402-316L"
```

Example Search Output:
```text
======================================================================
  SEARCH QUERY : 'bearing journal tolerance ISO h6'
  MODE         : HYBRID
  TOTAL HITS   : 5
======================================================================

  [Hit 1] Score: 0.0328 | Mode: hybrid
  Document    : sample_pump_spec.pdf (ID: 51826aca-8497-47b5-939b-edc76c0a522e)
  Location    : Page 2, Chunk #2
  Part Number : CFP-402-316L
  Revision    : D
  Section     : CFP-402 MECHANICAL CLEARANCES & ASSEMBLY SPECIFICATIONS
  Snippet     :
    CFP-402 MECHANICAL CLEARANCES & ASSEMBLY SPECIFICATIONS
    4. RUNNING CLEARANCES & TOLERANCES
    - Impeller front wear ring clearance: 0.25 mm to 0.35 mm (Diametral)
    - Impeller back wear ring clearance: 0.30 mm to 0.40 mm
    - Maximum shaft runout at mechanical seal face: < 0.025 mm TIR
    - Radial bearing journal tolerance: ISO h6 (-0.000 / -0.016 mm)
======================================================================
```

---

## 📡 API Reference

### 1. Document Ingestion & Page Extraction (Milestone 3)

#### Upload & Process PDF
`POST /api/v1/documents/upload` (multipart/form-data)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/documents/upload" \
  -F "file=@data/sample_pump_spec.pdf" \
  -F "document_type=SPECIFICATION" \
  -F "part_number=CFP-402-316L" \
  -F "revision=D"
```

#### List Extracted Pages
`GET /api/v1/documents/{document_id}/pages?page=1&page_size=50`

#### Retrieve Individual Page Content
`GET /api/v1/documents/{document_id}/pages/{page_number}` (1-indexed)

---

### 2. Chunking & Hybrid Search (Milestone 4)

#### Generate Structural Chunks & Embeddings
`POST /api/v1/documents/{document_id}/chunks/generate`
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/documents/{document_id}/chunks/generate"
```
Response:
```json
{
  "success": true,
  "message": "Generated 5 chunks for 'sample_pump_spec.pdf'.",
  "data": {
    "document_id": "74112557-78b9-497d-83c5-8a323bd3cad0",
    "filename": "sample_pump_spec.pdf",
    "chunks_created": 5,
    "embeddings_generated": 5,
    "indexed_count": 5,
    "status": "completed"
  }
}
```

#### List Document Chunks
`GET /api/v1/documents/{document_id}/chunks?page=1&page_size=20`
```bash
curl "http://127.0.0.1:8000/api/v1/documents/{document_id}/chunks"
```

#### Retrieve Individual Chunk
`GET /api/v1/documents/{document_id}/chunks/{chunk_id}`

#### Hybrid Search Across Chunks
`POST /api/v1/search`
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "bearing journal tolerance ISO h6",
    "top_k": 5,
    "mode": "hybrid",
    "filters": {
      "part_number": "CFP-402-316L"
    }
  }'
```
Response:
```json
{
  "success": true,
  "message": "Found 5 matching chunks via hybrid search.",
  "data": {
    "query": "bearing journal tolerance ISO h6",
    "mode": "hybrid",
    "total_results": 5,
    "results": [
      {
        "chunk_id": "9256b640-7d0c-4ad3-9346-be000955c29d",
        "document_id": "51826aca-8497-47b5-939b-edc76c0a522e",
        "page_id": "ab60f743-a388-4423-b486-c2e6bfc4aa7d",
        "page_number": 2,
        "chunk_index": 2,
        "filename": "sample_pump_spec.pdf",
        "document_type": "SPECIFICATION",
        "part_number": "CFP-402-316L",
        "revision": "D",
        "content": "CFP-402 MECHANICAL CLEARANCES & ASSEMBLY SPECIFICATIONS\n4. RUNNING CLEARANCES & TOLERANCES\n- Impeller front wear ring clearance: 0.25 mm to 0.35 mm (Diametral)...",
        "score": 0.0328,
        "retrieval_mode": "hybrid",
        "metadata": {
          "section": "CFP-402 MECHANICAL CLEARANCES & ASSEMBLY SPECIFICATIONS"
        }
      }
    ]
  }
}
```

