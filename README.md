# Engineering Document Intelligence & CAD Knowledge Copilot

A production-grade intelligent copilot platform designed for engineering teams to parse, index, search, and reason over complex engineering documents (specifications, BOMs, standards, datasheets) and CAD models/metadata.

> **Project Status (Milestone 3 - Document Intelligence & OCR Pipeline)**:
> Fully operational document intelligence pipeline capable of processing engineering PDFs page-by-page. Extracts selectable digital text with **PyMuPDF**, detects scanned/image-only pages via configurable heuristics, applies **OpenCV** image preprocessing (grayscale, denoising, Otsu thresholding), and performs **Tesseract OCR** fallback. Page records (`DocumentPage`) are stored in PostgreSQL with 1-based page numbering, extraction statistics (character and word counts), and processing status tracking.
> *Note: Embeddings, vector search, Azure AI Search, and LangGraph agents are scheduled for subsequent milestones.*

---

## 🏗️ Architecture & Tech Stack

- **Backend**: Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) (Async 2.x), [asyncpg](https://magicstack.github.io/asyncpg/), [Alembic](https://alembic.sqlalchemy.org/)
- **Document Intelligence & OCR**:
  - **PyMuPDF (`fitz`)**: Primary high-performance PDF validation, structure analysis, and native text extraction.
  - **OpenCV (`cv2`)**: Image preprocessing for scanned pages (grayscale conversion, Gaussian noise filtering, Otsu binarization).
  - **Tesseract OCR (`pytesseract`)**: Optical Character Recognition engine for scanned pages and drawing title blocks.
  - **Pillow (`PIL`)**: High-resolution page rendering and image handling.
- **Database**: PostgreSQL 16 (Local Windows setup at `C:\Users\admin\pgsql`; Docker Compose optional)
- **Frontend**: [React 18](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vitejs.dev/)
- **Configuration & Validation**: [Pydantic v2](https://docs.pydantic.dev/) and `pydantic-settings`
- **Testing**: [pytest](https://pytest.org/), `pytest-asyncio`, `aiosqlite` (24 hermetic automated tests)
- **Future Integrations (Configuration-Ready)**:
  - Orchestration: [LangGraph](https://python.langchain.com/docs/langgraph) / LangChain
  - LLM & Embeddings: Azure OpenAI (`gpt-4o`, `text-embedding-3-large`)
  - Hybrid Search: Azure AI Search

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
│   │   │   └── 20261005_8404a163fb1e_add_document_pages.py
│   │   └── env.py             # Async Alembic runner
│   ├── app/
│   │   ├── api/v1/            # Versioned API routes (health, documents, cad, chat)
│   │   ├── core/              # Config (Pydantic Settings), DB session, logging
│   │   ├── models/            # SQLAlchemy 2.0 ORM models (Document, DocumentPage, etc.)
│   │   ├── schemas/           # Pydantic v2 validation and serialization schemas
│   │   ├── services/          # Business logic layer
│   │   │   ├── document_service.py
│   │   │   └── document_processing/  # Milestone 3 Document Intelligence Pipeline
│   │   │       ├── pdf_extractor.py  # PyMuPDF validation and text extraction
│   │   │       ├── ocr.py            # OpenCV preprocessing & Tesseract runner
│   │   │       └── processor.py      # Page-by-page pipeline & OCR heuristic
│   │   ├── agents/            # LangGraph agent stubs (for future milestone)
│   │   └── integrations/      # Azure OpenAI & AI Search connectors (optional)
│   ├── tests/                 # Hermetic automated test suite (24 pytest tests)
│   ├── Dockerfile             # Container definition for backend
│   ├── pyproject.toml         # Python packaging and pytest configuration
│   └── requirements.txt       # Production & development dependencies
├── frontend/                  # React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── components/        # Layout, Common, Documents, CAD, Chat
│   │   ├── services/          # Typed API client services
│   │   └── types/             # Domain TypeScript interfaces
│   ├── package.json           # Frontend dependencies
│   └── vite.config.ts         # Vite build configuration
├── data/                      # Local data storage directories
│   ├── documents/             # Staged engineering PDFs (data/documents/{id}/{filename})
│   └── processed/             # Extracted artifacts and temporary files
├── scripts/                   # Automation and operational scripts
│   ├── init_db.py             # Database migration executor (alembic upgrade head)
│   ├── seed_data.py           # Sample engineering document seeder
│   └── ingest_cad_docs.py     # PDF ingestion CLI tool with progress & OCR reporting
└── docker/                    # Docker Compose orchestration
    ├── docker-compose.yml     # Multi-container stack (DB, Backend, Frontend)
    └── docker-compose.dev.yml # Dedicated PostgreSQL service for local development
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

## 🛠️ CLI Ingestion Tool

Ingest a single engineering PDF:
```powershell
python scripts/ingest_cad_docs.py data/sample_pump_spec.pdf --document-type "SPECIFICATION" --part-number "CFP-402" --revision "D"
```

Ingest an entire directory of PDFs:
```powershell
python scripts/ingest_cad_docs.py --source-dir data/documents/
```

Example Output:
```text
============================================================
  DOCUMENT INGESTION REPORT
============================================================
  Document ID      : 46eae343-d144-4d26-9cd1-651c992fc836
  Filename         : sample_pump_spec.pdf
  Document Type    : SPECIFICATION
  Part Number      : CFP-402
  Revision         : D
  Total Pages      : 3
  Processed Pages  : 3
  Native Text Pages: 2
  OCR Pages        : 1
  Final Status     : DocumentStatus.PROCESSED
============================================================
```

---

## 📡 Milestone 3 API Reference

### 1. Upload & Process PDF
`POST /api/v1/documents/upload` (multipart/form-data)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/documents/upload" \
  -F "file=@data/sample_pump_spec.pdf" \
  -F "document_type=SPECIFICATION" \
  -F "part_number=CFP-402-316L" \
  -F "revision=D"
```
Response:
```json
{
  "success": true,
  "message": "Document uploaded and processed successfully.",
  "data": {
    "document_id": "95ba61ff-d218-4eb7-8d53-f5318f9f1da1",
    "filename": "sample_pump_spec.pdf",
    "status": "PROCESSED",
    "page_count": 3,
    "processed_page_count": 3,
    "ocr_page_count": 1
  }
}
```

### 2. List Extracted Pages
`GET /api/v1/documents/{document_id}/pages?page=1&page_size=50`
```bash
curl "http://127.0.0.1:8000/api/v1/documents/95ba61ff-d218-4eb7-8d53-f5318f9f1da1/pages"
```
Response:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "page_number": 1,
        "extraction_method": "text",
        "ocr_used": false,
        "character_count": 1117,
        "word_count": 179,
        "text": "CENTRIFUGAL CHEMICAL FEED PUMP - TECHNICAL SPECIFICATION..."
      },
      {
        "page_number": 3,
        "extraction_method": "ocr",
        "ocr_used": true,
        "character_count": 268,
        "word_count": 35,
        "text": "QUALITY CONTROL INSPECTION & HYDROSTATIC TEST SIGN-OFF..."
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 50,
    "total_pages": 1
  }
}
```

### 3. Retrieve Individual Page Content
`GET /api/v1/documents/{document_id}/pages/{page_number}` (1-indexed)
```bash
curl "http://127.0.0.1:8000/api/v1/documents/95ba61ff-d218-4eb7-8d53-f5318f9f1da1/pages/1"
```
