from app.services.document_processing.ocr import (
    find_tesseract_cmd,
    is_tesseract_available,
    preprocess_image_for_ocr,
    perform_ocr,
    TesseractNotFoundError,
)
from app.services.document_processing.pdf_extractor import (
    validate_pdf_content,
    extract_native_page_text,
    render_page_to_image,
    normalize_extracted_text,
    PDFValidationError,
)
from app.services.document_processing.processor import (
    process_pdf_document,
    ProcessedPageResult,
    ProcessedDocumentResult,
    DocumentProcessingError,
    is_native_text_sufficient,
)

__all__ = [
    "find_tesseract_cmd",
    "is_tesseract_available",
    "preprocess_image_for_ocr",
    "perform_ocr",
    "TesseractNotFoundError",
    "validate_pdf_content",
    "extract_native_page_text",
    "render_page_to_image",
    "normalize_extracted_text",
    "PDFValidationError",
    "process_pdf_document",
    "ProcessedPageResult",
    "ProcessedDocumentResult",
    "DocumentProcessingError",
    "is_native_text_sufficient",
]
