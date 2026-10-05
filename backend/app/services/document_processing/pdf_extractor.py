import io
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Union
import fitz  # PyMuPDF
from PIL import Image

from app.core.config import settings

logger = logging.getLogger("engineering_copilot.pdf_extractor")


class PDFValidationError(ValueError):
    """Raised when an uploaded file fails PDF structure or security validation."""
    pass


def validate_pdf_content(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate that a file is a valid, readable, unencrypted PDF and within configured limits.
    Returns basic metadata dictionary: {page_count, file_size_bytes}.
    """
    path = Path(file_path)
    if not path.is_file():
        raise PDFValidationError(f"File not found or inaccessible: {path.name}")

    file_size = path.stat().st_size
    if file_size == 0:
        raise PDFValidationError("The uploaded file is empty (0 bytes).")

    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise PDFValidationError(
            f"File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    # Validate PDF magic bytes (%PDF-)
    with open(path, "rb") as f:
        header = f.read(5)
        if not header.startswith(b"%PDF-"):
            raise PDFValidationError("Invalid file format. File does not start with valid PDF header (%PDF-).")

    # Validate structure by opening with PyMuPDF
    try:
        doc = fitz.open(str(path))
    except Exception as e:
        raise PDFValidationError(f"Could not parse PDF structure: {str(e)}")

    try:
        if doc.is_encrypted:
            raise PDFValidationError("Encrypted or password-protected PDFs are not supported.")

        page_count = doc.page_count
        if page_count < 1:
            raise PDFValidationError("PDF document contains no pages.")

        if page_count > settings.MAX_PDF_PAGES:
            raise PDFValidationError(
                f"PDF has {page_count} pages, which exceeds the maximum limit of {settings.MAX_PDF_PAGES} pages."
            )

        return {
            "page_count": page_count,
            "file_size_bytes": file_size,
        }
    finally:
        doc.close()


def normalize_extracted_text(raw_text: str) -> str:
    """
    Clean extracted text without destroying technical engineering notations, symbols,
    units, tolerances (+/-), part numbers, decimals, or hyphens.
    - Strips carriage returns and null bytes.
    - Strips trailing spaces per line while preserving line boundaries.
    - Consolidates 3 or more consecutive blank lines into 2.
    """
    if not raw_text:
        return ""

    # Remove null characters and replace CRLF with LF
    text = raw_text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")

    # Normalize trailing whitespace per line
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Collapse excessive consecutive newlines (3+ -> 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_native_page_text(page: fitz.Page) -> str:
    """
    Extract text using PyMuPDF while preserving reading layout.
    """
    raw_text = page.get_text("text")
    return normalize_extracted_text(raw_text)


def render_page_to_image(page: fitz.Page, dpi: int = 300) -> Image.Image:
    """
    Render a PDF page to a high-resolution PIL Image for OCR processing.
    Ensures memory resources are released.
    """
    # 72 DPI is base resolution; scale matrix for desired DPI
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    try:
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        return image
    finally:
        # Free pixmap native memory
        pix = None
