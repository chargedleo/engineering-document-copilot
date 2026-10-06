import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union
import pymupdf as fitz

from app.core.config import settings
from app.services.document_processing.pdf_extractor import (
    validate_pdf_content,
    extract_native_page_text,
    render_page_to_image,
)
from app.services.document_processing.ocr import perform_ocr, is_tesseract_available

logger = logging.getLogger("engineering_copilot.processor")


@dataclass
class ProcessedPageResult:
    page_number: int  # 1-indexed
    text: str
    extraction_method: str  # "text" or "ocr"
    ocr_used: bool
    character_count: int
    word_count: int


@dataclass
class ProcessedDocumentResult:
    total_pages: int
    processed_pages: int
    ocr_pages: int
    pages: List[ProcessedPageResult]


class DocumentProcessingError(Exception):
    """Raised when PDF processing or OCR fails."""
    pass


def is_native_text_sufficient(text: str, min_chars: int) -> bool:
    """
    Scanned Page Detection Heuristic:
    Evaluates whether the natively extracted text contains enough non-whitespace
    characters to represent a digital document page rather than a scanned image.

    Heuristic criteria:
    - Counts alphanumeric and printable non-whitespace characters.
    - If count >= min_chars, native text extraction is considered sufficient.
    - If count < min_chars, the page is flagged as requiring OCR fallback.
    """
    non_space_chars = len(re.sub(r"\s+", "", text))
    return non_space_chars >= min_chars


def process_pdf_document(
    file_path: Union[str, Path],
    min_native_chars: int = None,
    ocr_dpi: int = None
) -> ProcessedDocumentResult:
    """
    Process an engineering PDF page-by-page.
    1. Validates the PDF structure and limits.
    2. Sequentially extracts native text using PyMuPDF.
    3. Evaluates native text sufficiency against `min_native_chars`.
    4. Triggers OCR via OpenCV preprocessing and Tesseract only when native text is insufficient.
    5. Returns page-by-page extraction results with 1-based page numbering.
    """
    if min_native_chars is None:
        min_native_chars = settings.PDF_MIN_NATIVE_TEXT_CHARS
    if ocr_dpi is None:
        ocr_dpi = settings.OCR_DPI

    path = Path(file_path)
    logger.info(f"Starting document processing for: {path.name}")

    # 1. Validate PDF
    validation_info = validate_pdf_content(path)
    page_count = validation_info["page_count"]
    logger.info(f"PDF validated successfully: {path.name} ({page_count} pages, {validation_info['file_size_bytes']} bytes)")

    doc = fitz.open(str(path))
    results: List[ProcessedPageResult] = []
    ocr_count = 0

    try:
        for idx in range(page_count):
            page_num = idx + 1  # 1-indexed human-friendly page number
            page = doc.load_page(idx)

            # Step 1: Attempt native text extraction
            native_text = extract_native_page_text(page)

            # Step 2: Apply scanned page heuristic
            if is_native_text_sufficient(native_text, min_native_chars):
                final_text = native_text
                method = "text"
                ocr_flag = False
                logger.debug(f"Page {page_num}/{page_count}: Native text sufficient ({len(final_text)} chars).")
            else:
                # Step 3: Insufficient native text -> Trigger OCR fallback
                logger.info(
                    f"Page {page_num}/{page_count}: Insufficient native text ({len(native_text.strip())} chars < {min_native_chars}); "
                    f"triggering OCR fallback."
                )
                try:
                    # Render page to image at specified DPI
                    page_img = render_page_to_image(page, dpi=ocr_dpi)
                    ocr_text = perform_ocr(page_img)

                    # Prefer OCR text if available; if OCR also produced empty (e.g. blank page),
                    # retain whatever text was found
                    final_text = ocr_text if len(ocr_text) > len(native_text) else (ocr_text or native_text)
                    method = "ocr"
                    ocr_flag = True
                    ocr_count += 1
                    logger.info(f"Page {page_num}/{page_count}: OCR completed successfully ({len(final_text)} chars).")
                except Exception as ocr_err:
                    logger.warning(
                        f"Page {page_num}/{page_count}: OCR failed or unavailable ({str(ocr_err)}). Falling back to native text."
                    )
                    # If OCR failed (e.g. Tesseract missing), fall back to whatever native text exists
                    final_text = native_text
                    method = "text"
                    ocr_flag = False

            char_count = len(final_text)
            word_count = len(final_text.split())

            results.append(
                ProcessedPageResult(
                    page_number=page_num,
                    text=final_text,
                    extraction_method=method,
                    ocr_used=ocr_flag,
                    character_count=char_count,
                    word_count=word_count,
                )
            )

        logger.info(
            f"Completed processing for {path.name}: {len(results)} pages processed ({ocr_count} via OCR)."
        )

        return ProcessedDocumentResult(
            total_pages=page_count,
            processed_pages=len(results),
            ocr_pages=ocr_count,
            pages=results,
        )

    except Exception as e:
        logger.error(f"Error processing PDF document {path.name}: {str(e)}", exc_info=True)
        raise DocumentProcessingError(f"Failed to process document {path.name}: {str(e)}") from e
    finally:
        doc.close()
