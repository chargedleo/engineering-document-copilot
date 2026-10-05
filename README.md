# Engineering Document Intelligence & CAD Knowledge Copilot

A production-grade intelligent copilot platform designed for engineering teams to parse, index, search, and reason over complex engineering documents (specifications, BOMs, standards, datasheets) and CAD models/metadata.

> **Project Status (Milestone 6 - LangGraph Engineering Copilot Agent)**:
> Fully operational autonomous agent orchestration layer built on LangGraph. Features genuine multi-tool engineering decision making (`search_engineering_documents`, `get_document_metadata`, `calculate_engineering`), deterministic rule-based planning, dynamic parameter extraction and value chaining from retrieved chunks to downstream calculations, prompt injection defense with passive XML data isolation, standardized abstention, a dedicated REST API (`POST /api/v1/agent/query`), an interactive CLI demonstration (`scripts/query_agent.py`), and 77 passing automated tests.

---

## 🏗️ Architecture & Tech Stack

- **Backend**: Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) (Async 2.x), [asyncpg](https://magicstack.github.io/asyncpg/), [Alembic](https://alembic.sqlalchemy.org/)
- **Document Intelligence & OCR (Milestone 3)**:
  - **PyMuPDF (`fitz`)**: High-performance PDF validation, structure analysis, and native text extraction.
  - **OpenCV (`cv2`)**: Image preprocessing for scanned pages (grayscale, Gaussian denoise, Otsu thresholding).
  - **Tesseract OCR (`pytesseract`)**: Optical Character Recognition engine for scanned pages and drawing title blocks.
  - **Pillow (`PIL`)**: High-resolution page rendering and image handling.
- **Chunking & Hybrid Search Engine (Milestone 4)**:
  - **Engineering Text Chunker**: Structural chunking preserving engineering units, tolerances, part numbers, and page provenance.
  - **Embedding Providers**: Abstract provider pattern with deterministic offline `LocalMockEmbeddingProvider` (unit-normalized 1536-dim vectors) and production `AzureOpenAIEmbeddingProvider`.
  - **Search Indices**: Abstract `BaseSearchIndex` with in-process `LocalSearchIndex` (BM25 + Cosine Vector + RRF) and `AzureSearchIndex` for Azure AI Search.
- **Grounded Retrieval-Augmented Generation (Milestone 5)**:
  - **LLM Providers**: Abstract `BaseLLMProvider` pattern with deterministic offline `LocalMockChatProvider` (grounded synthesis, unit preservation, citation tag generation) and production `AzureOpenAIChatProvider` (Azure OpenAI REST API).
  - **Context Assembly**: `ContextBuilder` structuring candidate hits above relevance threshold into `<engineering_context>` evidence blocks with `[C1]`, `[C2]` citation tracking.
  - **Untrusted Context Boundary**: Strict passive data isolation preventing prompt injections embedded in PDF files from hijacking LLM instructions.
  - **Standardized Abstention**: Explicit sufficiency check returning `"The available documents do not contain enough information to answer this question."` when evidence is missing.
- **Agentic Copilot & Tool Orchestration (Milestone 6)**:
  - **LangGraph**: `StateGraph` workflow (`classify_and_plan` -> `execute_tools` -> `synthesize_answer`) with typed state (`CopilotAgentState`), conditional execution, and dependency injection of `AsyncSession` via `RunnableConfig`.
  - **Engineering Tool Suite**:
    - `search_engineering_documents`: Wrapped M4 hybrid search engine with part number and revision filtering.
    - `get_document_metadata`: Database metadata querying for revision, page counts, processing status, and timestamps.
    - `calculate_engineering`: Isolated, unit-safe engineering calculations (bar/psi, Celsius/Fahrenheit, m³/h / LPM, kW/HP, percentage change) without arbitrary code execution.
  - **Dynamic Multi-Tool Chaining**: Resolves engineering values from retrieved PDF chunks into subsequent calculation tools while preserving chunk-level citation links (`[C1]`).
  - **Prompt-Injection Defense**: Untrusted text isolation inside structured `<engineering_context>` XML tags.
  - **Standardized Abstention**: Detects insufficient context and responds with canonical engineering abstention.
- **Database**: PostgreSQL 16 (Local Windows setup at `C:\Users\admin\pgsql`; Docker Compose optional)
- **Frontend**: [React 18](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vitejs.dev/)
- **Configuration & Validation**: [Pydantic v2](https://docs.pydantic.dev/) and `pydantic-settings`
- **Testing**: [pytest](https://pytest.org/), `pytest-asyncio`, `aiosqlite` (77 hermetic automated tests)
- **Cloud Integrations (Configuration-Ready)**:
  - *Note on Azure*: Azure OpenAI and Azure AI Search remain configuration-ready adapter options (`AZURE_OPENAI_API_KEY`, `AZURE_SEARCH_ENDPOINT`). In local development and testing, the system runs completely hermetic with offline deterministic providers (`LocalMockChatProvider`, `LocalMockEmbeddingProvider`, `LocalSearchIndex`). Azure OpenAI remains an adapter/configuration option and is not considered live-tested unless credentials and deployment were actually used.
- **Future Milestone Roadmap**:
  - CAD Geometry: STEP / DXF geometry parsing and 3D visual navigation (Milestone 7)

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
│   │   ├── api/v1/            # Versioned API routes (health, documents, search, rag, agent, cad, chat)
│   │   │   ├── endpoints/     # Route handlers (agent.py, rag.py, search.py, documents.py)
│   │   │   └── router.py      # Aggregated API router
│   │   ├── core/              # Config (Pydantic Settings), DB session, logging
│   │   ├── models/            # SQLAlchemy ORM models (Document, DocumentPage, DocumentChunk)
│   │   ├── schemas/           # Pydantic v2 schemas (document, chunk, rag, agent, common)
│   │   ├── services/          # Business logic layer
│   │   │   ├── document_service.py
│   │   │   ├── search_service.py   # Hybrid retrieval & query orchestration
│   │   │   ├── rag_service.py      # Grounded RAG synthesis & citation engine
│   │   │   ├── agent_service.py    # LangGraph agent orchestration service
│   │   │   ├── chunking/           # Structural engineering chunker
│   │   │   ├── embeddings/         # Embedding providers (LocalMock, Azure OpenAI)
│   │   │   ├── search/             # Hybrid search indices (LocalIndex, AzureSearchIndex)
│   │   │   ├── llm/                # LLM providers (LocalMock, Azure OpenAI REST)
│   │   │   ├── rag/                # Context builder & prompt engineering
│   │   │   └── document_processing/# PyMuPDF text extractor & OCR pipeline
│   │   ├── agents/            # LangGraph agent orchestration (Milestone 6)
│   │   │   ├── tools/         # Engineering tools (search, metadata, calculator)
│   │   │   ├── graph.py       # Compiled StateGraph workflow
│   │   │   ├── nodes.py       # State transition nodes (plan, execute, synthesize)
│   │   │   ├── planner.py     # Deterministic query planner & tool router
│   │   │   └── state.py       # Typed CopilotAgentState & ToolCall/Result models
│   │   └── integrations/      # Azure connectors (optional)
│   ├── tests/                 # Hermetic automated test suite (77 pytest tests)
│   │   ├── test_agent.py      # LangGraph agent & multi-tool test suite (21 tests)
│   │   ├── test_rag.py        # Grounded RAG & prompt injection test suite (15 tests)
│   │   ├── test_search.py     # Hybrid retrieval test suite (11 tests)
│   │   ├── test_chunking.py   # Engineering chunker tests (6 tests)
│   │   ├── test_document_processing.py # PDF & OCR processing tests (10 tests)
│   │   ├── test_documents.py  # Document CRUD & upload tests (10 tests)
│   │   └── test_health.py     # Health & readiness tests (4 tests)
│   ├── Dockerfile             # Container definition for backend
│   ├── pyproject.toml         # Python packaging and pytest configuration
│   └── requirements.txt       # Production & development dependencies (including langgraph)
├── frontend/                  # React + TypeScript + Vite SPA
├── data/                      # Local data storage directories
│   ├── documents/             # Staged engineering PDFs (data/documents/{id}/{filename})
│   └── processed/             # Extracted artifacts and temporary files
├── scripts/                   # Automation and operational scripts
│   ├── init_db.py             # Database migration executor (alembic upgrade head)
│   ├── seed_data.py           # Sample engineering document seeder
│   ├── ingest_cad_docs.py     # Ingestion & chunking CLI with progress reporting
│   ├── search_docs.py         # Keyword, vector, and hybrid search CLI
│   ├── query_rag.py           # Grounded RAG question-answering CLI with citations
│   └── query_agent.py         # LangGraph engineering copilot agent CLI
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
.\.venv\Scripts\pytest.exe tests/ -v
```

Expected output:
```text
tests/test_agent.py (21 tests) .....................                     PASSED
tests/test_chunking.py (6 tests) ......                                  PASSED
tests/test_document_processing.py (10 tests) ..........                  PASSED
tests/test_documents.py (10 tests) ..........                            PASSED
tests/test_health.py (4 tests) ....                                      PASSED
tests/test_rag.py (15 tests) ...............                             PASSED
tests/test_search.py (11 tests) ...........                              PASSED

============================= 77 passed in 7.14s =============================
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

### Grounded Engineering Q&A via RAG CLI (Milestone 5)
Ask technical questions with citation provenance and automatic evidence validation:

```powershell
python scripts/query_rag.py "What is the maximum working pressure of CFP-402-316L?"
```

Supported options:
- `--mode`: Retrieval mode (`hybrid` default, `keyword`, `vector`).
- `--top-k`: Maximum candidate chunks to retrieve and evaluate (default: 5).
- `--part-number`: Filter by engineering part number (e.g. `CFP-402-316L`).
- `--revision`: Filter by document revision (e.g. `D`).
- `--document-type`: Filter by document type (e.g. `SPECIFICATION`).

#### Example 1: Working Pressure Query
```powershell
python scripts/query_rag.py "What is the maximum working pressure of CFP-402-316L?"
```
Output:
```text
===========================================================================
  ENGINEERING COPILOT - GROUNDED RAG RESPONSE
===========================================================================
  QUESTION : What is the maximum working pressure of CFP-402-316L?
  PROVIDER : local_mock (mock-engineering-llm-v1)
  MODE     : HYBRID (Top-K: 5)
  EVIDENCE : Sufficient
  LATENCY  : 296.2 ms
---------------------------------------------------------------------------

  ANSWER:

    The maximum working pressure for CFP-402-316L is 16.0 bar (232 psi) at 20 C [C1].

---------------------------------------------------------------------------
  CITATIONS (1 referenced):

  [C1] sample_pump_spec.pdf (Page 1, Chunk #0 | Part: CFP-402-316L, Rev: D, Section: CENTRIFUGAL CHEMICAL FEED PUMP - TECHNICAL SPECIFICATION)
      Snippet:
        CENTRIFUGAL CHEMICAL FEED PUMP - TECHNICAL SPECIFICATION
        Document ID: SPEC-PUMP-402-REV-D
        Part Number: CFP-402-316L
        ...
===========================================================================
```

#### Example 2: Bearing Journal Tolerance Query
```powershell
python scripts/query_rag.py "What is the radial bearing journal tolerance?"
```
Output:
```text
  ANSWER:
    The radial bearing journal tolerance is ISO h6 (-0.000 / -0.016 mm) [C1].

  CITATIONS:
  [C1] sample_pump_spec.pdf (Page 2, Chunk #2 | Section: CFP-402 MECHANICAL CLEARANCES & ASSEMBLY SPECIFICATIONS)
```

#### Example 3: Maintenance Oil Change Interval
```powershell
python scripts/query_rag.py "What is the recommended oil change interval?"
```
Output:
```text
  ANSWER:
    The recommended oil change interval is Every 4000 operational hours or 6 months [C1].

  CITATIONS:
  [C1] sample_pump_spec.pdf (Page 2, Chunk #3 | Section: CFP-402 MECHANICAL CLEARANCES & ASSEMBLY SPECIFICATIONS)
```

#### Example 4: Hydrostatic Test Pressure
```powershell
python scripts/query_rag.py "What is the hydrostatic test pressure?"
```
Output:
```text
  ANSWER:
    The hydrostatic test pressure is 24.0 BAR GAUGE (1.5X DESIGN PRESSURE) [C1].

  CITATIONS:
  [C1] sample_pump_spec.pdf (Page 3, Chunk #4 | Section: QUALITY CONTROL INSPECTION & HYDROSTATIC TEST SIGN-OFF)
```

#### Example 5: Out-of-Domain Abstention Query
```powershell
python scripts/query_rag.py "What is the titanium wing spar yield strength?"
```
Output:
```text
===========================================================================
  ENGINEERING COPILOT - GROUNDED RAG RESPONSE
===========================================================================
  QUESTION : What is the titanium wing spar yield strength?
  PROVIDER : local_mock (mock-engineering-llm-v1)
  MODE     : HYBRID (Top-K: 5)
  EVIDENCE : Insufficient / Abstention
  LATENCY  : 348.4 ms
---------------------------------------------------------------------------

  ANSWER:

    The available documents do not contain enough information to answer this question.

---------------------------------------------------------------------------
  CITATIONS: None (Abstained or no relevant evidence matched)
===========================================================================
```

---

### Autonomous Engineering Copilot via LangGraph CLI (Milestone 6)
Execute autonomous question-answering with tool selection, execution traces, dynamic calculations, and grounded engineering citations:

```powershell
python scripts/query_agent.py "<engineering_question>"
```

Supported CLI options:
- `--top-k`: Maximum candidate chunks to retrieve and evaluate (default: 5).
- `--part-number`: Optional engineering part number filter (e.g., `CFP-402-316L`).
- `--revision`: Optional document revision filter (e.g., `D`).

#### Example 1: Multi-Tool Composite Workflow (Search + Dynamic Engineering Unit Conversion)
The agent recognizes that the query requires retrieving an engineering specification and converting its units into psi:
```powershell
python scripts/query_agent.py "What is the maximum working pressure of CFP-402-316L in psi?"
```
Output:
```text
================================================================================
  ATLAS COPCO GECIA - ENGINEERING COPILOT (LANGGRAPH AGENT)
================================================================================
  QUESTION    : What is the maximum working pressure of CFP-402-316L in psi?
  PROVIDER    : local_mock (mock-engineering-llm-v1)
  STATUS      : Grounded Synthesis Complete
  LATENCY     : 327.8 ms
  TOOLS USED  : search_engineering_documents, calculate_engineering
--------------------------------------------------------------------------------
  TOOL EXECUTION TRACE:
    [1] [OK] search_engineering_documents
        Input  : {'query': 'What is the maximum working pressure of CFP-402-316L in psi?', 'top_k': 5, 'part_number': 'CFP-402-316L'}
        Output : {'success': True, 'query': 'What is the maximum working pressure of CFP-402-316L in psi?', 'total_results': 5, 'retrieval_mode': 'hybrid', 'hits_count': 5}
    [2] [OK] calculate_engineering
        Input  : {'operation': 'bar_to_psi'}
        Output : {'success': True, 'operation': 'bar_to_psi', 'input': 16.0, 'result': 232.06, 'unit': 'psi', 'explanation': '16.0 bar * 14.50377 psi/bar ~= 232.06 psi'}
--------------------------------------------------------------------------------

  ANSWER:

    The maximum working pressure for CFP-402-316L is 16.0 bar (232 psi) at 20 C [C1].
    Using the engineering conversion tool, this corresponds to approximately 232.06 psi (16.0 bar * 14.50377 psi/bar ~= 232.06 psi).

--------------------------------------------------------------------------------
  GROUNDED CITATIONS (1 verified):

  [C1] sample_pump_spec.pdf (Page 1, Chunk #0 | Part: CFP-402-316L, Rev: D, Section: CENTRIFUGAL CHEMICAL FEED PUMP - TECHNICAL SPECIFICATION)
      Excerpt:
        CENTRIFUGAL CHEMICAL FEED PUMP - TECHNICAL SPECIFICATION
        Document ID: SPEC-PUMP-402-REV-D
        Part Number: CFP-402-316L
        ...
================================================================================
```

#### Example 2: Specification Search with Direct Engineering Citation
The agent selects `search_engineering_documents` to locate running clearances and tolerances:
```powershell
python scripts/query_agent.py "What is the radial bearing journal tolerance?"
```
Output:
```text
  ANSWER:
    The radial bearing journal tolerance is ISO h6 (-0.000 / -0.016 mm) [C1].

  GROUNDED CITATIONS (1 verified):
  [C1] sample_pump_spec.pdf (Page 2, Chunk #2 | Section: CFP-402 MECHANICAL CLEARANCES & ASSEMBLY SPECIFICATIONS)
```

#### Example 3: Document Metadata Registry Lookup
The agent detects a metadata query and calls `get_document_metadata` directly against the database:
```powershell
python scripts/query_agent.py "What is the document revision and status for sample_pump_spec.pdf?"
```
Output:
```text
================================================================================
  ATLAS COPCO GECIA - ENGINEERING COPILOT (LANGGRAPH AGENT)
================================================================================
  QUESTION    : What is the document revision and status for sample_pump_spec.pdf?
  PROVIDER    : local_mock (mock-engineering-llm-v1)
  STATUS      : Grounded Synthesis Complete
  LATENCY     : 437.1 ms
  TOOLS USED  : get_document_metadata
--------------------------------------------------------------------------------
  TOOL EXECUTION TRACE:
    [1] [OK] get_document_metadata
        Input  : {'filename': 'sample_pump_spec.pdf'}
        Output : {'success': True, 'found': True, 'document_id': '95ba61ff-d218-4eb7-8d53-f5318f9f1da1', 'filename': 'sample_pump_spec.pdf', 'document_type': 'SPECIFICATION', 'part_number': 'CFP-402-316L', 'revision': 'D', 'status': 'PROCESSED', 'page_count': 3, 'file_size_bytes': 1206071}
--------------------------------------------------------------------------------

  ANSWER:

    According to verified engineering document metadata, document 'sample_pump_spec.pdf' (Part Number: CFP-402-316L) is currently at Revision D with status 'PROCESSED' and contains 3 pages [C1].

--------------------------------------------------------------------------------
  GROUNDED CITATIONS (1 verified):

  [C1] sample_pump_spec.pdf (Page 1, Chunk #0 | Part: CFP-402-316L, Rev: D, Section: DOCUMENT METADATA REGISTRY)
================================================================================
```

#### Example 4: Direct Engineering Unit Conversion
The agent executes isolated numerical conversion via `calculate_engineering` without retrieving irrelevant documents:
```powershell
python scripts/query_agent.py "Convert 75 kW to horsepower"
```
Output:
```text
  ANSWER:
    75.0 kW * 1.34102 hp/kW ~= 100.58 hp

  TOOLS USED: calculate_engineering
  GROUNDED CITATIONS: None (Abstained or pure mathematical calculation)
```

#### Example 5: Abstention / Insufficient Evidence Query
When queried on specifications not present in the engineering corpus:
```powershell
python scripts/query_agent.py "What is the titanium wing spar yield strength?"
```
Output:
```text
================================================================================
  ATLAS COPCO GECIA - ENGINEERING COPILOT (LANGGRAPH AGENT)
================================================================================
  QUESTION    : What is the titanium wing spar yield strength?
  PROVIDER    : local_mock (mock-engineering-llm-v1)
  STATUS      : Abstained / Insufficient Evidence
  LATENCY     : 349.1 ms
  TOOLS USED  : search_engineering_documents
--------------------------------------------------------------------------------
  TOOL EXECUTION TRACE:
    [1] [OK] search_engineering_documents
        Input  : {'query': 'What is the titanium wing spar yield strength?', 'top_k': 5}
        Output : {'success': True, 'query': 'What is the titanium wing spar yield strength?', 'total_results': 5, 'retrieval_mode': 'hybrid', 'hits_count': 5}
--------------------------------------------------------------------------------

  ANSWER:

    The available documents do not contain enough information to answer this question.

--------------------------------------------------------------------------------
  GROUNDED CITATIONS: None (Abstained or pure mathematical calculation)
================================================================================
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

---

### 3. Grounded Retrieval-Augmented Generation (RAG) (Milestone 5)

#### Ask Technical Engineering Question
`POST /api/v1/rag/query`
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the maximum working pressure of CFP-402-316L?",
    "top_k": 5,
    "retrieval_mode": "hybrid",
    "filters": {
      "part_number": "CFP-402-316L",
      "revision": "D"
    }
  }'
```
Response:
```json
{
  "success": true,
  "message": "RAG answer synthesized successfully.",
  "data": {
    "query": "What is the maximum working pressure of CFP-402-316L?",
    "answer": "The maximum working pressure for CFP-402-316L is 16.0 bar (232 psi) at 20 C [C1].",
    "citations": [
      {
        "citation_id": "C1",
        "document_id": "51826aca-8497-47b5-939b-edc76c0a522e",
        "filename": "sample_pump_spec.pdf",
        "page_number": 1,
        "chunk_id": "8d212ab3-982e-4e55-b62a-b9d50c8b78a5",
        "chunk_index": 0,
        "part_number": "CFP-402-316L",
        "revision": "D",
        "section": "CENTRIFUGAL CHEMICAL FEED PUMP - TECHNICAL SPECIFICATION",
        "snippet": "CENTRIFUGAL CHEMICAL FEED PUMP - TECHNICAL SPECIFICATION\nDocument ID: SPEC-PUMP-402-REV-D\nPart Number: CFP-402-316L\nRevision: D..."
      }
    ],
    "retrieved_chunks_count": 5,
    "retrieval_mode": "hybrid",
    "sufficient_evidence": true,
    "provider": "local_mock",
    "model": "mock-engineering-llm-v1",
    "timing_ms": 296.2
  }
}
```

#### Abstention Response (When Evidence is Missing)
```json
{
  "success": true,
  "message": "Insufficient evidence to answer query.",
  "data": {
    "query": "What is the titanium wing spar yield strength?",
    "answer": "The available documents do not contain enough information to answer this question.",
    "citations": [],
    "retrieved_chunks_count": 0,
    "retrieval_mode": "hybrid",
    "sufficient_evidence": false,
    "provider": "local_mock",
    "model": "mock-engineering-llm-v1",
    "timing_ms": 12.4
  }
}
```

---

### 4. Agentic Copilot & Multi-Tool Execution (Milestone 6)

#### Query Autonomous Engineering Copilot
`POST /api/v1/agent/query`

Orchestrates multi-tool execution (document search, metadata lookup, unit calculations), dynamic chained parameter passing, and grounded synthesis with citation tracking.

##### Request (Multi-Tool Query with Part Filter):
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agent/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the maximum working pressure of CFP-402-316L in psi?",
    "top_k": 5,
    "filters": {
      "part_number": "CFP-402-316L"
    }
  }'
```

##### Response:
```json
{
  "success": true,
  "message": "Agent query executed successfully.",
  "data": {
    "query": "What is the maximum working pressure of CFP-402-316L in psi?",
    "answer": "The maximum working pressure for CFP-402-316L is 16.0 bar (232 psi) at 20 C [C1].\nUsing the engineering conversion tool, this corresponds to approximately 232.06 psi (16.0 bar * 14.50377 psi/bar ~= 232.06 psi).",
    "citations": [
      {
        "citation_id": "C1",
        "document_id": "95ba61ff-d218-4eb7-8d53-f5318f9f1da1",
        "filename": "sample_pump_spec.pdf",
        "page_number": 1,
        "chunk_id": "8d212ab3-982e-4e55-b62a-b9d50c8b78a5",
        "chunk_index": 0,
        "part_number": "CFP-402-316L",
        "revision": "D",
        "section": "CENTRIFUGAL CHEMICAL FEED PUMP - TECHNICAL SPECIFICATION",
        "snippet": "CENTRIFUGAL CHEMICAL FEED PUMP - TECHNICAL SPECIFICATION\nDocument ID: SPEC-PUMP-402-REV-D\nPart Number: CFP-402-316L\nRevision: D..."
      }
    ],
    "tool_traces": [
      {
        "tool_name": "search_engineering_documents",
        "status": "success",
        "input_summary": {
          "query": "What is the maximum working pressure of CFP-402-316L in psi?",
          "top_k": 5,
          "part_number": "CFP-402-316L"
        },
        "output_summary": {
          "success": true,
          "hits_count": 5,
          "retrieval_mode": "hybrid"
        },
        "error": null
      },
      {
        "tool_name": "calculate_engineering",
        "status": "success",
        "input_summary": {
          "operation": "bar_to_psi"
        },
        "output_summary": {
          "success": true,
          "operation": "bar_to_psi",
          "input": 16.0,
          "result": 232.06,
          "unit": "psi",
          "explanation": "16.0 bar * 14.50377 psi/bar ~= 232.06 psi"
        },
        "error": null
      }
    ],
    "tools_called": [
      "search_engineering_documents",
      "calculate_engineering"
    ],
    "should_abstain": false,
    "metadata": {
      "provider": "local_mock",
      "model": "mock-engineering-llm-v1",
      "latency_ms": 327.8
    }
  }
}
```

##### Metadata Lookup Query:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agent/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the document revision and status for sample_pump_spec.pdf?"
  }'
```
Response:
```json
{
  "success": true,
  "message": "Agent query executed successfully.",
  "data": {
    "query": "What is the document revision and status for sample_pump_spec.pdf?",
    "answer": "According to verified engineering document metadata, document 'sample_pump_spec.pdf' (Part Number: CFP-402-316L) is currently at Revision D with status 'PROCESSED' and contains 3 pages [C1].",
    "citations": [
      {
        "citation_id": "C1",
        "document_id": "95ba61ff-d218-4eb7-8d53-f5318f9f1da1",
        "filename": "sample_pump_spec.pdf",
        "page_number": 1,
        "chunk_id": null,
        "chunk_index": 0,
        "part_number": "CFP-402-316L",
        "revision": "D",
        "section": "DOCUMENT METADATA REGISTRY",
        "snippet": "Filename: sample_pump_spec.pdf | Part: CFP-402-316L | Rev: D | Status: PROCESSED | Pages: 3"
      }
    ],
    "tool_traces": [
      {
        "tool_name": "get_document_metadata",
        "status": "success",
        "input_summary": {
          "filename": "sample_pump_spec.pdf"
        },
        "output_summary": {
          "success": true,
          "found": true,
          "revision": "D",
          "status": "PROCESSED",
          "page_count": 3
        },
        "error": null
      }
    ],
    "tools_called": [
      "get_document_metadata"
    ],
    "should_abstain": false,
    "metadata": {
      "provider": "local_mock",
      "model": "mock-engineering-llm-v1",
      "latency_ms": 437.1
    }
  }
}
```

##### Abstention Response:
```json
{
  "success": true,
  "message": "Agent query executed successfully.",
  "data": {
    "query": "What is the titanium wing spar yield strength?",
    "answer": "The available documents do not contain enough information to answer this question.",
    "citations": [],
    "tool_traces": [
      {
        "tool_name": "search_engineering_documents",
        "status": "success",
        "input_summary": {
          "query": "What is the titanium wing spar yield strength?",
          "top_k": 5
        },
        "output_summary": {
          "success": true,
          "hits_count": 5
        },
        "error": null
      }
    ],
    "tools_called": [
      "search_engineering_documents"
    ],
    "should_abstain": true,
    "metadata": {
      "provider": "local_mock",
      "model": "mock-engineering-llm-v1",
      "latency_ms": 349.1
    }
  }
}
```


