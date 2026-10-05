import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_document_metadata_success(async_client: AsyncClient):
    """Test: Document creation with valid metadata returns 201 Created."""
    payload = {
        "filename": "Gas_Turbine_Specification_Rev2.pdf",
        "document_type": "SPECIFICATION",
        "part_number": "GT-200-B",
        "revision": "B",
        "file_size_bytes": 204800,
        "mime_type": "application/pdf",
        "metadata_payload": {
            "title": "Gas Turbine Compressor Specification",
            "author": "Thermal Systems Engineering"
        }
    }
    response = await async_client.post("/api/v1/documents", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    doc = body["data"]
    assert doc["id"] is not None
    assert doc["filename"] == "Gas_Turbine_Specification_Rev2.pdf"
    assert doc["document_type"] == "SPECIFICATION"
    assert doc["part_number"] == "GT-200-B"
    assert doc["revision"] == "B"
    assert doc["status"] == "PENDING"
    assert "created_at" in doc
    assert "uploaded_at" in doc


@pytest.mark.asyncio
async def test_get_document_by_id_success(async_client: AsyncClient):
    """Test: Document retrieval by ID returns document details."""
    # First create a document
    create_payload = {
        "filename": "Structural_Beam_Manual.pdf",
        "document_type": "MANUAL",
        "part_number": "SB-101",
        "revision": "1.0"
    }
    create_res = await async_client.post("/api/v1/documents", json=create_payload)
    assert create_res.status_code == 201
    doc_id = create_res.json()["data"]["id"]

    # Now retrieve by ID
    get_res = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    doc_data = get_res.json()["data"]
    assert doc_data["id"] == doc_id
    assert doc_data["filename"] == "Structural_Beam_Manual.pdf"
    assert doc_data["part_number"] == "SB-101"


@pytest.mark.asyncio
async def test_get_document_not_found(async_client: AsyncClient):
    """Test: Document retrieval with non-existent ID returns 404."""
    response = await async_client.get("/api/v1/documents/non-existent-uuid-12345")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_list_documents_pagination_and_filter(async_client: AsyncClient):
    """Test: Document listing returns paginated items and supports filters."""
    # Seed 2 documents
    doc1 = {
        "filename": "Aero_Hydraulics_Spec.pdf",
        "document_type": "SPECIFICATION",
        "part_number": "HYD-01"
    }
    doc2 = {
        "filename": "Valve_Assembly_Manual.pdf",
        "document_type": "MANUAL",
        "part_number": "VLV-02"
    }
    await async_client.post("/api/v1/documents", json=doc1)
    await async_client.post("/api/v1/documents", json=doc2)

    # List all documents
    list_res = await async_client.get("/api/v1/documents")
    assert list_res.status_code == 200
    list_body = list_res.json()["data"]
    assert list_body["total"] >= 2
    assert len(list_body["items"]) >= 2

    # Filter by document_type
    filter_res = await async_client.get("/api/v1/documents?document_type=SPECIFICATION")
    assert filter_res.status_code == 200
    filtered_items = filter_res.json()["data"]["items"]
    assert all(item["document_type"] == "SPECIFICATION" for item in filtered_items)


@pytest.mark.asyncio
async def test_create_document_validation_failure(async_client: AsyncClient):
    """Test: Validation failure when required fields are missing or invalid."""
    # Missing required 'filename' field
    invalid_payload = {
        "document_type": "SPECIFICATION"
        # 'filename' is omitted
    }
    response = await async_client.post("/api/v1/documents", json=invalid_payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "validation" in data["message"].lower()
    assert len(data["errors"]) > 0
