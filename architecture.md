# Architecture: Engineering Document Intelligence & CAD Knowledge Copilot

This document outlines the architectural blueprint, component design, data flow, container orchestration, and technology integrations for the **Engineering Document Intelligence & CAD Knowledge Copilot**.

---

## 1. System Overview

Engineering organizations handle heterogeneous documentation:
1. **Unstructured Documents**: Requirements specifications, regulatory compliance standards, operation & maintenance manuals, test reports, and datasheets (PDF, DOCX, XLSX).
2. **CAD & Geometric Models**: 2D drawings (DXF, DWG) and 3D assembly models (STEP, IGES, STL, Parasolid), containing geometric hierarchies, Bill of Materials (BOM), tolerance annotations, and engineering attributes.

The Copilot is engineered to bridge the semantic gap between textual specifications and CAD models, providing engineers with interactive question answering, automated compliance validation, BOM cross-referencing, and visual model navigation.

---

## 2. High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph ClientLayer["Frontend Presentation Layer (React + TS + Vite / Nginx)"]
        UI["Minimal Monochrome Web Interface\n(Linear / Vercel Aesthetic)"]
        DocViewer["Document & Spec Registry"]
        CadViewer["CAD 2D/3D Viewport Canvas"]
        ChatCopilot["Copilot Editorial Stream & Tool Logs"]
    end

    subgraph APILayer["Backend Gateway & Container Services (FastAPI + Uvicorn)"]
        API["FastAPI Async App"]
        AuthMiddleware["Security & CORS Middleware"]
        DocRoutes["/api/v1/documents"]
        SearchRoutes["/api/v1/search"]
        RagRoutes["/api/v1/rag"]
        AgentRoutes["/api/v1/agent"]
        CadRoutes["/api/v1/cad"]
        ChatRoutes["/api/v1/chat"]
        HealthRoutes["/api/v1/health & /ready"]
    end

    subgraph ServiceLayer["Service & Business Logic Layer"]
        DocService["Document Management Service"]
        OcrService["PyMuPDF + Tesseract OCR Pipeline"]
        ChunkService["Engineering Structural Chunker"]
        SearchService["Hybrid Retrieval Engine (BM25 + Dense RRF)"]
        RagService["Grounded RAG & Citation Engine"]
        AgentService["LangGraph Agent Orchestration Service"]
    end

    subgraph LangGraphWorkflow["LangGraph Tool Execution Graph"]
        Planner["classify_and_plan"]
        Executer["execute_tools"]
        Synthesizer["synthesize_answer"]
        ToolSearch["search_engineering_documents"]
        ToolMeta["get_document_metadata"]
        ToolCalc["calculate_engineering"]
    end

    subgraph DataStorage["Data & Persistence Layer"]
        PostgresDB[("PostgreSQL 16\n(Metadata, Pages, Chunks, Sessions)")]
        DocStore[("data/documents/\n(Raw Engineering Files)")]
        ProcessedStore[("data/processed/\n(Extracted Text, CAD Nodes, Chunks)")]
    end

    UI --> API
    API --> DocRoutes & SearchRoutes & RagRoutes & AgentRoutes & CadRoutes & ChatRoutes & HealthRoutes
    DocRoutes --> DocService
    DocService --> OcrService --> ChunkService
    SearchRoutes --> SearchService
    RagRoutes --> RagService
    AgentRoutes --> AgentService
    AgentService --> Planner --> Executer --> Synthesizer
    Executer --> ToolSearch & ToolMeta & ToolCalc

    DocService --> PostgresDB
    DocService --> DocStore
    ChunkService --> ProcessedStore & PostgresDB
    ToolSearch --> SearchService
    ToolMeta --> PostgresDB
    SearchService --> PostgresDB
```

---

## 3. Core Subsystems

### 3.1 Frontend Subsystem (React + TypeScript + Vite / Nginx)
- **Role**: Provides the editorial monochrome engineering interface for uploading files, browsing document registries, querying the autonomous copilot, and inspecting citations and calculation sheets.
- **Key Modules**:
  - `components/layout/`: Header, Navigation Tabs, and live backend connection heartbeat monitor.
  - `components/chat/`: Editorial document-style conversation streams, technical citations (`[C1]`), typographic calculation sheets, and compact technical tool logs.
  - `components/documents/`: Document registry table, upload dropzone, processing status tags, and metadata details.
  - `components/cad/`: Interactive CAD tree view and model placeholder.
  - `services/`: Axios/Fetch API client abstractions with unified TypeScript typings and automatic `/api` routing.
- **Production Containerization**: Multi-stage Docker build (`node:20-alpine` build -> `nginx:alpine` runtime). Nginx handles client-side SPA routing (`try_files $uri $uri/ /index.html;`), proxies `/api/` requests to backend service, provides 50MB request body limits for PDF uploads, and enforces security headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`).

### 3.2 Backend Subsystem (FastAPI)
- **Role**: High-performance asynchronous REST API handling file processing, metadata storage, session persistence, OCR fallback, hybrid search, and LangGraph agent execution.
- **Key Layers**:
  - `core/`: Environment settings (Pydantic `BaseSettings`), database connection pool management via async SQLAlchemy 2.x, and structured logging.
  - `api/v1/`: Versioned API routing with validated request and response envelopes.
  - `models/`: Database entities for documents, document pages, document chunks, CAD metadata nodes, and chat sessions.
  - `schemas/`: Pydantic models for validation, serialization, and OpenAPI documentation generation.
  - `services/`: Encapsulated domain business logic decoupled from HTTP transport.
  - `agents/`: LangGraph `StateGraph` workflow with deterministic planner, tool executor, and citation synthesizer.
- **Production Containerization**: Python 3.11 slim image running as unprivileged user `appuser` (UID 1000). System libraries installed for Tesseract OCR (`tesseract-ocr`, `tesseract-ocr-eng`) and OpenCV headless rendering (`libgl1`, `libglib2.0-0`). Managed startup via `entrypoint.sh` executing database connectivity verification and Alembic schema migrations (`alembic upgrade head`).

### 3.3 Data Storage & Persistence
- **PostgreSQL 16**:
  - `documents`: Stores document records, checksums, mime types, file sizes, and processing statuses.
  - `document_pages`: Stores 1-based page records with native text, OCR flag, and image metrics.
  - `document_chunks`: Stores structural engineering chunks with tokens, headings, units, and dense vector embeddings.
  - `cad_metadata`: Stores parsed CAD assembly parts, materials, mass properties, and dimensions.
  - `chat_sessions` & `chat_messages`: Stores multi-turn user conversations, generated responses, token metrics, and citations.
- **Filesystem Storage**:
  - `data/documents/`: Staging area for original engineering documents and CAD files.
  - `data/processed/`: Extracted text, normalized JSON CAD trees, generated previews, and cached chunks.

---

## 4. End-to-End Information & Reasoning Flow

### 4.1 Document Intelligence & Ingestion Pipeline
```text
PDF Upload / Ingestion
        ↓
PyMuPDF Text Extraction & Structure Analysis
        ↓
Native Text Check (Char count >= 50 per page)
   ├── [Native Text Sufficient] ──> Save DocumentPage
   └── [Scanned / Drawing] ──────> OpenCV Image Preprocessing
                                         ↓
                                   Tesseract OCR Engine
                                         ↓
                                   Save DocumentPage (is_ocr=True)
        ↓
Engineering Structural Chunker (Preserves Units, Tolerances, Headings)
        ↓
Dense Vector Generation (1536-dim via LocalMock / Azure OpenAI)
        ↓
Persist DocumentChunk (PostgreSQL document_chunks table)
        ↓
Indexed for Hybrid Retrieval (BM25 + Cosine Vector + Reciprocal Rank Fusion)
```

### 4.2 Autonomous Agent & Tool Reasoning Flow
```text
User Technical Query (e.g. "What is the max working pressure of CFP-402-316L in psi?")
        ↓
LangGraph Agent Workflow (classify_and_plan Node)
        ↓
Tool Planning & Dispatch
   ├── Tool 1: search_engineering_documents ("CFP-402-316L working pressure")
   │      └── Hybrid Search: BM25 + Vector RRF ──> Finds 16.0 bar in Page 1 chunk [C1]
   └── Tool 2: calculate_engineering (operation="bar_to_psi", input=16.0)
          └── Safe Unit Converter ──> 16.0 bar * 14.50377 = 232.06 psi
        ↓
Grounded Synthesis Node (Untrusted Context XML Boundary)
        ↓
Editorial Response: "The maximum working pressure for CFP-402-316L is 16.0 bar [C1], corresponding to 232.06 psi."
        ↓
React Monochrome UI (Live Citation Reference + Tool Traces)
```

---

## 5. Production Containerization & Deployment Topology (Milestone 8)

The application provides a containerized orchestration architecture using Docker Compose:

```mermaid
flowchart LR
    ClientBrowser["Web Browser\n(:5173 / :80)"] -->|HTTP / SPA /api| NginxFront["engineering_copilot_frontend\n(Nginx:alpine)"]
    NginxFront -->|Reverse Proxy :8000| FastApiBack["engineering_copilot_backend\n(FastAPI / Python 3.11-slim)"]
    FastApiBack -->|SQLAlchemy Async :5432| PostgresContainer["engineering_copilot_db\n(PostgreSQL 16-alpine)"]

    FastApiBack -.->|Bind Mount| VolDocs["./data/documents"]
    FastApiBack -.->|Bind Mount| VolProc["./data/processed"]
    PostgresContainer -.->|Named Volume| VolDb["postgres_data"]
```

### 5.1 Service Matrix & Responsibilities

| Service | Image | Internal Port | Host Port | Role & Configuration |
| :--- | :--- | :--- | :--- | :--- |
| **`postgres`** | `postgres:16-alpine` | `5432` | `5432` | PostgreSQL database with persistent named volume `postgres_data` and built-in healthcheck (`pg_isready`). |
| **`backend`** | Custom build (`backend/Dockerfile`) | `8000` | `8000` | FastAPI server running as non-root `appuser`. Managed by `entrypoint.sh` which awaits database readiness and applies `alembic upgrade head`. Built-in healthcheck (`curl /api/v1/health`). |
| **`frontend`** | Custom build (`frontend/Dockerfile`) | `80` | `5173` | Multi-stage build (`node:20-alpine` -> `nginx:alpine`). Serves compiled React assets, proxies `/api/` to backend, handles SPA fallbacks, and executes lightweight healthchecks. |

### 5.2 Container Security & Operational Principles
1. **Unprivileged Non-Root Execution**: Backend container creates and runs under `appuser:appgroup` (UID 1000), eliminating root privilege container escalation risks.
2. **Minimal Layer Attack Surface**: Multi-stage frontend build eliminates `node_modules` and compilation toolchains from runtime images.
3. **Hermetic Secret Management**: Zero credentials or secrets baked into images; configuration is completely environment-driven via `.env` and Docker Compose variables.
4. **Deterministic Migration Sequencing**: Startup race conditions between database and backend are resolved through container dependency conditions (`condition: service_healthy`) and entrypoint connection verification before applying Alembic migrations.
5. **Dual Local / Container Workflow**: Native Windows PostgreSQL 16 development remains completely supported alongside Docker Compose with zero codebase modifications.
6. **Automated CI Validation**: Continuous integration via GitHub Actions (`.github/workflows/ci.yml`) validates the entire test suite, frontend linting, production building, and Docker Compose configurations on every push and pull request.

---

## 6. Implementation Status & Milestone Roadmap

| Milestone | Scope & Capabilities | Status |
| :--- | :--- | :--- |
| **Milestone 1** | Repository structure, project scaffolding, base types, Docker templates. | Completed |
| **Milestone 2** | **Backend Foundation**: Asynchronous FastAPI, layered Service architecture, async SQLAlchemy 2.0 with PostgreSQL, bidirectional Alembic migrations, foundational Document metadata API (`GET`, `POST`), structured error handlers, and hermetic automated pytest suite. | Completed |
| **Milestone 3** | **Document Intelligence Pipeline**: Page-by-page PDF processing with PyMuPDF, scanned page detection heuristic, OpenCV image preprocessing, Tesseract OCR fallback, 1-based `DocumentPage` persistence in PostgreSQL, file upload endpoint (`POST /upload`), and page retrieval APIs. | Completed |
| **Milestone 4** | **Document Chunking & Hybrid Vector Search**: Structural/semantic engineering chunker preserving engineering notation, tolerances, units, and page provenance; 1536-dimensional vector embedding architecture; hybrid BM25 + vector search engine with Reciprocal Rank Fusion (RRF); `DocumentChunk` schema and Alembic migrations. | Completed |
| **Milestone 5** | **Retrieval-Augmented Generation (RAG)**: Grounded question-answering system combining hybrid retrieval with LLM synthesis; dual LLM provider layer (`BaseLLMProvider`, `LocalMockChatProvider`, `AzureOpenAIChatProvider`); structured evidence context assembly with citation tagging (`[C1]`); prompt injection defense; and explicit abstention protocol. | Completed |
| **Milestone 6** | **LangGraph Engineering Copilot Agent**: Autonomous stateful agent workflow orchestrated with LangGraph; genuine tool usage across three tools (`search_engineering_documents`, `get_document_metadata`, and safe `calculate_engineering`); multi-tool chaining for technical queries requiring calculation; citation provenance preservation; and standardized abstention. | Completed |
| **Milestone 7** | **Visual Design System**: Complete frontend transformation adhering to strict monochrome aesthetic (Linear, Vercel, Google Antigravity). Editorial conversation streams, typographic calculation result blocks, bordered citation references, compact technical tool logs, live backend health monitoring, and zero accent colors or cartoon AI decorations. | Completed |
| **Milestone 8** (Current) | **Productionization & Container Orchestration**: Production-grade Docker Compose architecture (`postgres:16-alpine`, Python 3.11-slim backend with system OCR and non-root execution, multi-stage Node 20 / Nginx Alpine frontend), automated startup migration handling (`entrypoint.sh`), `.dockerignore` file hygiene, environment variable categorization, health checks, GitHub Actions CI pipeline (`.github/workflows/ci.yml`), and 85 passing tests. | Completed |
| **Milestone 9** | **CAD Extension**: STEP/DXF geometric parser, 3D WebGL viewport canvas, and BOM cross-referencing. | Planned |
| **Milestone 10** | **Azure Cloud Deployment**: Azure App Service / Azure Container Apps, Azure PostgreSQL Flexible Server, Azure AI Search live integration, and Azure OpenAI production models. | Planned |
