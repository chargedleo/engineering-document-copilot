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


def generate_test_pdf_bytes() -> bytes:
    """Generate in-memory multi-page test PDF bytes using fitz."""
    import fitz
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "TURBINE COMPRESSOR SPECIFICATION MODEL TC-500\n"
        "Part Number: TC-500-ENG\n"
        "Operating Pressure: 30.5 bar +/- 0.5 bar\n"
        "Speed: 3600 RPM\n"
        "Material: ASTM A182 F316\n",
        fontsize=12
    )
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(
        (50, 72),
        "MAINTENANCE INTERVALS AND LUBRICATION SPECIFICATIONS\n"
        "Synthetic Lubricant: ISO VG 68\n"
        "Bearing replacement: 8000 operating hours\n",
        fontsize=12
    )
    b = doc.tobytes()
    doc.close()
    return b


@pytest.mark.asyncio
async def test_upload_document_pdf_success(async_client: AsyncClient):
    """Test: Upload valid PDF returns 201 Created and creates DocumentPage records."""
    pdf_bytes = generate_test_pdf_bytes()
    files = {"file": ("Turbine_Compressor_Spec.pdf", pdf_bytes, "application/pdf")}
    data = {
        "document_type": "SPECIFICATION",
        "part_number": "TC-500-ENG",
        "revision": "B"
    }
    response = await async_client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    res_data = body["data"]
    doc_id = res_data["document_id"]
    assert doc_id is not None
    assert res_data["filename"] == "Turbine_Compressor_Spec.pdf"
    assert res_data["status"] == "PROCESSED"
    assert res_data["page_count"] == 2
    assert res_data["processed_page_count"] == 2
    assert res_data["ocr_page_count"] == 0

    # Verify pages can be listed
    pages_res = await async_client.get(f"/api/v1/documents/{doc_id}/pages")
    assert pages_res.status_code == 200
    pages_data = pages_res.json()["data"]
    assert pages_data["total"] == 2
    assert len(pages_data["items"]) == 2

    # Verify 1-based page numbering
    page1 = pages_data["items"][0]
    page2 = pages_data["items"][1]
    assert page1["page_number"] == 1
    assert page1["extraction_method"] == "text"
    assert page1["ocr_used"] is False
    assert "TURBINE COMPRESSOR SPECIFICATION" in page1["text"]
    assert page1["character_count"] > 0
    assert page1["word_count"] > 0

    assert page2["page_number"] == 2
    assert page2["extraction_method"] == "text"
    assert "MAINTENANCE INTERVALS" in page2["text"]


@pytest.mark.asyncio
async def test_get_document_single_page(async_client: AsyncClient):
    """Test: Retrieve single document page by 1-based page number."""
    pdf_bytes = generate_test_pdf_bytes()
    files = {"file": ("Compressor_Spec_Single.pdf", pdf_bytes, "application/pdf")}
    upload_res = await async_client.post("/api/v1/documents/upload", files=files)
    doc_id = upload_res.json()["data"]["document_id"]

    # Retrieve Page 1
    page1_res = await async_client.get(f"/api/v1/documents/{doc_id}/pages/1")
    assert page1_res.status_code == 200
    page1 = page1_res.json()["data"]
    assert page1["document_id"] == doc_id
    assert page1["page_number"] == 1
    assert "TURBINE COMPRESSOR" in page1["text"]

    # Non-existent page number 99
    page99_res = await async_client.get(f"/api/v1/documents/{doc_id}/pages/99")
    assert page99_res.status_code == 404


@pytest.mark.asyncio
async def test_upload_invalid_file_extension(async_client: AsyncClient):
    """Test: Upload non-PDF file returns 400 Bad Request."""
    files = {"file": ("drawing.dwg", b"fake binary data", "application/octet-stream")}
    response = await async_client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Only PDF documents" in response.json()["message"]


@pytest.mark.asyncio
async def test_upload_empty_pdf_file(async_client: AsyncClient):
    """Test: Upload 0-byte PDF returns 400 Bad Request."""
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    response = await async_client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_upload_invalid_pdf_header(async_client: AsyncClient):
    """Test: Upload file without valid PDF header returns 400 Bad Request."""
    files = {"file": ("fake.pdf", b"NOT A PDF HEADER CONTENT", "application/pdf")}
    response = await async_client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Header does not match" in response.json()["message"]

