import io
import pytest
from unittest.mock import patch
import fitz
from PIL import Image, ImageDraw

from app.services.document_processing.pdf_extractor import (
    validate_pdf_content,
    extract_native_page_text,
    normalize_extracted_text,
    render_page_to_image,
    PDFValidationError,
)
from app.services.document_processing.ocr import (
    find_tesseract_cmd,
    is_tesseract_available,
    preprocess_image_for_ocr,
    perform_ocr,
    TesseractNotFoundError,
)
from app.services.document_processing.processor import (
    process_pdf_document,
    is_native_text_sufficient,
)


def create_sample_text_pdf(tmp_path, filename="sample_text.pdf") -> str:
    """Helper to create a 2-page digital engineering PDF with selectable text."""
    doc = fitz.open()

    p1 = doc.new_page(width=595, height=842)
    p1_text = (
        "ENGINEERING SPECIFICATION: HYDRAULIC VALVE HV-100\n"
        "Part Number: HV-100-REV-C\n"
        "Nominal Pressure: 25.0 bar +/- 0.5 bar\n"
        "Material: ASTM A351 Grade CF8M (316 SS)\n"
        "Operating Temperature: -20 C to +150 C\n"
    )
    p1.insert_text((50, 72), p1_text, fontsize=12)

    p2 = doc.new_page(width=595, height=842)
    p2_text = (
        "TORQUE SPECIFICATIONS & BOLT REQUIREMENTS\n"
        "Flange bolts (M16x2.0): 170 Nm +/- 5 Nm\n"
        "Actuator mounting bolts: 45 Nm\n"
        "Test procedure: Hydrostatic shell test at 38 bar for 15 min.\n"
    )
    p2.insert_text((50, 72), p2_text, fontsize=12)

    target = tmp_path / filename
    doc.save(str(target))
    doc.close()
    return str(target)


def create_sample_scanned_pdf(tmp_path, filename="sample_scanned.pdf") -> str:
    """Helper to create a scanned/image-only PDF with rendered text and no native text layer."""
    img = Image.new("RGB", (800, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 80), "VALVE SPECIFICATION 450 PSI STAINLESS STEEL", fill=(0, 0, 0))

    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(fitz.Rect(50, 50, 545, 250), stream=img_buf.getvalue())

    target = tmp_path / filename
    doc.save(str(target))
    doc.close()
    return str(target)


def test_pdf_validation_success(tmp_path):
    pdf_path = create_sample_text_pdf(tmp_path)
    info = validate_pdf_content(pdf_path)
    assert info["page_count"] == 2
    assert info["file_size_bytes"] > 0


def test_pdf_validation_empty_file(tmp_path):
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    with pytest.raises(PDFValidationError, match="empty"):
        validate_pdf_content(empty_file)


def test_pdf_validation_invalid_header(tmp_path):
    invalid_file = tmp_path / "fake.pdf"
    invalid_file.write_bytes(b"This is not a real PDF file header.")
    with pytest.raises(PDFValidationError, match="PDF header"):
        validate_pdf_content(invalid_file)


def test_pdf_validation_corrupted_structure(tmp_path):
    corrupted_file = tmp_path / "corrupt.pdf"
    corrupted_file.write_bytes(b"%PDF-1.7\nCorrupted random byte stream %%EOF")
    with pytest.raises(PDFValidationError, match="parse PDF structure"):
        validate_pdf_content(corrupted_file)


def test_text_normalization_preserves_engineering_notation():
    raw = "P/N: VLV-200-A\r\nTolerance: +/- 0.05 mm\r\n\r\n\r\n\r\nPressure: 15.5 bar\x00   "
    cleaned = normalize_extracted_text(raw)
    assert "P/N: VLV-200-A" in cleaned
    assert "+/- 0.05 mm" in cleaned
    assert "Pressure: 15.5 bar" in cleaned
    # Ensure 4 consecutive newlines were collapsed to 2
    assert "\n\n\n" not in cleaned
    # Ensure null character was removed
    assert "\x00" not in cleaned


def test_native_text_sufficiency_heuristic():
    short_text = "Page 1"
    assert is_native_text_sufficient(short_text, min_chars=50) is False

    long_engineering_text = (
        "Part Number: ABC-123. Nominal diameter: 50.0 mm. Test pressure: 20 bar. "
        "Complies with ISO 9001 and ASME Section VIII specifications."
    )
    assert is_native_text_sufficient(long_engineering_text, min_chars=50) is True


def test_process_text_pdf_page_by_page(tmp_path):
    pdf_path = create_sample_text_pdf(tmp_path)
    result = process_pdf_document(pdf_path, min_native_chars=50)

    assert result.total_pages == 2
    assert result.processed_pages == 2
    assert result.ocr_pages == 0

    # Verify 1-based page numbering
    assert result.pages[0].page_number == 1
    assert result.pages[0].extraction_method == "text"
    assert result.pages[0].ocr_used is False
    assert "HYDRAULIC VALVE HV-100" in result.pages[0].text
    assert result.pages[0].character_count > 0
    assert result.pages[0].word_count > 0

    assert result.pages[1].page_number == 2
    assert result.pages[1].extraction_method == "text"
    assert "TORQUE SPECIFICATIONS" in result.pages[1].text


def test_opencv_preprocessing(tmp_path):
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), "TEST OCR", fill=(0, 0, 0))

    preprocessed = preprocess_image_for_ocr(img)
    # Ensure binary 1-channel image output
    assert len(preprocessed.shape) == 2
    assert preprocessed.shape[0] == 100
    assert preprocessed.shape[1] == 200


def test_tesseract_discovery():
    # Verify that Tesseract discovery returns a path or None without crashing
    cmd = find_tesseract_cmd()
    if cmd:
        assert is_tesseract_available() is True


def test_ocr_processing_fallback_on_scanned_pdf(tmp_path):
    scanned_path = create_sample_scanned_pdf(tmp_path)

    if is_tesseract_available():
        result = process_pdf_document(scanned_path, min_native_chars=50)
        assert result.total_pages == 1
        assert result.processed_pages == 1
        assert result.ocr_pages == 1
        page1 = result.pages[0]
        assert page1.page_number == 1
        assert page1.extraction_method == "ocr"
        assert page1.ocr_used is True
        # Tesseract should extract text from the rendered image
        assert len(page1.text) > 0
        assert "VALVE" in page1.text.upper() or "SPECIFICATION" in page1.text.upper()
    else:
        # Unit test with mock when Tesseract is not available
        with patch("app.services.document_processing.processor.perform_ocr", return_value="MOCKED OCR TEXT"):
            result = process_pdf_document(scanned_path, min_native_chars=50)
            assert result.ocr_pages == 1
            assert result.pages[0].extraction_method == "ocr"
            assert result.pages[0].ocr_used is True
            assert result.pages[0].text == "MOCKED OCR TEXT"
