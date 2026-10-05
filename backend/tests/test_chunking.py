import pytest
from app.services.chunking import EngineeringDocumentChunker, PageInput


@pytest.fixture
def chunker():
    return EngineeringDocumentChunker(chunk_size_chars=300, chunk_overlap_chars=50)


def test_chunking_preserves_engineering_notation(chunker):
    """Verify units, tolerances, part numbers, and technical symbols are not mutated or stripped."""
    text = (
        "1.1 MECHANICAL SPECIFICATIONS\n"
        "The centrifugal slurry pump model CFP-402-316L operates at 1750 RPM ± 25 RPM.\n"
        "Maximum operating discharge pressure is 16.5 bar (239.3 psi) at 95 °C.\n"
        "Shaft tolerance conforms to ISO h6 (+0.000 / -0.016 mm) with runout < 0.025 mm.\n"
        "Design flow rate: 450 m³/h with minimum NPSHr of 3.2 m."
    )
    pages = [PageInput(page_id="p1", page_number=1, text=text)]
    doc_meta = {
        "document_id": "doc-001",
        "filename": "pump_specs.pdf",
        "document_type": "SPECIFICATION",
        "part_number": "CFP-402-316L",
        "revision": "D",
    }

    chunks = chunker.chunk_document_pages(pages, doc_meta)
    assert len(chunks) >= 1

    all_content = " ".join(c.content for c in chunks)
    assert "CFP-402-316L" in all_content
    assert "1750 RPM ± 25 RPM" in all_content
    assert "16.5 bar" in all_content
    assert "95 °C" in all_content
    assert "+0.000 / -0.016 mm" in all_content
    assert "450 m³/h" in all_content


def test_chunking_preserves_page_boundaries_and_metadata(chunker):
    """Verify chunks maintain page identity, ordering, and document metadata."""
    pages = [
        PageInput(page_id="page-1", page_number=1, text="SECTION 1: OVERVIEW\nIntroduction to assembly unit."),
        PageInput(page_id="page-2", page_number=2, text="SECTION 2: TORQUE SPECIFICATIONS\nBolt torque is 85 Nm."),
    ]
    doc_meta = {
        "document_id": "doc-123",
        "filename": "assembly_manual.pdf",
        "document_type": "MANUAL",
        "part_number": "ASM-8800",
        "revision": "C",
    }

    chunks = chunker.chunk_document_pages(pages, doc_meta)
    assert len(chunks) == 2

    c0 = chunks[0]
    assert c0.chunk_index == 0
    assert c0.page_number == 1
    assert c0.page_id == "page-1"
    assert c0.metadata_payload["document_id"] == "doc-123"
    assert c0.metadata_payload["part_number"] == "ASM-8800"
    assert c0.metadata_payload["revision"] == "C"

    c1 = chunks[1]
    assert c1.chunk_index == 1
    assert c1.page_number == 2
    assert c1.page_id == "page-2"
    assert c1.metadata_payload["document_id"] == "doc-123"


def test_chunking_short_pages(chunker):
    """Ensure very short pages produce clean single chunks without errors."""
    pages = [PageInput(page_id="p-short", page_number=1, text="CONFIDENTIAL - REVISION D")]
    doc_meta = {"document_id": "doc-short", "filename": "short.pdf"}

    chunks = chunker.chunk_document_pages(pages, doc_meta)
    assert len(chunks) == 1
    assert chunks[0].content == "CONFIDENTIAL - REVISION D"
    assert chunks[0].character_count == len("CONFIDENTIAL - REVISION D")
    assert chunks[0].word_count == 4


def test_chunking_oversized_blocks(chunker):
    """Ensure paragraphs larger than chunk_size are safely segmented without infinite loops."""
    long_line = "Torque spec: 45 Nm. " * 30  # ~600 chars, larger than chunk_size_chars=300
    pages = [PageInput(page_id="p-long", page_number=1, text=long_line)]
    doc_meta = {"document_id": "doc-long", "filename": "long.pdf"}

    chunks = chunker.chunk_document_pages(pages, doc_meta)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.character_count > 0
        assert c.page_number == 1


def test_chunking_section_detection(chunker):
    """Ensure section headers are tracked in chunk metadata."""
    text = (
        "2.0 ELECTRICAL REQUIREMENTS\n"
        "Voltage is 460 V 3-phase, 60 Hz.\n\n"
        "3.0 MAINTENANCE PROTOCOL\n"
        "Inspect seal rings every 500 operating hours."
    )
    pages = [PageInput(page_id="p-sec", page_number=1, text=text)]
    doc_meta = {"document_id": "doc-sec", "filename": "specs.pdf"}

    chunks = chunker.chunk_document_pages(pages, doc_meta)
    assert len(chunks) >= 1
    # Check that metadata contains section information
    sections = [c.metadata_payload.get("section") for c in chunks]
    assert any("ELECTRICAL" in s or "MAINTENANCE" in s for s in sections if s)


def test_chunking_ocr_text_with_noise(chunker):
    """Ensure OCR text with noisy line breaks and characters does not break the chunker."""
    ocr_text = (
        "DWG NO: C-8890-REV_B\n"
        "MATERIAL: ASTM A351 CF8M (316 SS)\n\n"
        "NOTES:\n"
        "1. ALL DIMENSIONS IN MILLIMETERS UNLESS NOTED.\n"
        "2. BREAK ALL SHARP EDGES 0.25 - 0.50 MM.\n"
        "3. HYDROSTATIC TEST AT 24.5 BAR FOR 30 MIN."
    )
    pages = [PageInput(page_id="p-ocr", page_number=1, text=ocr_text)]
    doc_meta = {"document_id": "doc-ocr", "filename": "drawing.pdf"}

    chunks = chunker.chunk_document_pages(pages, doc_meta)
    assert len(chunks) >= 1
    all_content = " ".join(c.content for c in chunks)
    assert "24.5 BAR" in all_content
    assert "ASTM A351 CF8M" in all_content

