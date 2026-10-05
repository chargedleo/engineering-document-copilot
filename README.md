# Engineering Document Intelligence & CAD Knowledge Copilot

A production-grade intelligent copilot platform designed for engineering teams to parse, index, search, and reason over complex engineering documents (specifications, BOMs, standards, datasheets) and CAD models/metadata.

> **Project Status (Milestone 8 - Containerization, Reproducibility & Productionization)**:
> Fully containerized, reproducible application featuring Docker Compose orchestration (`postgres:16-alpine`, Python 3.11-slim FastAPI backend with system OCR and non-root execution, multi-stage Node 20 / Nginx Alpine frontend), automated startup schema migrations via Alembic (`entrypoint.sh`), environment-driven configuration supporting dual workflows (local Windows development alongside Docker Compose), automated GitHub Actions CI pipeline (`.github/workflows/ci.yml`), and 85 passing tests.

---

## 🏗️ Architecture & Core Flows

### High-Level Service Architecture
```text
React UI (Port 5173 / Nginx)
    ↓  [Reverse Proxy /api/]
FastAPI Backend (Port 8000 / Uvicorn)
    ↓
LangGraph Agent Orchestrator
    ├── Engineering Search Tool (Hybrid BM25 + Vector RRF)
    ├── Document Metadata Tool (PostgreSQL Registry)
    └── Engineering Calculator Tool (Deterministic Unit Converters)
         ↓
PostgreSQL 16 (Port 5432 / Persistent Storage)
```

### End-to-End Ingestion & Reasoning Flow
```text
Engineering PDF
    ↓
Text Extraction & OCR Fallback (PyMuPDF + OpenCV + Tesseract)
    ↓
Page-Aware Structural Chunks (Units, Tolerances, Headings Preserved)
    ↓
Hybrid Retrieval Engine (BM25 Keyword + 1536-dim Dense Vector + RRF)
    ↓
Grounded RAG (Evidence Context Assembly, Citations [C1], Prompt-Injection Defense)
    ↓
LangGraph Agent (Multi-Tool Composite Planning & Unit Conversion)
    ↓
Minimal Monochrome UI (Typography-Led Editorial Presentation)
```

---

## 🧰 Technology Stack

- **Backend**: Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) (Async 2.x), [asyncpg](https://magicstack.github.io/asyncpg/), [Alembic](https://alembic.sqlalchemy.org/)
- **Document Intelligence & OCR (Milestone 3)**:
  - **PyMuPDF (`fitz`)**: High-performance PDF validation, structure analysis, and native text extraction.
  - **OpenCV (`cv2`)**: Headless image preprocessing for scanned pages (grayscale, Gaussian denoise, Otsu thresholding).
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
- **Visual Design System & Frontend Architecture (Milestone 7)**:
  - **React 18 + TypeScript + Vite**: Responsive, minimal single-page application.
  - **Monochrome Design Philosophy**: High-contrast, typography-led aesthetic inspired by Linear, Vercel, and Google Antigravity. Strictly black, white, and grayscale canvas with zero accent colors.
  - **Editorial Layout**: Document-style conversation streams, bordered technical citations (`[C1]`), typographic calculation sheets, and compact technical tool logs.
- **Productionization & Container Orchestration (Milestone 8)**:
  - **Docker & Docker Compose**: Multi-container stack (`postgres:16-alpine`, `backend`, `frontend`).
  - **Backend Image**: Debian-slim base with system `tesseract-ocr`, `libgl1`, `libglib2.0-0`, non-root user `appuser`, `HEALTHCHECK`, and `entrypoint.sh` for reliable startup migrations.
  - **Frontend Image**: Multi-stage build (`node:20-alpine` build -> `nginx:alpine` runtime) with SPA routing, 50MB upload buffer, security headers, and `/api/` reverse proxy.
  - **CI/CD**: GitHub Actions workflow (`.github/workflows/ci.yml`) validating backend tests, frontend lint & build, and Docker configurations without requiring cloud credentials.
- **Database**: PostgreSQL 16 (Native Windows development or Docker Compose container)
- **Testing**: [pytest](https://pytest.org/), `pytest-asyncio`, `aiosqlite` (85 hermetic automated tests)

For an in-depth architectural breakdown and sequence diagrams, refer to [`architecture.md`](./architecture.md).

---

## 📁 Repository Structure

```text
├── .env.example              # Environment variables template with safe placeholders
├── .gitignore                 # Excludes .env, virtualenvs, caches, raw uploads
├── .github/workflows/ci.yml   # GitHub Actions automated test & build pipeline
├── docker-compose.yml         # Root Docker Compose production orchestration
├── README.md                  # Project overview and reproduction guide
├── architecture.md            # System architecture and data flow blueprint
├── backend/                   # FastAPI application & database migrations
│   ├── alembic/               # Alembic database migration scripts & versions
│   │   ├── versions/          # Version-controlled migration files
│   │   └── env.py             # Async Alembic runner
│   ├── app/
│   │   ├── api/v1/            # Versioned API routes (health, documents, search, rag, agent, cad, chat)
│   │   │   ├── endpoints/     # Route handlers (agent.py, rag.py, search.py, documents.py)
│   │   │   └── router.py      # Aggregated API router
│   │   ├── core/              # Config (Pydantic Settings), DB session, logging
│   │   ├── models/            # SQLAlchemy ORM models (Document, DocumentPage, DocumentChunk)
│   │   ├── schemas/           # Pydantic v2 schemas (document, chunk, rag, agent, common)
│   │   ├── services/          # Business logic layer (document, chunking, search, rag, agent)
│   │   └── agents/            # LangGraph agent orchestration (graph, nodes, planner, state, tools)
│   ├── tests/                 # Hermetic automated test suite (85 pytest tests)
│   │   ├── test_agent.py      # LangGraph agent & multi-tool test suite (21 tests)
│   │   ├── test_rag.py        # Grounded RAG & prompt injection test suite (15 tests)
│   │   ├── test_search.py     # Hybrid retrieval test suite (11 tests)
│   │   ├── test_chunking.py   # Engineering chunker tests (6 tests)
│   │   ├── test_document_processing.py # PDF & OCR processing tests (10 tests)
│   │   ├── test_documents.py  # Document CRUD & upload tests (10 tests)
│   │   ├── test_health.py     # Health & readiness tests (4 tests)
│   │   └── test_production_config.py # Production config, health degradation, container specs (8 tests)
│   ├── .dockerignore          # Excludes caches, venvs, and secrets from image build
│   ├── Dockerfile             # Production Debian-slim image with OCR and non-root appuser
│   ├── entrypoint.sh          # Container entrypoint with migration execution
│   └── pyproject.toml         # Python packaging and pytest configuration
├── frontend/                  # React 18 + TypeScript + Vite SPA (Milestone 7)
│   ├── src/
│   │   ├── components/        # chat/, documents/, cad/, architecture/, layout/, common/
│   │   ├── services/          # API clients (agentService, documentService, api)
│   │   ├── hooks/             # Reactive state hooks (useChat, useDocuments)
│   │   ├── types/             # Strict TypeScript definitions
│   │   ├── App.tsx            # Clean view orchestrator
│   │   └── index.css          # Monochrome typography-led design system
│   ├── .dockerignore          # Excludes node_modules and build artifacts
│   ├── Dockerfile             # Multi-stage production build (Node 20 -> Nginx Alpine)
│   ├── nginx.conf             # Hardened Nginx configuration with reverse proxy and 50MB body limit
│   ├── package.json
│   └── vite.config.ts         # Reverse-proxy to FastAPI backend (localhost:8000)
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
└── docker/                    # Subdirectory Docker Compose reference
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

Configuration variables are grouped into distinct categories:

| Category | Key Variables | Description | Local Windows | Docker Compose |
| :--- | :--- | :--- | :--- | :--- |
| **Application** | `APP_NAME`, `APP_ENV`, `DEBUG`, `HOST`, `PORT` | FastAPI server runtime parameters. | `PORT=8000`, `DEBUG=True` | Injected by Compose |
| **Database** | `DATABASE_URL` | Asynchronous SQLAlchemy connection string. | `localhost:5432` | `postgres:5432` |
| **Migrations** | `RUN_MIGRATIONS` | Automatically run `alembic upgrade head` on startup. | Executed via CLI | `true` (via entrypoint) |
| **Storage** | `DOCUMENTS_STORAGE_DIR`, `PROCESSED_STORAGE_DIR` | Filesystem paths for uploaded PDFs and cached chunks. | `./data/documents` | Mounted `/app/data` |
| **OCR** | `TESSERACT_CMD`, `OCR_DPI` | Path to Tesseract engine and render resolution. | Auto-discovered on PATH | Discovered on PATH |
| **Search & RAG**| `EMBEDDING_PROVIDER`, `SEARCH_PROVIDER`, `LLM_PROVIDER` | Provider selection (`auto`, `local`, `azure`). | `auto` (uses deterministic local) | `auto` |
| **Azure Staging**| `AZURE_OPENAI_API_KEY`, `AZURE_SEARCH_ENDPOINT` | Optional cloud credentials (decoupled from local run). | Optional (leave empty) | Optional (leave empty) |
| **Frontend** | `VITE_API_BASE_URL`, `FRONTEND_PORT` | Client API endpoint and exposed host port. | `http://localhost:8000/api/v1` | `5173` |

---

## 🐳 Docker Compose Workflow (Productionization)

Docker Compose provides a reproducible multi-container environment that starts PostgreSQL, runs migrations, launches the backend, and serves the frontend.

### 1. Build and Start the Stack
From the project root:
```bash
docker compose up --build
```

Compose orchestrates startup with health dependency ordering:
1. `engineering_copilot_db` launches and verifies readiness (`pg_isready`).
2. `engineering_copilot_backend` verifies database reachability, runs `alembic upgrade head`, and starts Uvicorn.
3. `engineering_copilot_frontend` compiles production assets, boots Nginx, and proxies `/api/` calls to the backend.

### 2. Access Containerized Services
- **Web Application**: [`http://localhost:5173`](http://localhost:5173)
- **Backend API Docs (Swagger UI)**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **Liveness Health Check**: [`http://localhost:8000/api/v1/health`](http://localhost:8000/api/v1/health)
- **Readiness Health Check (DB Connected)**: [`http://localhost:8000/api/v1/health/ready`](http://localhost:8000/api/v1/health/ready)

### 3. Stop and Reset Containers
To stop containers while preserving database state:
```bash
docker compose down
```

To stop containers and completely reset database volume storage:
```bash
docker compose down -v
```

---

## 💻 Local Development Setup (Without Docker)

The existing native Windows development workflow remains completely supported and does not require Docker.

### 1. Database & Migrations (Local Windows PostgreSQL)
Start PostgreSQL 16 on port `5432` (installed at `C:\Users\admin\pgsql`):
```powershell
& "C:\Users\admin\pgsql\bin\postgres.exe" -D "C:\Users\admin\pgsql\data"
```

If initializing for the first time:
```powershell
$env:PGPASSWORD = "postgres"
& "C:\Users\admin\pgsql\bin\createdb.exe" -U postgres -h localhost engineering_copilot
```

Apply database migrations:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Verify migration rollback and upgrade:
```powershell
alembic downgrade -1
alembic upgrade head
```

### 2. Run Automated Backend Test Suite
The hermetic test suite runs against an in-memory SQLite database (`aiosqlite`) with zero cloud dependencies:
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
tests/test_production_config.py (8 tests) ........                       PASSED
tests/test_rag.py (15 tests) ...............                             PASSED
tests/test_search.py (11 tests) ...........                              PASSED

============================= 85 passed in 10.81s =============================
```

### 3. Start FastAPI Server
```powershell
# From backend/ directory
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Start React Frontend (Development)
```powershell
# From frontend/ directory
npm.cmd run dev
```
Open [`http://localhost:5173`](http://localhost:5173) in your browser.

To run frontend quality checks:
```powershell
# Type check and lint
npm.cmd run lint

# Production build
npm.cmd run build
```

---

## 🔍 Tesseract OCR Configuration

Tesseract OCR is supported with automatic multi-tier discovery:
1. **Configured setting**: Looks at `TESSERACT_CMD` in `.env` if provided.
2. **System PATH**: Searches for `tesseract` on PATH via `shutil.which`.
3. **Standard Windows paths fallback**: Checks `C:\Program Files\Tesseract-OCR\tesseract.exe`.
4. **Linux / Container**: Automatically located at `/usr/bin/tesseract` via system package `tesseract-ocr`.

Verification on Windows:
```powershell
where.exe tesseract
# Output: C:\Program Files\Tesseract-OCR\tesseract.exe

tesseract --version
# Output: tesseract v5.x
```

*(Note: If Tesseract is not installed, digital-text PDFs continue to process normally. When an image-only page requires OCR, a clear 503 error is returned without crashing the server).*

---

## 🛠️ CLI Ingestion, Retrieval & Agent Tools

### 1. Ingest and Index Engineering PDFs
Ingest a single engineering PDF with automatic structural chunking and vector indexing:
```powershell
python scripts/ingest_cad_docs.py data/sample_pump_spec.pdf --document-type "SPECIFICATION" --part-number "CFP-402-316L" --revision "D"
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

### 2. Search Engineering Chunks via CLI
Query engineering specifications using keyword, vector, or hybrid retrieval:
```powershell
python scripts/search_docs.py "bearing journal tolerance ISO h6" --mode hybrid
```

### 3. Grounded Engineering Q&A via RAG CLI (Milestone 5)
Ask technical questions with citation provenance and automatic evidence validation:
```powershell
python scripts/query_rag.py "What is the maximum working pressure of CFP-402-316L?"
```

### 4. Autonomous Engineering Copilot via LangGraph CLI (Milestone 6)
Execute autonomous question-answering with tool selection, execution traces, dynamic calculations, and grounded engineering citations:
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
  LATENCY     : 439.5 ms
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
================================================================================
```

---

## 📡 API Reference Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/health` | `GET` | Service liveness healthcheck (returns 200). |
| `/api/v1/health/ready` | `GET` | Service readiness check (verifies database connectivity; returns 503 if unreachable). |
| `/api/v1/documents/upload` | `POST` | Multipart upload and ingestion of engineering PDFs. |
| `/api/v1/documents` | `GET` | List ingested engineering documents with pagination and filters. |
| `/api/v1/documents/{id}/pages` | `GET` | Retrieve extracted page text and OCR flags. |
| `/api/v1/documents/{id}/chunks/generate` | `POST` | Execute structural chunking and vector indexing. |
| `/api/v1/search` | `POST` | Hybrid keyword + dense vector search across engineering chunks. |
| `/api/v1/rag/query` | `POST` | Grounded RAG synthesis with evidence boundaries and citations. |
| `/api/v1/agent/query` | `POST` | Autonomous LangGraph agent with tool execution traces. |

---

## 🔒 Security Hardening Review

- **Zero Baked Secrets**: No API keys, database passwords, or connection strings in Docker images or source code.
- **Non-Root Execution**: Backend container runs strictly as unprivileged `appuser:appgroup` (UID 1000).
- **Multi-Stage Minimization**: Production frontend container discards `node_modules` and compiler tools; runtime contains only Nginx and compiled HTML/JS/CSS assets.
- **Upload & Body Limits**: Nginx reverse proxy explicitly limits request bodies to 50MB (`client_max_body_size 50M`), matching backend constraints.
- **Security Headers**: Production Nginx injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`, and strict referrer policy headers.
- **Untrusted Prompt Isolation**: Retrieved document text is treated as passive untrusted data wrapped in XML boundaries to defend against prompt injections.
- **Safe Engineering Calculator**: Calculation tool uses explicit mathematical operation dispatch and never invokes `eval()`.

---

## 🧪 CI/CD Pipeline (GitHub Actions)

Continuous integration is configured in [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) and executes on every push and pull request to `master` and `main`:

1. **`backend-test` Job**:
   - Ubuntu runner with `tesseract-ocr`, `tesseract-ocr-eng`, `libgl1`, and `libglib2.0-0` installed.
   - Python 3.11 with cached pip dependencies.
   - Runs `pytest backend/tests/ -v` (85 tests passing).
   - Entirely hermetic with zero cloud credentials required.
2. **`frontend-check` Job**:
   - Node.js 20 with cached npm dependencies.
   - Executes TypeScript type checking and linting (`npm run lint`).
   - Executes production build compilation (`npm run build`).
3. **`docker-validate` Job**:
   - Validates the root Docker Compose specification via `docker compose config`.
   - Builds backend and frontend test images using Buildx.

---

## ⚖️ Verification Status & Limitations

| Component | Status | Evidence & Notes |
| :--- | :--- | :--- |
| **Backend Test Suite** | **VERIFIED** | 85 passed in 10.81s (77 baseline + 8 production config/health tests). |
| **Frontend Lint** | **VERIFIED** | `npm.cmd run lint` (`tsc --noEmit`) passed with 0 errors. |
| **Frontend Build** | **VERIFIED** | `npm.cmd run build` (`vite build`) passed (42 modules, 169.66 kB bundle). |
| **Docker Compose Config** | **VERIFIED** | `docker compose -f docker-compose.yml config` validated with exit code 0. |
| **Local PostgreSQL Workflow** | **VERIFIED** | PostgreSQL 16 on Windows verified with migrations and agent queries. |
| **Agent End-to-End Query** | **VERIFIED** | Max working pressure query verified: 16.0 bar ≈ 232.06 psi with citation `[C1]`. |
| **Docker Runtime Containers** | **IMPLEMENTED** | `backend/Dockerfile` and `frontend/Dockerfile` are production-complete with LF line endings, healthchecks, and non-root user. Runtime execution on this Windows machine is pending an active Docker engine / CI runner. |
| **Azure Cloud Deployments** | **CONFIGURED / DECOUPLED** | Azure OpenAI and Azure AI Search adapters exist in codebase, but local execution uses deterministic offline mock providers. Live cloud deployment belongs to Milestone 10. |

---

## 🗺️ Roadmap: Milestone 9 & Beyond

- **Milestone 9 (Planned)**: **CAD Geometry & Visual Navigation**
  - STEP/DXF parser for part hierarchies and BOM cross-referencing.
  - WebGL / Three.js 3D viewport canvas.
- **Milestone 10 (Planned)**: **Azure Cloud Deployment**
  - Azure Container Apps / Azure App Service hosting.
  - Azure PostgreSQL Flexible Server.
  - Live Azure OpenAI (GPT-4o) and Azure AI Search deployment.
