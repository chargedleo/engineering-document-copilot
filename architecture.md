# Architecture: Engineering Document Intelligence & CAD Knowledge Copilot

This document outlines the architectural blueprint, component design, data flow, and technology integrations for the **Engineering Document Intelligence & CAD Knowledge Copilot**.

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
    subgraph ClientLayer["Frontend Presentation Layer (React + TS + Vite)"]
        UI["Modern Web Interface"]
        DocViewer["Document & Spec Viewer"]
        CadViewer["CAD 3D/2D Viewer Canvas"]
        ChatCopilot["Copilot Chat & Citation Inspector"]
    end

    subgraph APILayer["Backend Gateway & API Services (FastAPI)"]
        API["FastAPI App (Async)"]
        AuthMiddleware["Security & CORS Middleware"]
        DocRoutes["/api/v1/documents"]
        CadRoutes["/api/v1/cad"]
        ChatRoutes["/api/v1/chat"]
        HealthRoutes["/api/v1/health"]
    end

    subgraph ServiceLayer["Service & Business Logic Layer"]
        DocService["Document Management Service"]
        CadService["CAD Extraction & Geometry Service"]
        ChatService["Copilot Orchestration Service"]
    end

    subgraph AIEngine["AI & Reasoning Engine (Planned Integration)"]
        LangGraphAgent["LangGraph Multi-Agent Workflows"]
        AzureOpenAI["Azure OpenAI (GPT-4o / Embeddings)"]
        AzureSearch["Azure AI Search (Hybrid + Vector Index)"]
    end

    subgraph DataStorage["Data & Storage Layer"]
        PostgresDB[("PostgreSQL 16\n(Metadata, Sessions, Auditing)")]
        DocStore[("data/documents/\n(Raw Engineering Files)")]
        ProcessedStore[("data/processed/\n(Extracted Text, CAD Nodes, Chunks)")]
    end

    UI --> API
    API --> DocRoutes & CadRoutes & ChatRoutes & HealthRoutes
    DocRoutes --> DocService
    CadRoutes --> CadService
    ChatRoutes --> ChatService

    DocService --> PostgresDB
    DocService --> DocStore
    CadService --> ProcessedStore

    ChatService --> LangGraphAgent
    LangGraphAgent --> AzureOpenAI
    LangGraphAgent --> AzureSearch
    LangGraphAgent --> PostgresDB
```

---

## 3. Core Subsystems

### 3.1 Frontend Subsystem (React + TypeScript + Vite)
- **Role**: Provides the engineering user interface for uploading files, browsing documents, inspecting extracted CAD structures, and conversing with the copilot.
- **Key Modules**:
  - `components/layout/`: Main application navigation, sidebar, and status indicators.
  - `components/documents/`: Document lists, upload dropzone, processing status tags.
  - `components/cad/`: Interactive CAD tree view and model placeholder.
  - `components/chat/`: Conversational interface supporting multi-turn dialogue, markdown formatting, and source citation cards.
  - `services/`: Axios/Fetch API client abstractions with strong TypeScript typings.

### 3.2 Backend Subsystem (FastAPI)
- **Role**: High-performance asynchronous REST API handling file processing, metadata storage, session persistence, and routing agent actions.
- **Key Layers**:
  - `core/`: Environment settings (Pydantic `BaseSettings`), database connection pool management via async SQLAlchemy, and structured logging.
  - `api/v1/`: Versioned API routing with validated request and response envelopes.
  - `models/`: Database entities for documents, CAD metadata nodes, chat sessions, and message history.
  - `schemas/`: Pydantic models for validation, serialization, and OpenAPI documentation generation.
  - `services/`: Encapsulated domain business logic decoupled from HTTP transport.

### 3.3 Data Storage & Persistence
- **PostgreSQL 16**:
  - `documents`: Stores document records, checksums, mime types, file sizes, and processing statuses.
  - `cad_metadata`: Stores parsed CAD assembly parts, materials, mass properties, and dimensions.
  - `chat_sessions` & `chat_messages`: Stores multi-turn user conversations, generated responses, token metrics, and citations.
- **Filesystem Storage**:
  - `data/documents/`: Secure staging area for original engineering documents and CAD files.
  - `data/processed/`: Extracted text, normalized JSON CAD trees, generated previews, and cached chunks.

### 3.4 Search & Embeddings Engine (Milestone 4 Implemented)
- **Embedding Layer**:
  - Abstract interface `BaseEmbeddingProvider` with factory pattern (`get_embedding_provider`).
  - `LocalMockEmbeddingProvider`: Deterministic token-hash random projection generating unit-normalized 1536-dimensional dense vectors offline without API keys or cloud dependencies.
  - `AzureOpenAIEmbeddingProvider`: Production integration connecting to Azure OpenAI (`text-embedding-3-large`).
- **Hybrid Search Engine**:
  - Abstract interface `BaseSearchIndex` with factory pattern (`get_search_index`).
  - `LocalSearchIndex`: In-process hybrid search engine supporting BM25 lexical keyword matching, cosine vector similarity, and Reciprocal Rank Fusion (RRF).
  - `AzureSearchIndex`: Production cloud integration targeting Azure AI Search REST API.
  - **Reciprocal Rank Fusion (RRF)**:
    $$RRF(d) = \sum_{m \in \{\text{keyword}, \text{vector}\}} \frac{1}{60 + \text{rank}_m(d)}$$
  - Metadata filtering: Granular filtering by `document_id`, `document_type`, `part_number`, `revision`, and `page_number`.

### 3.5 Grounded Retrieval-Augmented Generation (RAG) (Milestone 5 Implemented)
- **Dual LLM Provider Layer**:
  - Abstract interface `BaseLLMProvider` with factory pattern (`get_llm_provider`).
  - `LocalMockChatProvider`: Offline deterministic mock provider delivering grounded synthesis, unit/tolerance preservation, citation linking (`[C1]`, `[C2]`), and standard abstention without cloud credentials.
  - `AzureOpenAIChatProvider`: Production cloud integration using official REST endpoints (`AZURE_OPENAI_CHAT_DEPLOYMENT` / `gpt-4o`).
  - Provider auto-detection: selects `azure_openai` if endpoint and credentials exist; falls back to `local_mock` seamlessly.
- **Context Assembly & Prompt Isolation**:
  - `ContextBuilder`: Assembles retrieved candidate chunks above relevance threshold (`RAG_RELEVANCE_THRESHOLD`) into structured evidence blocks wrapped in `<engineering_context>`.
  - Untrusted Data Boundary: Document text is explicitly isolated as untrusted data to immunize synthesis against prompt injections embedded in PDFs.
- **Strict Grounding & Citation Extraction**:
  - In-text citation tags (`[C1]`, `[C2]`) mapped directly to `CitationItem` metadata (`document_id`, `filename`, `page_number`, `chunk_id`, `chunk_index`, `part_number`, `revision`, `section`, `snippet`).
  - Explicit Abstention: When evidence is insufficient or missing, cleanly returns standard response (`"The available documents do not contain enough information to answer this question."`) with `sufficient_evidence=False` and empty citations.
- **REST API & CLI**:
  - `POST /api/v1/rag/query` exposing grounded engineering question-answering.
  - `scripts/query_rag.py` providing interactive CLI querying with formatted citations.

### 3.6 LangGraph Engineering Copilot Agent (Milestone 6 Implemented)
- **Agent Workflow & State Machine**:
  - Built with [LangGraph](https://python.langchain.com/docs/langgraph) using a typed `CopilotAgentState` (`TypedDict`).
  - Genuine tool-using agent architecture executing explicit, validated tool calls instead of a single unconstrained retrieval step.
  - Topology: `START -> classify_and_plan -> execute_tools (conditional) -> synthesize_answer -> END`.

```text
                     ┌─────────────────────┐
                     │ LangGraph Agent     │
                     │                     │
User Query ─────────→│ Decide / Route      │
                     └─────────┬───────────┘
                               │
                  ┌────────────┼─────────────┐
                  ↓            ↓             ↓
             Search Tool   Metadata Tool   Calculator
                  │            │             │
                  └────────────┼─────────────┘
                               ↓
                        Tool Results
                               ↓
                       Grounded LLM
                               ↓
                       Final Response
                               ↓
                     Citations + Trace
```

- **Tools Suite**:
  1. `SearchEngineeringDocumentsTool`: Wraps the existing M4 hybrid retrieval service (BM25 + Dense Vectors + RRF). Preserves page provenance, document ID, filename, chunk index, revision, section, and relevance score.
  2. `GetDocumentMetadataTool`: Retrieves verified document metadata from PostgreSQL (`Document` entity) including filename, document type, part number, revision, status, page count, and file size.
  3. `EngineeringCalculatorTool`: Safe, deterministic engineering conversion tool supporting `bar_to_psi`, `psi_to_bar`, `celsius_to_fahrenheit`, `fahrenheit_to_celsius`, `flow_m3h_to_lpm`, `flow_lpm_to_m3h`, `kw_to_hp`, `hp_to_kw`, and `percentage_change`. Never uses `eval()`.
- **Multi-Tool Composite Chaining**:
  - Supports queries requiring both document evidence and calculation (e.g., retrieving operating pressure in bar from specifications, then converting to psi).
  - Citations are strictly attached to document-derived facts, while calculated values are transparently labeled as tool evaluations.
- **Untrusted Context Boundary**:
  - Retrieved document contents are isolated as passive untrusted data inside `<engineering_context>`. Malicious prompt-injection instructions embedded in PDFs cannot hijack agent routing or execute unauthorized tools.
- **Standardized Abstention**:
  - Reuses the M5 grounding philosophy. When evidence is insufficient or missing, returns `"The available documents do not contain enough information to answer this question."` with `should_abstain = True`.
- **REST API & CLI**:
  - `POST /api/v1/agent/query`: Exposes autonomous agent answering with tool execution traces.
  - `scripts/query_agent.py`: Interactive CLI demonstration tool.

> [!NOTE]
> Azure OpenAI remains an adapter/configuration option and is not considered live-tested unless credentials and deployment were actually used. Local development and automated testing execute against the deterministic `LocalMockChatProvider`.

### 3.7 CAD Extension (Future Milestone 7)
- **CAD Geometry Engine**: STEP/DXF metadata extraction, BOM cross-referencing, and 3D visual integration.

---

## 4. Document Intelligence, Hybrid Search & Grounded RAG Pipeline (Milestones 3, 4, 5 & 6 Implemented)

```mermaid
flowchart TD
    Upload["Engineering PDF Upload\n(POST /api/v1/documents/upload)"] --> Validation["PDF Validation\n(%PDF- Header, Size <= 50MB, Pages <= 500)"]
    Validation --> LocalStore["Local File Storage\n(data/documents/{document_id}/{filename})"]
    LocalStore --> PyMuPDF["PyMuPDF (fitz)\nPage-by-Page Extraction"]
    PyMuPDF --> Heuristic{"Native Text\nSufficient?\n(>= 50 chars)"}

    Heuristic -- Yes --> NativePath["Native Text Normalized\nextraction_method: text\nocr_used: false"]
    Heuristic -- No (Scanned) --> Render["Render Page Image\n(300 DPI via fitz Matrix)"]

    Render --> CV2["OpenCV Preprocessing\n(Grayscale + Denoise + Otsu)"]
    CV2 --> OCR["Tesseract OCR Engine\nextraction_method: ocr\nocr_used: true"]

    NativePath --> SavePage["Persist DocumentPage Record\n(page_number, char_count, word_count)"]
    OCR --> SavePage

    SavePage --> PostgresPages[("PostgreSQL 16\n(document_pages table)")]
    PostgresPages --> Chunking["Engineering Document Chunker\n(Preserves Headings, Units, Tolerances)"]

    Chunking --> EmbeddingGen["Generate Dense Embeddings\n(1536-dim via LocalMock / Azure OpenAI)"]
    EmbeddingGen --> SaveChunks[("PostgreSQL 16\n(document_chunks table)")]
    SaveChunks --> IndexSearch["Hybrid Search Index\n(BM25 + Dense Vectors + RRF)"]

    subgraph M6AgentPipeline["Milestone 6: LangGraph Agent Orchestrator"]
        UserQ["User Technical Query\n(POST /api/v1/agent/query or query_agent.py)"] --> Planner["classify_and_plan Node\n(Detects Search, Metadata, Calc, Multi-Tool)"]
        Planner --> Dispatch{"Tools Needed?"}
        Dispatch -- Yes --> ExecTools["execute_tools Node"]
        Dispatch -- No --> Synthesize["synthesize_answer Node"]
        ExecTools --> Tool1["Search Tool\n(Hybrid RRF)"]
        ExecTools --> Tool2["Metadata Tool\n(PostgreSQL Document)"]
        ExecTools --> Tool3["Calculator Tool\n(Deterministic Units)"]
        Tool1 & Tool2 & Tool3 --> Synthesize
        Synthesize --> AgentOutput["Agent Response\n(Grounded Answer + Citations + Tool Traces)"]
    end

    IndexSearch -.-> Tool1
    PostgresPages -.-> Tool2

    subgraph FuturePhases["Future Milestones (Strictly Decoupled)"]
        CAD["CAD Geometry Engine (Milestone 7)"]
    end

    AgentOutput -.-> FuturePhases
```

---

## 5. Security & Production Principles

1. **Strict Secret Isolation**: No API keys or credentials committed to source code; managed via `.env` and secret stores.
2. **Path Traversal Protection**: Uploaded filenames are sanitized with basename isolation to prevent directory traversal attacks (`../../`).
3. **Information Disclosure Prevention**: Global exception handlers redact absolute filesystem paths, database connection strings, and stack traces from API responses.
4. **Untrusted Context Isolation**: Retrieved document text is treated strictly as passive, untrusted data wrapped in XML boundaries to defend against prompt injections.
5. **Deterministic Tool Execution**: The engineering calculator uses explicit operation dispatch and never uses `eval()`, preventing arbitrary code execution.
6. **Async I/O**: Asynchronous database and HTTP calls to prevent blocking the event loop during heavy concurrent workloads.
7. **Structured Logging**: Contextual logs with query tokens, hit counts, latency, and tool traces without logging raw sensitive engineering documents.
8. **Graceful Degradation**: Dual provider architecture allows local development and automated testing with zero cloud credentials, automatically promoting to Azure OpenAI and Azure AI Search when credentials are provided.

---

## 6. Implementation Status & Milestone Roadmap

| Milestone | Scope & Capabilities | Status |
| :--- | :--- | :--- |
| **Milestone 1** | Repository structure, project scaffolding, base types, Docker templates. | Completed |
| **Milestone 2** | **Backend Foundation**: Asynchronous FastAPI, layered Service architecture, async SQLAlchemy 2.0 with PostgreSQL, bidirectional Alembic migrations, foundational Document metadata API (`GET`, `POST`), structured error handlers, and hermetic automated pytest suite. Azure OpenAI & AI Search configurations are decoupled and optional. | Completed |
| **Milestone 3** | **Document Intelligence Pipeline**: Page-by-page PDF processing with PyMuPDF, scanned page detection heuristic, OpenCV image preprocessing, Tesseract OCR fallback, 1-based `DocumentPage` persistence in PostgreSQL, file upload endpoint (`POST /upload`), page retrieval APIs (`GET /pages`, `GET /pages/{num}`), CLI ingestion tool (`ingest_cad_docs.py`), and 24 passing automated tests. | Completed |
| **Milestone 4** | **Document Chunking & Hybrid Vector Search**: Structural/semantic engineering chunker preserving engineering notation, tolerances, units, and page provenance; 1536-dimensional vector embedding architecture with deterministic offline mock and Azure OpenAI client; hybrid BM25 + vector search engine with Reciprocal Rank Fusion (RRF); `DocumentChunk` schema and Alembic migrations; chunk generation and search API endpoints (`/chunks/generate`, `/chunks`, `/search`); CLI retrieval tool (`search_docs.py`); and 41 passing automated tests. | Completed |
| **Milestone 5** | **Retrieval-Augmented Generation (RAG)**: Grounded question-answering system combining hybrid retrieval with LLM synthesis; dual LLM provider layer (`BaseLLMProvider`, `LocalMockChatProvider`, `AzureOpenAIChatProvider`); structured evidence context assembly with citation tagging (`[C1]`, `[C2]`); strict unit/tolerance/part-number fidelity; prompt injection defense with untrusted context isolation; explicit abstention protocol (`sufficient_evidence=False`); REST endpoint `POST /api/v1/rag/query`; CLI tool `scripts/query_rag.py`; and 56 passing automated tests. | Completed |
| **Milestone 6** (Current) | **LangGraph Engineering Copilot Agent**: Autonomous stateful agent workflow orchestrated with LangGraph; genuine tool usage across three tools (`search_engineering_documents`, `get_document_metadata`, and safe `calculate_engineering`); multi-tool chaining for technical queries requiring calculation; citation provenance preservation; prompt-injection containment; standardized abstention; REST API `POST /api/v1/agent/query`; CLI tool `scripts/query_agent.py`; and 77 passing automated tests. | Completed |
| **Milestone 7** | **CAD Extension**: STEP/DXF metadata extraction, BOM cross-referencing, and 3D visual integration. | Planned |


