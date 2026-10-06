# Engineering Copilot — 3-Minute Live Interview Demo Script

This script provides a concise, structured 3-minute technical walkthrough designed for an AI Engineering / CAD Automation interview (e.g. Atlas Copco GECIA Graduate Engineer Trainee).

---

## ⏱️ Timeline & Talking Points

### 1. Problem (20 seconds)
> *"Engineering teams deal with dense, heterogeneous documentation — technical specifications, compliance manuals, tolerances, and drawings. Generic LLMs hallucinate numbers, miscalculate unit conversions, and lack provenance back to engineering drawings. This Copilot solves that by combining page-aware OCR, hybrid retrieval, deterministic tool calculation, and grounded citations."*

### 2. Architecture & Tech Stack (30 seconds)
> *"The backend is built with FastAPI, SQLAlchemy 2.0 async, and PostgreSQL. Multi-tool orchestration is powered by a compiled LangGraph StateGraph. The frontend is a minimal, high-contrast monochrome React/TypeScript SPA inspired by Linear and Vercel. For deployment, we support both a fully hermetic local environment and verified live integrations with Azure OpenAI, Azure AI Search, and Azure PostgreSQL Flexible Server."*

### 3. Upload & Document Pipeline (30 seconds)
> *"When a technical specification is uploaded — such as `sample_pump_spec.pdf` — the ingestion engine validates the PDF header, extracts selectable text with PyMuPDF, and automatically falls back to OpenCV image preprocessing and Tesseract OCR for scanned drawings. Text is chunked with engineering-aware boundaries preserving tolerances and units, embedded into 1536-dimensional vectors, and indexed into hybrid BM25 + dense vector storage."*

### 4. Technical Question Answering (45 seconds)
> **Action:** In the Workspace, click starter or enter:
> ```text
> What is the maximum working pressure of CFP-402-316L in psi?
> ```
> **Talking Point:**
> *"Notice the multi-step execution trace: the LangGraph agent plans two tools. First, `search_engineering_documents` retrieves Chunk 1 on Page 1, identifying the working pressure as 16.0 bar. Rather than allowing the LLM to guess the psi conversion, the planner chains that extracted value into `calculate_engineering` (`bar_to_psi`), deterministically yielding 232.06 psi. The synthesized answer displays the exact value with an in-text citation `[C1]`."*

### 5. Deterministic Unit Calculation Tool (30 seconds)
> **Action:** In the Workspace, click starter or enter:
> ```text
> Convert 75 kW to horsepower
> ```
> **Talking Point:**
> *"Here, the agent recognizes a pure calculation request. It bypasses document search, calls `calculate_engineering` with `kw_to_hp` at 75 kW, and returns exactly 100.58 hp in under 10 milliseconds. LLMs frequently make subtle rounding mistakes on unit conversions; isolating math into deterministic code guarantees engineering reliability."*

### 6. Grounded Citations & Evidence Boundaries (30 seconds)
> **Action:** Expand citation card `[C1]` on the previous response.
> **Talking Point:**
> *"Every answer is bounded by an `<engineering_context>` evidence boundary. In the UI, each citation `[C1]` displays the source filename, page number, part number, and section title, with an expandable raw snippet. This ensures engineers can verify source truth immediately."*

### 7. Out-of-Domain Abstention & Hallucination Defense (30 seconds)
> **Action:** In the Workspace, click starter or enter:
> ```text
> Give me the material specification for a titanium wing spar.
> ```
> **Talking Point:**
> *"When asked an out-of-domain question, the retrieval engine discovers no relevant chunks above the threshold. The LLM evaluates the context, detects insufficient evidence, and returns a standardized refusal: 'The available documents do not contain enough information to answer this question.' Zero citations are invented. This strict abstention is critical for engineering safety."*

### 8. Cloud & Deployment Architecture (30 seconds)
> *"The system is designed with abstract provider interfaces. In development, it runs hermetically with zero cloud dependencies using local mock providers and SQLite/PostgreSQL. In Milestone 9, we integrated and verified the stack against live Microsoft Azure services: Azure OpenAI for GPT-4o and text-embedding-3-small, Azure AI Search for hybrid vector retrieval, Azure PostgreSQL Flexible Server, and Azure Blob Storage. Frontend assets are hosted on Azure Static Web Apps, while container images are distributed via Azure Container Registry. Backend Azure container hosting remains a future deployment step."*

### 9. Engineering Tradeoffs & Summary (30 seconds)
> *"Key engineering decisions include: using LangGraph over rigid sequential chains for dynamic planning; enforcing deterministic calculation tools instead of LLM arithmetic; maintaining page-level provenance throughout the pipeline; and implementing an automated 8-case benchmark harness (`evaluate_copilot.py`) that measures pass rates, abstention accuracy, and latency."*

---

## 🎯 Quick-Reference Live Queries

| # | Demo Step | Query String | Primary Mechanism |
|---|:---|:---|:---|
| 1 | **Factual Retrieval + Tool Calculation** | `What is the maximum working pressure of CFP-402-316L in psi?` | Hybrid Search → Dynamic Extraction → Unit Calculator → Citations |
| 2 | **Direct Unit Calculation** | `Convert 75 kW to horsepower` | Deterministic Calculator Tool |
| 3 | **Metadata Registry Lookup** | `What is the document revision and status for sample_pump_spec.pdf?` | Relational SQL Metadata Tool |
| 4 | **Tolerance & Detail** | `What is the radial bearing journal tolerance?` | Precision Chunk Retrieval (ISO h6) |
| 5 | **Out-of-Domain Abstention** | `Give me the material specification for a titanium wing spar.` | Insufficient Evidence Boundary / Abstention |
