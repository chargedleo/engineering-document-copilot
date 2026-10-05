# Engineering Document Intelligence & CAD Knowledge Copilot

A production-grade intelligent copilot platform designed for engineering teams to parse, index, search, and reason over complex engineering documents (specifications, BOMs, standards, datasheets) and CAD models/metadata.

> **Project Status (Milestone 2 - Backend Production Foundation)**:
> Fully operational local backend foundation featuring asynchronous FastAPI, layered service architecture, async SQLAlchemy 2.0 with PostgreSQL, bidirectional Alembic migrations, metadata-only Document APIs, structured error handling, and automated pytest suite.
> *Note: AI reasoning (LangGraph), vector search (Azure AI Search), LLMs (Azure OpenAI), and CAD geometric parsing are intentionally decoupled and scheduled for subsequent milestones.*

---

## 🏗️ Architecture & Tech Stack

- **Backend**: Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) (Async 2.x), [asyncpg](https://magicstack.github.io/asyncpg/), [Alembic](https://alembic.sqlalchemy.org/)
- **Database**: PostgreSQL 16 (local or containerized via Docker)
- **Frontend**: [React 18](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vitejs.dev/)
- **Configuration & Validation**: [Pydantic v2](https://docs.pydantic.dev/) and `pydantic-settings`
- **Testing**: [pytest](https://pytest.org/), `pytest-asyncio`, `aiosqlite` (hermetic in-memory testing)
- **Future Integrations (Configuration-Ready)**:
  - Orchestration: [LangGraph](https://python.langchain.com/docs/langgraph) / LangChain
  - LLM & Embeddings: Azure OpenAI (`gpt-4o`, `text-embedding-3-large`)
  - Hybrid Search: Azure AI Search

For an in-depth architectural breakdown and sequence diagrams, refer to [`architecture.md`](./architecture.md).

---

## 📁 Repository Structure

```text
├── .env.example              # Environment variables template with safe placeholders
├── .gitignore                 # Excludes .env, virtualenvs, caches, artifacts
├── README.md                  # Project overview and reproduction guide
├── architecture.md            # System architecture and data flow blueprint
├── backend/                   # FastAPI application & database migrations
│   ├── alembic/               # Alembic database migration scripts & versions
│   │   ├── versions/          # Version-controlled migration files
│   │   └── env.py             # Async Alembic runner
│   ├── app/
│   │   ├── api/v1/            # Versioned API routes (health, documents, cad, chat)
│   │   ├── core/              # Config (Pydantic Settings), DB session, logging
│   │   ├── models/            # SQLAlchemy 2.0 ORM models (Document, Chat, etc.)
│   │   ├── schemas/           # Pydantic v2 validation and serialization schemas
│   │   ├── services/          # Business logic layer (DocumentService, etc.)
│   │   ├── agents/            # LangGraph agent stubs (for future milestone)
│   │   └── integrations/      # Azure OpenAI & AI Search connectors (optional)
│   ├── tests/                 # Hermetic automated test suite (pytest + SQLite)
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
│   ├── documents/             # Raw engineering documents
│   └── processed/             # Parsed text, extracted metadata, chunks
├── scripts/                   # Automation and operational scripts
│   ├── init_db.py             # Database migration executor (alembic upgrade head)
│   └── seed_data.py           # Sample engineering document seeder
└── docker/                    # Docker Compose orchestration
    ├── docker-compose.yml     # Multi-container stack (DB, Backend, Frontend)
    └── docker-compose.dev.yml # Dedicated PostgreSQL service for local development
```

---

## 🚀 Local Development Setup (Milestone 2)

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher (for frontend)
- **Database**: PostgreSQL 16 (via Docker or local PostgreSQL installation)
- **PowerShell** (Windows) or **Bash** (Linux/macOS)

---

### Step 1: Environment Configuration

Copy the example environment configuration into `.env` at the project root:

**PowerShell (Windows):**
```powershell
Copy-Item .env.example .env
```

**Bash (Linux/macOS):**
```bash
cp .env.example .env
```

Ensure `.env` contains your database connection string:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/engineering_copilot
```
*(Azure credentials in `.env` are optional placeholders; the backend runs fully without them).*

---

### Step 2: Start PostgreSQL Database

#### Option A: Using Docker Compose (Recommended)
From the project root:
```powershell
docker compose -f docker/docker-compose.dev.yml up db -d
```
This starts PostgreSQL 16 with a persistent Docker volume (`postgres_dev_data`) and healthcheck on port `5432`.

#### Option B: Using Local / Native PostgreSQL
Ensure PostgreSQL is running locally on port `5432`, and create the target database:
```sql
CREATE DATABASE engineering_copilot;
```

---

### Step 3: Backend Setup & Virtual Environment

1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Create and activate a Python virtual environment:
   **Windows (PowerShell):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   **Linux / macOS:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

### Step 4: Run Database Migrations (Alembic)

The schema is strictly managed via Alembic. Ensure migrations are applied:

```powershell
# From the backend/ directory with .venv active:
alembic upgrade head
```

*Verification commands:*
```powershell
# Rollback the last migration:
alembic downgrade -1

# Re-apply migrations:
alembic upgrade head
```

Alternatively, run the database initialization script from the repository root:
```powershell
cd ..
python scripts/init_db.py
```

To seed initial sample engineering documents:
```powershell
python scripts/seed_data.py
```

---

### Step 5: Run Automated Tests

The test suite runs hermetically using an in-memory SQLite async database (`aiosqlite`) and does not modify your local PostgreSQL database:

```powershell
# From backend/ directory:
pytest tests/ -v
```

Expected output:
```text
tests/test_documents.py::test_create_document_metadata PASSED
tests/test_documents.py::test_get_document_by_id PASSED
tests/test_documents.py::test_get_document_not_found PASSED
tests/test_documents.py::test_list_documents_pagination PASSED
tests/test_documents.py::test_document_validation_failure PASSED
tests/test_health.py::test_health_endpoint PASSED
tests/test_health.py::test_readiness_endpoint_connected PASSED
tests/test_health.py::test_readiness_endpoint_db_failure PASSED
tests/test_health.py::test_swagger_docs_accessible PASSED
============================== 9 passed ==============================
```

---

### Step 6: Start FastAPI Backend Server

From the `backend/` directory:
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify backend health in another terminal or browser:
- **Liveness Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
  ```json
  {"status": "healthy", "service": "Engineering Document & CAD Copilot API", "version": "0.1.0"}
  ```
- **Readiness Check (DB Connectivity)**: [http://127.0.0.1:8000/api/v1/health/ready](http://127.0.0.1:8000/api/v1/health/ready)
  ```json
  {
    "status": "ready",
    "checks": {
      "database": "connected",
      "azure_openai": "not_configured (optional for Milestone 2)",
      "azure_search": "not_configured (optional for Milestone 2)"
    }
  }
  ```
- **Interactive OpenAPI Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Step 7: Start React Frontend (Optional)

1. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```
2. Install dependencies and start the Vite dev server:
   ```powershell
   npm install
   npm run dev
   ```
3. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📡 Milestone 2 Document API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service liveness probe. |
| `GET` | `/api/v1/health/ready` | Readiness probe (verifies PostgreSQL database connectivity). |
| `POST` | `/api/v1/documents` | Create document metadata record (`filename`, `part_number`, `revision`, `document_type`). |
| `GET` | `/api/v1/documents` | List documents with pagination (`skip`, `limit`) and filters. |
| `GET` | `/api/v1/documents/{document_id}` | Retrieve a specific document record by UUID. |

### Example: Create Document Metadata
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "PUMP-200-MANUAL.pdf",
    "document_type": "manual",
    "part_number": "PUMP-200",
    "revision": "B"
  }'
```

### Example: Validation Error Response
Validation errors return a clean HTTP 422 JSON payload without leaking internal stack traces:
```json
{
  "error": "Validation Error",
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "filename"],
      "msg": "Field required"
    }
  ]
}
```

---

## 🔒 Security & Best Practices

1. **No Credentials in Git**: `.env` is ignored by `.gitignore`. Only safe placeholders exist in `.env.example`.
2. **Safe Exception Handling**: Global exception handlers intercept raw database and runtime errors, preventing sensitive connection strings or stack traces from appearing in client responses.
3. **Decoupled Architecture**: Azure OpenAI and Azure AI Search configurations are optional for local runs. The application boots and operates cleanly without cloud credentials.
4. **Asynchronous I/O**: The entire database and request lifecycle utilizes `asyncio` and `asyncpg` for non-blocking I/O.
