# Engineering Document Intelligence & CAD Knowledge Copilot

A production-oriented intelligent copilot platform designed for engineering teams to parse, index, search, and reason over complex engineering documents (specifications, BOMs, standards, datasheets) and CAD models/metadata.

<p align="center">
  <a href="https://lively-river-014b48c0f.6.azurestaticapps.net/">
    <strong>Open Live Demo</strong>
  </a>
</p>

<p align="center">
  <img src="docs/screenshots/home.png.png" alt="Engineering Copilot Home" width="900">
</p>

---

## Core Capabilities

<table>
<tr>
<td width="33%" align="center">

### Grounded RAG

<a href="docs/screenshots/grounded-rag.png.png">
  <img src="docs/screenshots/grounded-rag.png.png" alt="Grounded Engineering RAG">
</a>

**Citation-backed engineering answers**

</td>

<td width="33%" align="center">

### Engineering Tools

<a href="docs/screenshots/engineering-calculation.png.png">
  <img src="docs/screenshots/engineering-calculation.png.png" alt="Deterministic Engineering Calculation">
</a>

**Tool-based deterministic calculations**

</td>

<td width="33%" align="center">

### Safe Abstention

<a href="docs/screenshots/absentation.png.png">
  <img src="docs/screenshots/absentation.png.png" alt="Evidence-Grounded Abstention">
</a>

**No answer when evidence is insufficient**

</td>
</tr>
</table>

---

## System Overview

<p align="center">
  <img src="docs/screenshots/architecture.png.png" alt="Engineering Copilot Architecture" width="900">
</p>

## Document Intelligence

<p align="center">
  <img src="docs/screenshots/document-registry.png.png" alt="Engineering Document Registry" width="900">
</p>

---
> **Portfolio Alignment**: Built as an applied engineering portfolio project supporting applications for **AI/ML Engineer**, **AI Graduate Engineer**, and **CAD Automation & Applied AI** roles (e.g., Atlas Copco GECIA Graduate Engineer Trainee). Demonstrates enterprise document intelligence, deterministic hybrid retrieval, grounded agentic reasoning, Docker productionization, and live Microsoft Azure cloud integration.
>
> **Project Status (Milestone 10 — Final Evaluation, Polish & Portfolio Release [COMPLETE])**:
> The system has completed comprehensive automated benchmark evaluation (8/8 test cases passed across both local hermetic and live Azure cloud modes with 100% citation fidelity and 100% out-of-domain abstention precision). Live enterprise data and AI cloud services are verified on Microsoft Azure (`rg-engineering-copilot`): Azure Database for PostgreSQL Flexible Server v16 (`psql-engcopilot-06724`), Azure OpenAI Service (`text-embedding-3-small` + `gpt-4o`), Azure AI Search (`engineering-docs-index` with HNSW vector + hybrid RRF), Azure Blob Storage (`stengcopilot06724`), and Azure Static Web Apps / Storage Static Website (`stengcopilot06724.z13.web.core.windows.net`).
> *Azure Backend Compute Hosting Notice*: Azure backend compute container hosting (Container Apps / App Service) is **NOT DEPLOYED / NOT VERIFIED** and remains a future deployment step. The application is fully operational via hybrid local/cloud execution and multi-container Docker Compose.

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
- **Azure Cloud Integration & Service Verification (Milestone 9)**:
  - **Azure Database for PostgreSQL Flexible Server**: PostgreSQL 16 managed database (`Standard_B1ms`) with SSL encryption and Alembic schema management (Live & Verified).
  - **Azure OpenAI Service**: Production dense embeddings (`text-embedding-3-small`, 1536 dims) and grounded conversational synthesis (`gpt-4o`) (Live & Verified).
  - **Azure AI Search**: Enterprise hybrid vector search with HNSW vector profile and Reciprocal Rank Fusion (`vectorQueries` REST API 2023-11-01) (Live & Verified).
  - **Azure Blob Storage**: Cloud document persistence for raw engineering PDFs via `StorageService` (Live & Verified).
  - **Azure Storage Static Website & Azure Static Web Apps**: Production static asset hosting for the monochrome React UI (Live & Verified).
  - **Azure Container Registry**: Image repository (`acrengcopilot06724.azurecr.io`) for container distribution (Configured).
  - **Azure Backend Compute Hosting**: Backend compute hosting on Azure Container Apps / App Service is not deployed / not verified (future deployment step; currently connects to live Azure services via hybrid local or Docker Compose execution).
- **Evaluation, Polish & Portfolio Release (Milestone 10)**:
  - **Automated Benchmark Harness**: [`scripts/evaluate_copilot.py`](./scripts/evaluate_copilot.py) evaluating 8 engineering benchmark scenarios with quantitative scoring across local hermetic and live Azure modes.
  - **Metrics & Reports**: Structured JSON benchmark evaluation output ([`docs/evaluation-report.json`](./docs/evaluation-report.json)) recording retrieval precision, citation accuracy, abstention reliability, and latency.
  - **Interview & Demonstration Deliverables**: 3-minute timed interview walkthrough ([`docs/demo-script.md`](./docs/demo-script.md)) and technical defense notes ([`docs/interview-notes.md`](./docs/interview-notes.md)).
- **Database**: PostgreSQL 16 (Native Windows development, Docker Compose, or Azure PostgreSQL Flexible Server)
- **Testing**: [pytest](https://pytest.org/), `pytest-asyncio`, `aiosqlite` (94 hermetic automated tests across 9 test suites)

For an in-depth architectural breakdown and sequence diagrams, refer to [`architecture.md`](./architecture.md).

---

## 📁 Repository Structure

```text
├── .env.example              # Environment variables template with safe placeholders
├── .gitignore                 # Excludes .env, virtualenvs, caches, raw uploads
├── .github/workflows/ci.yml   # GitHub Actions automated test & build pipeline
├── docker-compose.yml         # Root Docker Compose production orchestration
├── README.md                  # Project overview, benchmark evaluation, and portfolio guide
├── architecture.md            # System architecture and data flow blueprint
├── docs/                      # Portfolio demonstration, interview notes, and evaluation data
│   ├── demo-script.md         # 3-minute timed technical interview presentation script
│   ├── interview-notes.md     # Engineering decision rationales and defense Q&A
│   └── evaluation-report.json # Automated benchmark evaluation metrics (local & Azure)
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
│   ├── tests/                 # Hermetic automated test suite (94 pytest tests)
│   │   ├── test_agent.py      # LangGraph agent & multi-tool test suite (21 tests)
│   │   ├── test_rag.py        # Grounded RAG & prompt injection test suite (15 tests)
│   │   ├── test_search.py     # Hybrid retrieval test suite (11 tests)
│   │   ├── test_chunking.py   # Engineering chunker tests (6 tests)
│   │   ├── test_document_processing.py # PDF & OCR processing tests (10 tests)
│   │   ├── test_documents.py  # Document CRUD & upload tests (10 tests)
│   │   ├── test_health.py     # Health & readiness tests (4 tests)
│   │   ├── test_production_config.py # Production config, health degradation, container specs (8 tests)
│   │   └── test_storage.py    # Local & Azure Blob storage provider semantics tests (9 tests)
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
├── scripts/                   # Automation, evaluation, and operational scripts
│   ├── evaluate_copilot.py    # Automated 8-case benchmark evaluation harness (Local & Azure)
│   ├── verify_azure_live_e2e.py # 5-scenario live Azure cloud verification suite
│   ├── test_azure_storage.py  # Live Azure Blob Storage upload/download verification
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
tests/test_storage.py (9 tests) .........                                PASSED

============================= 94 passed in 10.20s =============================
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

## 📊 Benchmark Evaluation & Quality Metrics (Milestone 10)

Milestone 10 implements an automated, reproducible benchmark evaluation harness ([`scripts/evaluate_copilot.py`](./scripts/evaluate_copilot.py)) that measures factual retrieval precision, citation accuracy, out-of-domain abstention reliability, tool selection correctness, engineering calculation accuracy, and latency profiles.

The evaluation suite executes across two distinct execution environments:
1. **Local Hermetic Mode (`--mode local`)**: Evaluates against an in-memory SQLite database, unit-normalized local embeddings, and deterministic local LLM simulation with zero external network calls or cloud dependencies.
2. **Live Azure Cloud Mode (`--mode azure`)**: Evaluates against live enterprise cloud infrastructure: Azure OpenAI Service (`gpt-4o` + `text-embedding-3-small`), Azure AI Search (`engineering-docs-index` with HNSW vector search and hybrid RRF), and Azure Database for PostgreSQL Flexible Server v16 (`psql-engcopilot-06724`).

### 1. High-Level Quality & Reliability Metrics

| Metric | Local Hermetic Mode | Live Azure Cloud Mode | Target Threshold | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Benchmark Test Pass Rate** | **100.0% (8/8)** | **100.0% (8/8)** | ≥ 95.0% | **PASSED** |
| **Grounded Citation Fidelity** | **100.0%** | **100.0%** | 100.0% | **PASSED** |
| **Out-of-Domain Abstention Precision** | **100.0%** | **100.0%** | 100.0% | **PASSED** |
| **Tool Selection Accuracy** | **100.0%** | **100.0%** | 100.0% | **PASSED** |
| **Engineering Calculation Accuracy** | **100.0%** | **100.0%** | 100.0% | **PASSED** |
| **Mean Query Latency** | **13.2 ms** | **5,682.9 ms** | < 10,000 ms (Azure) | **PASSED** |
| **Median (P50) Latency** | **8.6 ms** | **5,753.3 ms** | < 8,000 ms (Azure) | **PASSED** |
| **Minimum Latency** | **3.2 ms** | **10.0 ms** | - | **PASSED** |
| **Maximum Latency** | **32.1 ms** | **10,501.0 ms** | - | **PASSED** |
| **Total Test Suite Runtime** | **5.49 s** | **49.65 s** | - | **PASSED** |

### 2. Detailed Benchmark Test Case Results

| Case ID | Category | Technical Query | Expected Tools | Citations | Abstain? | Local (ms) | Azure (ms) | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **EVAL-A** | Factual & Unit Conversion | *"What is the maximum working pressure of CFP-402-316L in psi?"* | `search`, `calculate` | `[C1]` | No | 12.4 ms | 5,837.7 ms | **PASSED** |
| **EVAL-B** | Direct Calculation | *"Convert 75 kW to horsepower"* | `calculate` | None | No | 3.2 ms | 10.0 ms | **PASSED** |
| **EVAL-C** | Metadata Registry | *"What is the revision of the CFP-402-316L document?"* | `metadata` | `[C1]` | No | 8.6 ms | 10,501.0 ms | **PASSED** |
| **EVAL-D** | Tolerancing & GD&T | *"What is the radial bearing journal tolerance for CFP-402-316L?"* | `search` | `[C2]` | No | 8.2 ms | 5,753.3 ms | **PASSED** |
| **EVAL-E** | Out-of-Domain Abstention | *"Give me the material specification for a titanium wing spar."* | `search` | None | **Yes** | 7.9 ms | 5,322.8 ms | **PASSED** |
| **EVAL-F** | Composite Tool Chaining | *"What is the working pressure in psi?"* | `search`, `calculate` | `[C2]` | No | 14.1 ms | 5,710.5 ms | **PASSED** |
| **EVAL-G** | Citation Provenance | *"What is the recommended oil change frequency for CFP-402-316L?"* | `search` | `[C1]` | No | 18.5 ms | 6,714.3 ms | **PASSED** |
| **EVAL-H** | Missing Info Abstention | *"What is the return policy and refund procedure for this pump?"* | `search` | None | **Yes** | 8.1 ms | 5,613.3 ms | **PASSED** |

### 3. Key Reliability Insights

1. **Deterministic Unit Conversion (Zero Arithmetic Hallucination)**:
   - When converting `16.0 bar` to `psi`, the system dispatched the deterministic engineering calculator tool (`calculate_engineering`), yielding `232.06 psi` (`16.0 * 14.50377`). It never relied on LLM token probability prediction for unit calculations.
2. **Strict Abstention Precision (Zero Uncontrolled Hallucination)**:
   - In both EVAL-E (aerospace titanium query against pump specs) and EVAL-H (e-commerce return policy query against pump specs), the copilot retrieved zero chunks above relevance threshold (0.25) and returned the standardized abstention response:
     > *"The available documents do not contain enough information to answer this question."*
   - Abstention precision was 100.0% with zero speculative or hallucinated content generated.
3. **Citation Provenance & Grounding**:
   - 100% of non-abstaining responses included verifiable citation tags (`[C1]`, `[C2]`) mapped directly to the underlying document filename, page number, and section title.
4. **Context-Aware Value Extraction**:
   - In multi-step tool chaining (EVAL-F), the LangGraph planner dynamically extracted context-qualified values (e.g., *working pressure: 16.0 bar* vs *hydrostatic test pressure: 24.0 bar*) before passing arguments to subsequent tools.

### 4. Running the Benchmark Evaluation Harness

The benchmark harness can be run on-demand via the CLI:

```powershell
# Run local hermetic benchmark (in-memory SQLite + local mock; zero cloud dependencies)
python scripts/evaluate_copilot.py --mode local

# Run live Azure cloud benchmark (live Azure OpenAI + AI Search + PostgreSQL)
python scripts/evaluate_copilot.py --mode azure

# Custom output report path
python scripts/evaluate_copilot.py --mode local --output docs/evaluation-report.json
```

The complete machine-readable evaluation report is stored at [`docs/evaluation-report.json`](./docs/evaluation-report.json).

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
   - Runs `pytest backend/tests/ -v` (94 tests passing).
   - Entirely hermetic with zero cloud credentials required.
2. **`frontend-check` Job**:
   - Node.js 20 with cached npm dependencies.
   - Executes TypeScript type checking and linting (`npm run lint`).
   - Executes production build compilation (`npm run build`).
3. **`docker-validate` Job**:
   - Validates the root Docker Compose specification via `docker compose config`.
   - Builds backend and frontend test images using Buildx.

---

## ☁️ Milestone 9 — Azure Cloud Integration & Service Verification

Milestone 9 connects and verifies the Engineering Document Intelligence & CAD Knowledge Copilot against live Microsoft Azure data and AI services hosted in resource group `rg-engineering-copilot` under Azure Free Tier and low-cost development quotas. All Azure data, AI, and static frontend hosting services are live and verified, while backend Azure compute container hosting remains a future deployment step.

### 1. High-Level Azure Service Topology

```text
React Monochrome Frontend (HTTPS)
   ├── Azure Static Web Apps: https://lively-river-014b48c0f.6.azurestaticapps.net
   └── Azure Storage Static Website: https://stengcopilot06724.z13.web.core.windows.net
         │
         │  [API Requests / Reverse Proxy]
         ▼
FastAPI Copilot Backend Gateway (Local Host / Docker Compose)
   ├── Azure PostgreSQL Flexible Server (psql-engcopilot-06724.postgres.database.azure.com:5432)
   │     └── PostgreSQL 16, 7 tables, Alembic head applied (Metadata, Pages, Chunks, Sessions)
   ├── Azure Blob Storage (stengcopilot06724.blob.core.windows.net)
   │     └── Container: "documents" (Raw PDF ingestion & persistence via StorageService)
   ├── Azure AI Search (search-engineering-copilot.search.windows.net)
   │     ├── Index: "engineering-docs-index" (HNSW Vector 1536-dim + Keyword Hybrid Search)
   │     └── Index: "cad-knowledge-index" (CAD part metadata & BOM retrieval)
   └── Azure OpenAI Service (aoai-engineering-copilot-06724.openai.azure.com)
         ├── text-embedding-3-small (1536-dimensional dense vector embeddings)
         └── gpt-4o (Grounded conversational synthesis)
```

### 2. Live Azure Services Inventory

| Resource Name | Service Type & SKU | Region | Endpoint / Host | Status & Role |
| :--- | :--- | :--- | :--- | :--- |
| **`psql-engcopilot-06724`** | Azure Database for PostgreSQL Flexible Server (`Standard_B1ms`, 32GB) | `centralus` | `psql-engcopilot-06724.postgres.database.azure.com:5432` | **VERIFIED**: PostgreSQL 16 database. Applied all 7 Alembic migrations; stores documents, pages, chunks, and sessions. |
| **`aoai-engineering-copilot-06724`** | Azure OpenAI Service (`S0`) | `eastus` | `https://aoai-engineering-copilot-06724.openai.azure.com/` | **VERIFIED**: `text-embedding-3-small` (1536 dims) for dense indexing; `gpt-4o` for grounded RAG synthesis. |
| **`search-engineering-copilot`** | Azure AI Search (`Free` Tier, $0/mo) | `eastus` | `https://search-engineering-copilot.search.windows.net` | **VERIFIED**: Created `engineering-docs-index` (HNSW vector profile + searchable text) and `cad-knowledge-index`. Uses REST API 2023-11-01 `vectorQueries`. |
| **`stengcopilot06724`** | Azure Storage Account (`Standard_LRS`, StorageV2) | `eastus` | `https://stengcopilot06724.blob.core.windows.net` | **VERIFIED**: Container `documents` for raw PDF persistence via `StorageService`. Static website `$web` serving compiled React bundle. |
| **`stengcopilot06724.z13.web.core.windows.net`** | Azure Storage Static Website | `eastus` | `https://stengcopilot06724.z13.web.core.windows.net/` | **VERIFIED**: Deployed compiled React bundle (`frontend/dist`); returns HTTP 200 OK. |
| **`stapp-engineering-copilot`** | Azure Static Web Apps (`Free`) | `eastus2` | `https://lively-river-014b48c0f.6.azurestaticapps.net` | **VERIFIED**: Provisioned with deployment token for automated CI/CD static frontend delivery. |
| **`acrengcopilot06724`** | Azure Container Registry (`Basic`) | `eastus` | `acrengcopilot06724.azurecr.io` | **CONFIGURED**: Container registry for packaging and distributing Docker images. |
| **FastAPI Backend Compute Hosting** | Azure Container Apps / App Service | - | - | **NOT DEPLOYED / NOT VERIFIED**: Backend Azure compute hosting remains a future deployment step. Currently connects to all live Azure services from local / Docker runtime. |

### 3. How to Run Against Live Azure Cloud

#### Step 1: Configure Azure Environment Variables
Copy the Azure configuration template:
```powershell
Copy-Item backend/.env.azure.example backend/.env.azure
```
Populate `backend/.env.azure` with your Azure credentials (or export as shell environment variables):
```ini
DATABASE_URL=postgresql+asyncpg://copilotadmin:<password>@psql-engcopilot-06724.postgres.database.azure.com:5432/engineering_copilot?ssl=require
EMBEDDING_PROVIDER=azure
SEARCH_PROVIDER=azure
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://aoai-engineering-copilot-06724.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_SEARCH_ENDPOINT=https://search-engineering-copilot.search.windows.net
AZURE_SEARCH_API_KEY=<your-key>
AZURE_SEARCH_INDEX_NAME=engineering-docs-index
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=stengcopilot06724;AccountKey=<your-key>;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=documents
```

#### Step 2: Run Live Azure End-to-End Verification Suite
Execute the automated live verification script that exercises all 5 Azure services:
```powershell
python scripts/verify_azure_live_e2e.py
```

#### Step 3: Run FastAPI Connected to Live Azure
```powershell
# From backend/ directory with Azure environment active
.\.venv\Scripts\uvicorn.exe app.main:app --port 8000
```

### 4. Live Cloud Verification Test Suite Evidence

The test suite [`scripts/verify_azure_live_e2e.py`](./scripts/verify_azure_live_e2e.py) validates all 5 core engineering flows against live Azure services with real API calls:

```text
================================================================================
  LIVE AZURE CLOUD END-TO-END VERIFICATION
  Resource Group : rg-engineering-copilot
  PostgreSQL Host: psql-engcopilot-06724.postgres.database.azure.com
  OpenAI Endpoint: https://aoai-engineering-copilot-06724.openai.azure.com/
  Search Endpoint: https://search-engineering-copilot.search.windows.net
  Storage Account: stengcopilot06724 (container: documents)
================================================================================

[TEST 1] INGESTION & LIVE AZURE VECTOR INDEXING
  PDF Ingested   : data/sample_pump_spec.pdf (CFP-402-316L Rev D)
  Pages Extracted: 3 (2 native text, 1 OCR fallback via Tesseract)
  Blob Upload    : Uploaded raw PDF to Azure Blob Storage 'documents' container
  DB Persistence : Saved Document + 3 DocumentPages into Azure PostgreSQL Flexible Server
  Chunking       : Generated 5 structural chunks preserving engineering units
  Azure OpenAI   : Generated 5 x 1536-dim embeddings via text-embedding-3-small
  Azure AI Search: Indexed 5 chunks into 'engineering-docs-index'
  Status         : PASSED (All 5 chunks indexed into live Azure AI Search)

[TEST 2] WORKING PRESSURE QUERY (SEARCH + UNIT CONVERSION)
  Query          : "What is the maximum working pressure of CFP-402-316L in psi?"
  Tools Executed : search_engineering_documents, calculate_engineering
  Latency        : 5.48s
  Evidence Cited : [C1] sample_pump_spec.pdf (Page 1)
  Synthesized Ans: The maximum working pressure for CFP-402-316L is 16.0 bar (232 psi) at 20 C [C1].
                   Using the engineering calculation tool: 16.0 bar * 14.50377 psi/bar ~= 232.06 psi.
  Status         : PASSED (Citation [C1] verified, 232.06 psi calculation verified)

[TEST 3] DIRECT ENGINEERING CALCULATION
  Query          : "Convert 75 kW to horsepower"
  Tools Executed : calculate_engineering
  Latency        : 0.01s
  Synthesized Ans: 75.0 kW * 1.34102 hp/kW ~= 100.58 hp
  Status         : PASSED (Exact conversion 100.58 hp verified)

[TEST 4] ABSTENTION ON OUT-OF-DOMAIN QUERY
  Query          : "What is the maximum allowable stress for a titanium wing spar?"
  Tools Executed : search_engineering_documents
  Latency        : 5.34s
  Abstain Flag   : True
  Synthesized Ans: The available documents do not contain enough information to answer this question.
  Status         : PASSED (Correctly refused to hallucinate on missing domain data)

[TEST 5] METADATA LOOKUP FROM AZURE POSTGRESQL
  Query          : "What is the revision and document type of CFP-402-316L?"
  Tools Executed : get_document_metadata
  Latency        : 1.81s
  Synthesized Ans: Document 'CFP-402-316L' (sample_pump_spec.pdf) is a SPECIFICATION at Revision D,
                   currently PROCESSED with 3 pages [C1].
  Status         : PASSED (Exact revision D and document type SPECIFICATION verified)

================================================================================
  ALL 5 LIVE AZURE VERIFICATION TESTS PASSED
================================================================================
```

### 5. Cost Breakdown & Teardown

All provisioned Azure services strictly adhere to the Azure Free Trial $200 credit and free-tier allocation:

| Service | Pricing Tier | Monthly Cost Footprint |
| :--- | :--- | :--- |
| **Azure AI Search** | Free Tier | **$0.00 / month** (1 service per subscription) |
| **Azure Static Web Apps** | Free SKU | **$0.00 / month** |
| **Azure OpenAI Service** | S0 Pay-as-you-go | **<$0.05** across full verification suite |
| **Azure PostgreSQL Flexible** | Standard_B1ms (1 vCPU, 2 GiB RAM, 32 GiB storage) | **~$0.018 / hour** during active testing |
| **Azure Blob Storage** | Standard_LRS (Hot) | **<$0.01** |
| **Azure Container Registry** | Basic Tier | **~$0.167 / day** |

#### Complete Cloud Teardown
To immediately delete all resources and stop any cost accumulation, run:
```bash
az group delete --name rg-engineering-copilot --yes --no-wait
```

---

## 🎯 Portfolio Demonstration & Interview Guide

This project is packaged as a portfolio demonstration for **AI Graduate Engineer**, **AI/ML Engineer**, and **CAD Automation & Applied AI** roles (such as Atlas Copco GECIA Graduate Engineer Trainee).

Comprehensive interview and presentation materials are provided in the [`docs/`](./docs) directory:

- **[`docs/demo-script.md`](./docs/demo-script.md)**: A structured, 3-minute timed live technical demonstration walkthrough covering:
  1. *The Engineering Problem*: Why generic LLMs fail on technical specifications (hallucinated units, ignoring tolerances, lack of source page accountability).
  2. *Ingestion & OCR Pipeline*: High-resolution PDF rendering with OpenCV thresholding and Tesseract OCR fallback for scanned drawings.
  3. *Hybrid Retrieval & Grounded RAG*: BM25 exact part number matching combined with dense vector semantic search via Reciprocal Rank Fusion (RRF).
  4. *Deterministic Multi-Tool Chaining*: LangGraph agent extracting raw values (`16.0 bar`) and executing safe Python conversion tools (`232.06 psi`) instead of speculative LLM math.
  5. *Strict Abstention Defense*: Refusing to answer out-of-domain queries (e.g. titanium wing spars) when evidence is absent.
  6. *Azure Enterprise Topology*: Connecting to live cloud data and AI services while explaining why backend compute hosting remains a deliberate future deployment step.
- **[`docs/interview-notes.md`](./docs/interview-notes.md)**: Exhaustive technical interview defense notes answering 20 core engineering questions (A through T), covering:
  - *Hybrid Search vs Pure Dense Vector*: Why BM25 is mandatory for alphanumeric codes like `CFP-402-316L` and tolerance classes like `ISO h6`.
  - *Grounded RAG vs Fine-Tuning*: Why RAG was chosen over model weight modification for dynamic technical document repositories.
  - *Page-Aware Structural Chunking*: Preserving section titles, table structures, and page provenance across chunk boundaries.
  - *Prompt Injection Boundaries*: Wrapping untrusted PDF text in passive XML contexts (`<engineering_context>`) to prevent prompt hijacking.
  - *Deterministic Calculations*: Avoiding token probability arithmetic for mission-critical pressure and power conversions.
  - *Azure Architecture & Cost Decisions*: Selecting Free Tier Azure AI Search and Serverless/Flexible tiers for zero-cost standby operation.
- **[`docs/evaluation-report.json`](./docs/evaluation-report.json)**: Quantitative evaluation results from the 8-scenario benchmark test suite across both local hermetic and live Azure environments.

---

## ⚖️ Milestone Verification Status & Evidence Traceability

Every capability across the project roadmap has been cataloged with verifiable status labels:

- `[IMPLEMENTED]` — Full application code written, integrated, and validated.
- `[VERIFIED]` — Tested with automated test suites or live cloud service execution with evidence.
- `[CONFIGURED]` — Configuration or resource provisioned; awaiting container deployment.
- `[PLACEHOLDER]` — UI architectural reference schema / demo layout; underlying kernel intentionally deferred.
- `[NOT DEPLOYED / NOT VERIFIED]` — Deliberately out-of-scope or reserved for future enterprise deployment.

### Milestone Progression (M1 – M10)

| Milestone | Scope & Deliverable | Status & Verification Evidence |
| :--- | :--- | :--- |
| **M1** | Architecture & Repository Foundation | `[IMPLEMENTED] [VERIFIED]` Directory structure, async SQLAlchemy, Alembic, Pydantic schemas. |
| **M2** | FastAPI + PostgreSQL + Alembic | `[IMPLEMENTED] [VERIFIED]` Async session management, 7 database migrations, CRUD endpoints. |
| **M3** | PDF Ingestion & OCR Fallback | `[IMPLEMENTED] [VERIFIED]` PyMuPDF native extraction, OpenCV denoise/threshold, Tesseract OCR fallback. |
| **M4** | Chunking & Hybrid Retrieval Engine | `[IMPLEMENTED] [VERIFIED]` Page-aware chunker, BM25 + dense vector + Reciprocal Rank Fusion (RRF). |
| **M5** | Grounded RAG, Citations & Abstention | `[IMPLEMENTED] [VERIFIED]` XML untrusted context boundary, `[C1]` citation fidelity, standardized abstention. |
| **M6** | LangGraph Tool-Using Agent | `[IMPLEMENTED] [VERIFIED]` StateGraph workflow, search/metadata/calculator tools, multi-tool chaining. |
| **M7** | Minimal Monochrome React UI | `[IMPLEMENTED] [VERIFIED]` High-contrast typography-led UI, editorial conversation stream, citation popovers. |
| **M8** | Production Docker & CI/CD | `[IMPLEMENTED] [VERIFIED]` Multi-container Docker Compose, non-root backend, Nginx proxy, GitHub Actions. |
| **M9** | Azure Cloud Integration & Services | `[IMPLEMENTED] [VERIFIED]` Live Azure PostgreSQL Flexible, OpenAI, AI Search, Blob Storage, Static Web Apps. |
| **M10** | Final Evaluation, Polish & Portfolio Release | `[IMPLEMENTED] [VERIFIED]` 8-case benchmark harness (100% pass rate), demo script, interview notes, portfolio ready. |

### Component-Level Verification Matrix

| Component / Service | Status | Evidence & Verification Notes |
| :--- | :---: | :--- |
| **Backend Test Suite** | `[IMPLEMENTED] [VERIFIED]` | 94 hermetic tests passed in 10.20s across 9 test suites (`pytest`). |
| **Frontend Lint** | `[IMPLEMENTED] [VERIFIED]` | `npm.cmd run lint` (`tsc --noEmit`) passed with 0 errors. |
| **Frontend Production Build** | `[IMPLEMENTED] [VERIFIED]` | `npm.cmd run build` (`vite build`) passed (42 modules, 171.03 kB bundle). |
| **Docker Compose Multi-Container Stack** | `[IMPLEMENTED] [VERIFIED]` | Verified healthy on local Docker Desktop: PostgreSQL 16, FastAPI backend, React/Nginx frontend. |
| **Local Windows PostgreSQL** | `[IMPLEMENTED] [VERIFIED]` | PostgreSQL 16 verified on port 5432 with Alembic migrations and agent queries. |
| **Azure PostgreSQL Flexible Server** | `[IMPLEMENTED] [VERIFIED]` | `psql-engcopilot-06724` (PostgreSQL 16, `centralus`). Applied all 7 Alembic migrations with live table persistence. |
| **Azure OpenAI Embeddings** | `[IMPLEMENTED] [VERIFIED]` | `aoai-engineering-copilot-06724` running `text-embedding-3-small` (1536 dims). Verified live document chunk vectorization. |
| **Azure OpenAI Chat Synthesis** | `[IMPLEMENTED] [VERIFIED]` | `aoai-engineering-copilot-06724` running `gpt-4o`. Verified grounded synthesis, tool calling, citations, and abstention. |
| **Azure AI Search Hybrid Index** | `[IMPLEMENTED] [VERIFIED]` | `search-engineering-copilot` (Free Tier). Provisioned `engineering-docs-index` (HNSW vector + keyword) via REST API 2023-11-01 `vectorQueries`. |
| **Azure Blob Storage Persistence** | `[IMPLEMENTED] [VERIFIED]` | `stengcopilot06724` (container `documents`). Verified automated upload and download via `StorageService`. |
| **Azure Storage Static Website** | `[IMPLEMENTED] [VERIFIED]` | Hosted compiled React bundle on `$web` (`https://stengcopilot06724.z13.web.core.windows.net/`); returns HTTP 200 OK. |
| **Azure Static Web Apps** | `[IMPLEMENTED] [VERIFIED]` | Provisioned and active at `https://lively-river-014b48c0f.6.azurestaticapps.net` with deployment token configured. |
| **Live Azure End-to-End Suite** | `[IMPLEMENTED] [VERIFIED]` | Automated test suite (`scripts/verify_azure_live_e2e.py`) passed all 5 live test scenarios against real Azure cloud services. |
| **Evaluation Benchmark Harness** | `[IMPLEMENTED] [VERIFIED]` | Automated 8-case suite (`scripts/evaluate_copilot.py`) achieved 100% pass rate in both local (5.49s) and Azure cloud (49.65s) modes. |
| **Azure Container Registry** | `[CONFIGURED]` | Provisioned `acrengcopilot06724.azurecr.io` (Basic SKU) with admin credentials enabled. |
| **Azure Backend Compute Hosting** | `[NOT DEPLOYED / NOT VERIFIED]` | Backend Azure compute container hosting (Container Apps / App Service) was not deployed and remains a future deployment step. All live Azure data and AI services and frontend hosting are verified, with the backend running locally or in Docker connected to Azure. |
| **CAD 3D Geometry Viewer** | `[PLACEHOLDER]` | The CAD tab in the UI serves as an architectural target schema reference and demonstration wireframe. B-Rep geometry engines and WebGL renderers are deliberately reserved for future engineering extensions. |

---

## 🚀 Future Engineering Extensions (Beyond Portfolio Scope)

While Milestone 10 represents the complete, verified scope of the portfolio platform, the system was designed with clean abstraction boundaries allowing straightforward expansion into industrial CAD automation workflows:

1. **Native CAD Geometry Kernel Integration**:
   - Integration with OpenCASCADE (`pythonocc`) or FreeCAD headless API to parse raw STEP (`.stp`), IGES (`.igs`), and DXF files.
   - Extract exact boundary representation (B-Rep) topological entities, feature trees, and face-level geometric metadata directly into PostgreSQL.
2. **Interactive 3D WebGL Assembly Canvas**:
   - Client-side rendering of CAD assemblies using Three.js / React Three Fiber.
   - Bi-directional cross-referencing: clicking a part in the 3D viewport queries its specification in the copilot, while clicking a citation (`[C1]`) highlights the corresponding 3D subassembly.
3. **Automated GD&T & Standards Compliance Engine**:
   - Rule-based compliance auditing comparing extracted drawing tolerances against ISO 1101 and ASME Y14.5 geometric dimensioning and tolerancing standards.
   - Flagging out-of-spec surface finishes, missing datum references, or unsupported fit classes directly in the engineering review workflow.
4. **Azure Container Apps Production Compute Deployment**:
   - Packaging the backend image into `acrengcopilot06724.azurecr.io` and deploying to Azure Container Apps with Managed Identity authentication (eliminating connection strings).

> **Project Completion Note**: This repository represents the completed, verified **Milestone 10 — Final Evaluation, Polish & Portfolio Release**. No Milestone 11 is planned; the platform is complete, benchmarked, and ready for portfolio evaluation and technical interviews.
