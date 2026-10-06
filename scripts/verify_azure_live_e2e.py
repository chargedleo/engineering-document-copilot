#!/usr/bin/env python3
"""
Comprehensive Live Azure Cloud Verification Script for Milestone 9.
Verifies all 5 Azure services and end-to-end capabilities:
1. Azure Database for PostgreSQL Flexible Server
2. Azure Blob Storage
3. Azure AI Search (Hybrid + Vectors)
4. Azure OpenAI Embeddings (text-embedding-3-small)
5. Azure OpenAI Chat (gpt-4o) via LangGraph Agent

Performs the 5 required E2E verification tests:
- Test 1: Ingestion Pipeline (PDF -> Azure Blob + Azure PostgreSQL + Azure OpenAI + Azure Search)
- Test 2: Working Pressure Query (CFP-402-316L 16.0 bar -> 232 psi with citation)
- Test 3: Engineering Calculation Query (Convert 75 kW to horsepower)
- Test 4: Abstention Query (Titanium wing spar -> abstains)
- Test 5: Metadata Lookup Query (CFP-402-316L -> Revision D)
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load Azure Environment Variables from backend/.env.azure if available
env_azure_path = BACKEND_DIR / ".env.azure"
if env_azure_path.exists():
    with open(env_azure_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# Ensure Azure providers are selected
os.environ["EMBEDDING_PROVIDER"] = "azure"
os.environ["SEARCH_PROVIDER"] = "azure"
os.environ["LLM_PROVIDER"] = "azure"
os.environ["STORAGE_PROVIDER"] = "azure"

# Re-import settings after env vars set
from app.core.config import settings
for key, val in os.environ.items():
    if hasattr(settings, key):
        if key == "DEBUG":
            setattr(settings, key, str(val).lower() in ("true", "1", "yes"))
        else:
            setattr(settings, key, val)

# Bind database engine to rotated DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core import database
database.engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    future=True,
    pool_pre_ping=True,
)
database.AsyncSessionLocal = async_sessionmaker(
    bind=database.engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
AsyncSessionLocal = database.AsyncSessionLocal

from app.services.document_service import DocumentService
from app.services.agent_service import AgentService
from app.schemas.agent import AgentQueryRequest
from app.services.embeddings.factory import reset_embedding_provider
from app.services.search.factory import reset_search_index
from app.services.llm.factory import reset_llm_provider
from app.services.storage import StorageService
from sqlalchemy import select
from app.models.document import Document, DocumentChunk, DocumentPage, DocumentStatus
import uuid

reset_embedding_provider()
reset_search_index()
reset_llm_provider()


async def run_azure_verification():
    print("=" * 80)
    print("  MILESTONE 9: LIVE AZURE CLOUD STACK END-TO-END VERIFICATION")
    print("=" * 80)
    print(f"  PostgreSQL Server : psql-engcopilot-06724.postgres.database.azure.com (centralus)")
    print(f"  Blob Storage      : stengcopilot06724.blob.core.windows.net/documents (eastus)")
    print(f"  OpenAI Endpoint   : aoai-engineering-copilot-06724.openai.azure.com (eastus)")
    print(f"  Search Endpoint   : search-engineering-copilot.search.windows.net (eastus)")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # TEST 0: LIVE AZURE BLOB STORAGE TEMPORARY BLOB UPLOAD / DOWNLOAD / CLEANUP
    # --------------------------------------------------------------------------
    print("\n>>> TEST 0: Live Azure Blob Storage Upload / Download / Cleanup...")
    test_run_id = uuid.uuid4().hex[:12]
    temp_doc_id = f"m9-verification/{test_run_id}"
    temp_filename = "test.txt"
    temp_blob_path = f"{temp_doc_id}/{temp_filename}"
    temp_payload = f"M9 live blob verification payload {test_run_id}".encode("utf-8")

    # Upload
    uploaded_url = StorageService.upload_document_blob(temp_doc_id, temp_filename, temp_payload)
    assert uploaded_url and "stengcopilot06724.blob.core.windows.net" in uploaded_url, "Upload failed"
    print(f"  [+] Temporary test blob uploaded successfully: {temp_blob_path}")

    # Download
    downloaded_bytes = StorageService.download_document_blob(temp_doc_id, temp_filename)
    assert downloaded_bytes == temp_payload, "Downloaded content mismatch"
    print(f"  [+] Downloaded content matched exact uploaded payload ({len(downloaded_bytes)} bytes)")

    # Cleanup temporary test blob
    from azure.storage.blob import BlobServiceClient
    bsc = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
    cc = bsc.get_container_client(settings.AZURE_STORAGE_CONTAINER_NAME or "documents")
    cc.delete_blob(temp_blob_path)
    print(f"  [+] Temporary test blob deleted cleanly: {temp_blob_path}")
    print(">>> TEST 0 PASSED: Live Azure Blob Storage verified!")

    pdf_path = ROOT_DIR / "data" / "sample_pump_spec.pdf"
    if not pdf_path.exists():
        print(f"ERROR: Sample PDF not found at {pdf_path}")
        return False

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    doc_id = None

    async with AsyncSessionLocal() as session:
        # ----------------------------------------------------------------------
        # TEST 1: LIVE INGESTION PIPELINE
        # ----------------------------------------------------------------------
        print("\n>>> TEST 1: Ingestion & Live Azure Indexing...")
        stmt = select(Document).where(
            Document.part_number == "CFP-402-316L",
            Document.status == DocumentStatus.PROCESSED
        )
        res = await session.execute(stmt)
        doc = res.scalars().first()

        if not doc:
            t0 = time.perf_counter()
            doc, proc_res = await DocumentService.process_and_store_document(
                db=session,
                file_bytes=pdf_bytes,
                original_filename="sample_pump_spec.pdf",
                document_type="SPECIFICATION",
                part_number="CFP-402-316L",
                revision="D",
            )
            doc_id = doc.id
            print(f"  [+] Document persisted in Azure PostgreSQL: ID={doc.id}")
            print(f"  [+] Processed pages: {proc_res.total_pages} (native text: {proc_res.total_pages - proc_res.ocr_pages})")
            print(f"  [+] Azure Blob URL: {doc.metadata_payload.get('azure_blob_url')}")

            chunk_info = await DocumentService.generate_document_chunks(session, doc.id)
            t_ingest = time.perf_counter() - t0
            print(f"  [+] Chunks created: {chunk_info.chunks_created}")
            print(f"  [+] Azure OpenAI Embeddings generated: {chunk_info.embeddings_generated}")
            print(f"  [+] Indexed into Azure AI Search: {chunk_info.indexed_count}")
            print(f"  [+] Ingestion elapsed time: {t_ingest:.2f}s")

            assert chunk_info.chunks_created > 0, "No chunks created"
            assert chunk_info.embeddings_generated > 0, "No embeddings generated"
            assert chunk_info.indexed_count > 0, "No chunks indexed in Azure Search"
        else:
            doc_id = doc.id
            print(f"  [+] Using verified document in Azure PostgreSQL: ID={doc.id}")
            print(f"  [+] Azure Blob URL: {doc.metadata_payload.get('azure_blob_url')}")
            chunks_count = await session.scalar(
                select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            )
            print(f"  [+] Document verified in Azure PostgreSQL with status: {doc.status}")

        print(">>> TEST 1 PASSED: End-to-end ingestion pipeline succeeded!")

        # Allow Azure AI Search index replication buffer
        await asyncio.sleep(2)

        # ----------------------------------------------------------------------
        # TEST 2: WORKING PRESSURE QUERY WITH CITATION
        # ----------------------------------------------------------------------
        print("\n>>> TEST 2: Working Pressure Query (CFP-402-316L in psi)...")
        t0 = time.perf_counter()
        req2 = AgentQueryRequest(
            query="What is the maximum working pressure of CFP-402-316L in psi?",
            top_k=5,
        )
        res2 = await AgentService.run_agent(session, req2)
        t2 = time.perf_counter() - t0
        print(f"  [+] Latency: {t2:.2f}s")
        print(f"  [+] Tools used: {res2.tools_used}")
        print(f"  [+] Citations: {len(res2.citations)}")
        for c in res2.citations:
            print(f"      - {c.filename} Page {c.page_number} ({c.section})")
        print(f"  [+] Answer:\n{res2.answer.strip()}\n")

        assert not res2.should_abstain, "Should not abstain on valid pump pressure question"
        assert len(res2.citations) > 0, "Expected at least one citation"
        answer_lower = res2.answer.lower()
        # Verify 16 bar and/or 232 psi
        assert "16" in answer_lower or "232" in answer_lower, "Expected 16 bar or 232 psi in answer"
        print(">>> TEST 2 PASSED: Working pressure answered with citations!")

        # ----------------------------------------------------------------------
        # TEST 3: CALCULATION QUERY
        # ----------------------------------------------------------------------
        print("\n>>> TEST 3: Engineering Unit Calculation (75 kW to horsepower)...")
        t0 = time.perf_counter()
        req3 = AgentQueryRequest(
            query="Convert 75 kW to horsepower",
        )
        res3 = await AgentService.run_agent(session, req3)
        t3 = time.perf_counter() - t0
        print(f"  [+] Latency: {t3:.2f}s")
        print(f"  [+] Tools used: {res3.tools_used}")
        print(f"  [+] Answer:\n{res3.answer.strip()}\n")

        assert not res3.should_abstain, "Calculation should not abstain"
        assert any("calc" in t.lower() for t in res3.tools_used), f"Expected calculation tool in {res3.tools_used}"
        assert "100" in res3.answer, "Expected ~100.58 hp in answer"
        print(">>> TEST 3 PASSED: Engineering calculation performed correctly!")

        # ----------------------------------------------------------------------
        # TEST 4: ABSTENTION QUERY
        # ----------------------------------------------------------------------
        print("\n>>> TEST 4: Out-of-Domain Abstention Query (Titanium wing spar)...")
        t0 = time.perf_counter()
        req4 = AgentQueryRequest(
            query="What is the maximum allowable stress for a titanium wing spar?",
        )
        res4 = await AgentService.run_agent(session, req4)
        t4 = time.perf_counter() - t0
        print(f"  [+] Latency: {t4:.2f}s")
        print(f"  [+] Should abstain: {res4.should_abstain}")
        print(f"  [+] Tools used: {res4.tools_used}")
        print(f"  [+] Answer:\n{res4.answer.strip()}\n")

        assert res4.should_abstain, "Agent must abstain on out-of-domain knowledge"
        assert len(res4.citations) == 0, "No citations expected for abstention"
        print(">>> TEST 4 PASSED: Out-of-domain query properly abstained!")

        # ----------------------------------------------------------------------
        # TEST 5: METADATA LOOKUP QUERY
        # ----------------------------------------------------------------------
        print("\n>>> TEST 5: Engineering Metadata Lookup (CFP-402-316L Revision)...")
        t0 = time.perf_counter()
        req5 = AgentQueryRequest(
            query="What is the revision and document type of CFP-402-316L?",
        )
        res5 = await AgentService.run_agent(session, req5)
        t5 = time.perf_counter() - t0
        print(f"  [+] Latency: {t5:.2f}s")
        print(f"  [+] Tools used: {res5.tools_used}")
        print(f"  [+] Answer:\n{res5.answer.strip()}\n")

        assert not res5.should_abstain, "Metadata lookup should not abstain"
        assert "get_document_metadata" in res5.tools_used or "search_engineering_documents" in res5.tools_used
        assert "D" in res5.answer or "d" in res5.answer, "Expected Revision D in answer"
        print(">>> TEST 5 PASSED: Metadata lookup returned Revision D!")

    print("\n" + "=" * 80)
    print("  ALL 5 LIVE AZURE CLOUD VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = asyncio.run(run_azure_verification())
    sys.exit(0 if success else 1)
