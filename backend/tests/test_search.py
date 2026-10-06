import pytest
import numpy as np
from httpx import AsyncClient
import pymupdf as fitz

from app.services.embeddings.local_mock import LocalMockEmbeddingProvider
from app.services.search.local_index import LocalSearchIndex
from app.services.search.base import SearchHit
from app.services.search.factory import reset_search_index


@pytest.fixture(autouse=True)
def reset_index():
    reset_search_index()
    yield
    reset_search_index()


# =========================================================================
# 1. EMBEDDINGS TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_mock_embedding_dimensions_and_norm():
    """Verify local mock embedding provider produces normalized 1536-dimensional vectors."""
    provider = LocalMockEmbeddingProvider(dimensions=1536)
    assert provider.dimension == 1536

    texts = [
        "Centrifugal pump CFP-402 operating at 1750 RPM.",
        "Electrical wiring standard 460 V 60 Hz 3-phase.",
    ]
    vectors = await provider.embed_texts(texts)
    assert len(vectors) == 2
    for v in vectors:
        assert len(v) == 1536
        norm = np.linalg.norm(np.array(v, dtype=np.float32))
        assert abs(norm - 1.0) < 1e-4


@pytest.mark.asyncio
async def test_mock_embedding_deterministic():
    """Verify identical text produces identical embedding vector."""
    provider = LocalMockEmbeddingProvider(dimensions=1536)
    text = "Flange bolt torque 170 Nm +/- 5 Nm."

    v1 = await provider.embed_query(text)
    v2 = await provider.embed_query(text)
    assert v1 == v2


@pytest.mark.asyncio
async def test_mock_embedding_semantic_proximity():
    """Verify texts sharing key engineering terms have higher cosine similarity."""
    provider = LocalMockEmbeddingProvider(dimensions=1536)

    q = "centrifugal pump impeller slurry"
    doc_related = "centrifugal slurry pump with stainless steel impeller"
    doc_unrelated = "high voltage electrical transformer grounding specification"

    q_vec = np.array(await provider.embed_query(q))
    rel_vec = np.array(await provider.embed_query(doc_related))
    unrel_vec = np.array(await provider.embed_query(doc_unrelated))

    sim_rel = float(np.dot(q_vec, rel_vec))
    sim_unrel = float(np.dot(q_vec, unrel_vec))

    assert sim_rel > sim_unrel


# =========================================================================
# 2. LOCAL SEARCH INDEX TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_local_search_index_keyword_retrieval():
    """Verify BM25 keyword search retrieves exact engineering terms."""
    index = LocalSearchIndex()
    provider = LocalMockEmbeddingProvider()

    c1_text = "Valve model HV-100 operates at 25.0 bar nominal pressure."
    c2_text = "Standard lubrication schedule for SKF bearing 6205."

    chunks = [
        {
            "chunk_id": "c1",
            "document_id": "doc1",
            "chunk_index": 0,
            "page_number": 1,
            "filename": "valve.pdf",
            "document_type": "SPECIFICATION",
            "part_number": "HV-100",
            "content": c1_text,
            "embedding": await provider.embed_query(c1_text),
        },
        {
            "chunk_id": "c2",
            "document_id": "doc2",
            "chunk_index": 0,
            "page_number": 1,
            "filename": "bearing.pdf",
            "document_type": "MANUAL",
            "part_number": "SKF-6205",
            "content": c2_text,
            "embedding": await provider.embed_query(c2_text),
        },
    ]

    await index.index_chunks(chunks)

    # Keyword search for HV-100
    hits = await index.search(query="HV-100 valve pressure", mode="keyword", top_k=5)
    assert len(hits) >= 1
    assert hits[0].chunk_id == "c1"
    assert hits[0].part_number == "HV-100"


@pytest.mark.asyncio
async def test_local_search_index_metadata_filtering():
    """Verify search respects metadata filters (part_number, document_type, document_id)."""
    index = LocalSearchIndex()
    provider = LocalMockEmbeddingProvider()

    chunks = [
        {
            "chunk_id": "c1",
            "document_id": "doc-A",
            "chunk_index": 0,
            "page_number": 1,
            "filename": "valve_A.pdf",
            "document_type": "SPECIFICATION",
            "part_number": "V-100",
            "content": "Pressure rating 50 bar.",
            "embedding": await provider.embed_query("Pressure rating 50 bar."),
        },
        {
            "chunk_id": "c2",
            "document_id": "doc-B",
            "chunk_index": 0,
            "page_number": 1,
            "filename": "valve_B.pdf",
            "document_type": "MANUAL",
            "part_number": "V-200",
            "content": "Pressure rating 50 bar.",
            "embedding": await provider.embed_query("Pressure rating 50 bar."),
        },
    ]
    await index.index_chunks(chunks)

    # Filter by document_type
    hits = await index.search(
        query="Pressure",
        mode="keyword",
        filters={"document_type": "SPECIFICATION"},
    )
    assert len(hits) == 1
    assert hits[0].chunk_id == "c1"

    # Filter by part_number
    hits_part = await index.search(
        query="Pressure",
        mode="keyword",
        filters={"part_number": "V-200"},
    )
    assert len(hits_part) == 1
    assert hits_part[0].chunk_id == "c2"


@pytest.mark.asyncio
async def test_local_search_index_hybrid_rrf():
    """Verify hybrid search combines keyword and vector signals."""
    index = LocalSearchIndex()
    provider = LocalMockEmbeddingProvider()

    text = "Centrifugal slurry pump CFP-402 casing bolt torque 120 Nm."
    q_vec = await provider.embed_query("CFP-402 torque")

    chunks = [
        {
            "chunk_id": "c1",
            "document_id": "doc1",
            "chunk_index": 0,
            "page_number": 1,
            "filename": "pump.pdf",
            "document_type": "SPECIFICATION",
            "part_number": "CFP-402",
            "content": text,
            "embedding": await provider.embed_query(text),
        }
    ]
    await index.index_chunks(chunks)

    hits = await index.search(
        query="CFP-402 torque",
        query_vector=q_vec,
        mode="hybrid",
        top_k=5,
    )
    assert len(hits) == 1
    assert hits[0].chunk_id == "c1"
    assert hits[0].retrieval_mode == "hybrid"


# =========================================================================
# 3. END-TO-END API TESTS
# =========================================================================

def _create_test_pdf_bytes() -> bytes:
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "1.0 EQUIPMENT SPECIFICATION\n"
        "Model: COMP-900 Turbo Compressor\n"
        "Discharge pressure: 32.5 bar +/- 0.5 bar.\n"
        "Flow rate: 1200 m3/h at 3600 RPM.\n",
        fontsize=12,
    )
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(
        (50, 72),
        "2.0 INSTALLATION & TORQUE SPECS\n"
        "Anchor bolt torque: 250 Nm.\n"
        "Flange alignment runout < 0.05 mm.\n",
        fontsize=12,
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_chunks_generate_and_list_api(async_client: AsyncClient):
    """Test full flow: upload PDF -> process -> generate chunks -> list chunks -> get chunk."""
    pdf_bytes = _create_test_pdf_bytes()
    files = {"file": ("compressor_spec.pdf", pdf_bytes, "application/pdf")}
    data = {
        "document_type": "SPECIFICATION",
        "part_number": "COMP-900",
        "revision": "A",
    }

    # 1. Upload and process PDF
    upload_resp = await async_client.post("/api/v1/documents/upload", files=files, data=data)
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["data"]["document_id"]

    # 2. Trigger chunk generation
    gen_resp = await async_client.post(f"/api/v1/documents/{doc_id}/chunks/generate")
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()["data"]
    assert gen_data["document_id"] == doc_id
    assert gen_data["chunks_created"] >= 2
    assert gen_data["embeddings_generated"] >= 2
    assert gen_data["indexed_count"] >= 2
    assert gen_data["status"] == "completed"

    # 3. List chunks
    list_resp = await async_client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert list_resp.status_code == 200
    chunk_items = list_resp.json()["data"]["items"]
    assert len(chunk_items) == gen_data["chunks_created"]

    first_chunk = chunk_items[0]
    assert first_chunk["document_id"] == doc_id
    assert first_chunk["chunk_index"] == 0
    assert first_chunk["page_number"] == 1
    assert "COMP-900" in first_chunk["content"] or "EQUIPMENT" in first_chunk["content"]
    assert first_chunk["embedding_status"] == "completed"

    # 4. Get specific chunk by ID
    chunk_id = first_chunk["id"]
    get_chunk_resp = await async_client.get(f"/api/v1/documents/{doc_id}/chunks/{chunk_id}")
    assert get_chunk_resp.status_code == 200
    assert get_chunk_resp.json()["data"]["id"] == chunk_id


@pytest.mark.asyncio
async def test_search_api_modes_and_filters(async_client: AsyncClient):
    """Test /api/v1/search endpoint with keyword, vector, hybrid, and metadata filtering."""
    # Upload and generate chunks for a document
    pdf_bytes = _create_test_pdf_bytes()
    files = {"file": ("compressor_spec.pdf", pdf_bytes, "application/pdf")}
    data = {
        "document_type": "SPECIFICATION",
        "part_number": "COMP-900",
        "revision": "B",
    }
    upload_resp = await async_client.post("/api/v1/documents/upload", files=files, data=data)
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["data"]["document_id"]
    await async_client.post(f"/api/v1/documents/{doc_id}/chunks/generate")

    # A. Keyword search
    kw_payload = {
        "query": "COMP-900 3600 RPM",
        "mode": "keyword",
        "top_k": 5,
    }
    kw_resp = await async_client.post("/api/v1/search", json=kw_payload)
    assert kw_resp.status_code == 200
    kw_results = kw_resp.json()["data"]["results"]
    assert len(kw_results) >= 1
    assert any("3600 RPM" in r["content"] for r in kw_results)

    # B. Vector search
    vec_payload = {
        "query": "compressor discharge pressure",
        "mode": "vector",
        "top_k": 3,
    }
    vec_resp = await async_client.post("/api/v1/search", json=vec_payload)
    assert vec_resp.status_code == 200
    vec_results = vec_resp.json()["data"]["results"]
    assert len(vec_results) >= 1

    # C. Hybrid search
    hyb_payload = {
        "query": "Anchor bolt torque 250 Nm",
        "mode": "hybrid",
        "top_k": 5,
    }
    hyb_resp = await async_client.post("/api/v1/search", json=hyb_payload)
    assert hyb_resp.status_code == 200
    hyb_results = hyb_resp.json()["data"]["results"]
    assert len(hyb_results) >= 1
    assert any("250 Nm" in r["content"] for r in hyb_results)

    # D. Filtered search
    filter_payload = {
        "query": "torque",
        "mode": "hybrid",
        "top_k": 5,
        "filters": {
            "part_number": "COMP-900",
            "document_type": "SPECIFICATION",
        },
    }
    filt_resp = await async_client.post("/api/v1/search", json=filter_payload)
    assert filt_resp.status_code == 200
    filt_results = filt_resp.json()["data"]["results"]
    assert len(filt_results) >= 1
    for r in filt_results:
        assert r["part_number"] == "COMP-900"


@pytest.mark.asyncio
async def test_search_api_validation(async_client: AsyncClient):
    """Test validation errors on invalid search requests."""
    # Empty query should fail with 422
    resp = await async_client.post("/api/v1/search", json={"query": "", "mode": "hybrid"})
    assert resp.status_code == 422

    # Invalid top_k (< 1) should fail with 422
    resp_k = await async_client.post("/api/v1/search", json={"query": "test", "top_k": 0})
    assert resp_k.status_code == 422


@pytest.mark.asyncio
async def test_chunks_generate_negative_cases(async_client: AsyncClient):
    """Test 404 for non-existent document and 400 for un-extracted document."""
    # 404 Not Found
    resp_404 = await async_client.post("/api/v1/documents/non-existent-id/chunks/generate")
    assert resp_404.status_code == 404

    # Create document metadata without uploading/processing pages
    doc_create_resp = await async_client.post(
        "/api/v1/documents",
        json={"filename": "empty_doc.pdf", "document_type": "SPECIFICATION"},
    )
    assert doc_create_resp.status_code == 201
    empty_doc_id = doc_create_resp.json()["data"]["id"]

    # Attempt to chunk empty document -> 400 Bad Request
    resp_400 = await async_client.post(f"/api/v1/documents/{empty_doc_id}/chunks/generate")
    assert resp_400.status_code == 400


@pytest.mark.asyncio
async def test_chunks_get_and_list_negative_cases(async_client: AsyncClient):
    """Test 404 for non-existent document or chunk ID."""
    resp_list_404 = await async_client.get("/api/v1/documents/non-existent-id/chunks")
    assert resp_list_404.status_code == 404

    resp_get_404 = await async_client.get("/api/v1/documents/non-existent-id/chunks/non-existent-chunk")
    assert resp_get_404.status_code == 404

