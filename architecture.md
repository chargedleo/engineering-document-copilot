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

### 3.4 AI Orchestration & Search Engine (Planned Integration)
- **LangGraph**:
  - State machine-based multi-agent orchestration.
  - Routes complex queries across hybrid search, CAD metadata lookup, and synthesis agents.
  - Enables human-in-the-loop validation for engineering change recommendations.
- **Azure OpenAI**:
  - Language Model: `gpt-4o` for deep technical synthesis and engineering reasoning.
  - Embedding Model: `text-embedding-3-large` for dense semantic representation.
- **Azure AI Search**:
  - Hybrid search combining BM25 keyword matching and dense vector search with Semantic Re-ranking.
  - Separate indexes for text documents and CAD metadata/assembly nodes.

---

## 4. End-to-End Ingestion & Query Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Engineer as Engineering User
    participant Frontend as React Frontend
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant Search as Azure AI Search
    participant Agent as LangGraph Copilot

    Note over Engineer,API: 1. Ingestion Phase
    Engineer->>Frontend: Upload Engineering Doc / CAD File
    Frontend->>API: POST /api/v1/documents/upload
    API->>DB: Record Document Entry (Status: PENDING)
    API-->>Frontend: 202 Accepted (doc_id)

    Note over API,Search: Background Processing (scripts/ingest_cad_docs.py)
    API->>DB: Update Status: COMPLETED

    Note over Engineer,Agent: 2. Query & Copilot Reasoning Phase
    Engineer->>Frontend: Ask: "What are the tolerance limits for Part #402?"
    Frontend->>API: POST /api/v1/chat/query
    API->>Agent: Run Copilot Graph (State + History)
    Agent->>Search: Hybrid Vector + Keyword Query
    Search-->>Agent: Matched Document Chunks & CAD Nodes
    Agent->>Agent: Synthesize Technical Answer with Citations
    Agent-->>API: Copilot Response + Citations + CAD References
    API->>DB: Save Message & Citation Logs
    API-->>Frontend: 200 OK (Answer & References)
    Frontend-->>Engineer: Render Response with interactive citations
```

---

## 5. Security & Production Principles

1. **Strict Secret Isolation**: No API keys or credentials committed to source code; managed via `.env` and secret stores.
2. **Async I/O**: Asynchronous database and HTTP calls to prevent blocking the event loop during heavy concurrent workloads.
3. **Structured Logging**: JSON-formatted logs with request correlation IDs for end-to-end traceability.
4. **Data Isolation**: Raw uploads and processed outputs are stored with deterministic hashing to avoid duplicate indexing and filename collisions.

---

## 6. Implementation Status & Milestone Roadmap

| Milestone | Scope & Capabilities | Status |
| :--- | :--- | :--- |
| **Milestone 1** | Repository structure, project scaffolding, base types, Docker templates. | Completed |
| **Milestone 2** (Current) | **Backend Foundation**: Asynchronous FastAPI, layered Service architecture, async SQLAlchemy 2.0 with PostgreSQL, bidirectional Alembic migrations, foundational Document metadata API (`GET`, `POST`), structured error handlers, and hermetic automated pytest suite. Azure OpenAI & AI Search configurations are decoupled and optional. | Completed |
| **Milestone 3** | **Document Processing Pipeline**: Ingestion of engineering PDFs, text extraction, page-level chunking, and embedding generation. | Planned |
| **Milestone 4** | **Hybrid Vector Search & RAG**: Azure AI Search indexing, vector similarity, and keyword filtering. | Planned |
| **Milestone 5** | **LangGraph Copilot Agent**: Multi-turn dialogue, citation generation, and verification loop. | Planned |
| **Milestone 6** | **CAD Extension**: STEP/DXF metadata extraction, BOM cross-referencing, and visual integration. | Planned |

