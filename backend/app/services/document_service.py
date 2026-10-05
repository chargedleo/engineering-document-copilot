import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document, DocumentStatus, DocumentPage, ExtractionMethod
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentFilter
from app.services.document_processing.processor import (
    process_pdf_document,
    ProcessedDocumentResult,
    DocumentProcessingError,
)
from app.services.document_processing.pdf_extractor import PDFValidationError

logger = logging.getLogger("engineering_copilot.document_service")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an uploaded filename to prevent directory traversal and filesystem attacks.
    Extracts only the terminal filename component and strips dangerous characters.
    """
    base_name = Path(filename).name
    cleaned = re.sub(r'[\\/*?:"<>|\x00]', "_", base_name).strip()
    return cleaned or "uploaded_document.pdf"


def sanitize_error_message(err_msg: str) -> str:
    """
    Remove sensitive local filesystem paths and tracebacks from error strings.
    """
    # Replace Windows drive paths and Unix paths
    cleaned = re.sub(r'[A-Za-z]:\\[^\s"\']+', "[redacted_path]", err_msg)
    cleaned = re.sub(r'/(?:[a-zA-Z0-9_\-\.]+/)+[a-zA-Z0-9_\-\.]+', "[redacted_path]", cleaned)
    return cleaned[:1000]


class DocumentService:
    """Service layer for engineering document management and document intelligence."""

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        filter_params: Optional[DocumentFilter] = None
    ) -> Tuple[List[Document], int]:
        query = select(Document)

        if filter_params:
            if filter_params.document_type:
                query = query.where(Document.document_type.ilike(f"%{filter_params.document_type}%"))
            if filter_params.part_number:
                query = query.where(Document.part_number.ilike(f"%{filter_params.part_number}%"))
            if filter_params.status:
                query = query.where(Document.status == filter_params.status)
            if filter_params.search_query:
                term = f"%{filter_params.search_query}%"
                query = query.where(
                    or_(
                        Document.filename.ilike(term),
                        Document.part_number.ilike(term)
                    )
                )

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        documents = list(result.scalars().all())

        return documents, total

    @staticmethod
    async def get_document_by_id(db: AsyncSession, doc_id: str) -> Optional[Document]:
        query = select(Document).where(Document.id == doc_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_document(db: AsyncSession, doc_in: DocumentCreate) -> Document:
        """Create document metadata in database."""
        db_doc = Document(
            filename=doc_in.filename,
            document_type=doc_in.document_type,
            part_number=doc_in.part_number,
            revision=doc_in.revision,
            file_path=doc_in.file_path,
            mime_type=doc_in.mime_type,
            file_size_bytes=doc_in.file_size_bytes or 0,
            status=DocumentStatus.PENDING,
            metadata_payload=doc_in.metadata_payload,
        )
        db.add(db_doc)
        await db.commit()
        await db.refresh(db_doc)
        return db_doc

    @staticmethod
    async def update_document(db: AsyncSession, doc_id: str, doc_update: DocumentUpdate) -> Optional[Document]:
        doc = await DocumentService.get_document_by_id(db, doc_id)
        if not doc:
            return None

        update_data = doc_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(doc, key, value)

        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def process_and_store_document(
        db: AsyncSession,
        file_bytes: bytes,
        original_filename: str,
        document_type: str = "SPECIFICATION",
        part_number: Optional[str] = None,
        revision: Optional[str] = "A"
    ) -> Tuple[Document, ProcessedDocumentResult]:
        """
        Execute full Milestone 3 ingestion pipeline:
        1. Sanitize filename and create Document record (status: PENDING).
        2. Store file safely under data/documents/{document_id}/{filename}.
        3. Transition status to PROCESSING.
        4. Validate and process PDF page-by-page (PyMuPDF native extraction + OCR fallback).
        5. Persist DocumentPage records to database.
        6. Transition status to PROCESSED (or FAILED on error).
        """
        safe_name = sanitize_filename(original_filename)
        file_size = len(file_bytes)

        # 1. Create Document record
        doc = Document(
            filename=safe_name,
            document_type=document_type,
            part_number=part_number,
            revision=revision,
            file_size_bytes=file_size,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
            metadata_payload={"original_filename": original_filename}
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        logger.info(f"Document record created: ID={doc.id}, file={safe_name}")

        # 2. Local file storage: data/documents/{document_id}/{safe_filename}
        base_dir = Path(settings.DOCUMENTS_STORAGE_DIR).resolve()
        target_dir = base_dir / doc.id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file_path = (target_dir / safe_name).resolve()

        # Enforce path containment
        if not target_file_path.is_relative_to(base_dir):
            doc.status = DocumentStatus.FAILED
            doc.error_message = "Invalid storage destination path."
            await db.commit()
            raise ValueError("Path traversal attempt detected in filename.")

        try:
            with open(target_file_path, "wb") as f:
                f.write(file_bytes)

            # Update document file_path (stored relative to project or absolute safe path)
            doc.file_path = str(target_file_path)
            doc.status = DocumentStatus.PROCESSING
            await db.commit()

            logger.info(f"Document {doc.id} set to PROCESSING; beginning extraction.")

            # 3. Process PDF page-by-page
            processing_result = process_pdf_document(target_file_path)

            # 4. Save DocumentPage records
            for p in processing_result.pages:
                method_enum = (
                    ExtractionMethod.OCR
                    if p.extraction_method.lower() == "ocr"
                    else ExtractionMethod.TEXT
                )
                page_record = DocumentPage(
                    document_id=doc.id,
                    page_number=p.page_number,
                    text=p.text,
                    extraction_method=method_enum,
                    character_count=p.character_count,
                    word_count=p.word_count,
                    ocr_used=p.ocr_used
                )
                db.add(page_record)

            # 5. Mark document as PROCESSED
            doc.status = DocumentStatus.PROCESSED
            doc.metadata_payload = {
                **(doc.metadata_payload or {}),
                "page_count": processing_result.total_pages,
                "ocr_page_count": processing_result.ocr_pages,
            }
            await db.commit()
            await db.refresh(doc)

            logger.info(
                f"Document {doc.id} processed successfully: {processing_result.total_pages} pages "
                f"({processing_result.ocr_pages} via OCR)."
            )
            return doc, processing_result

        except Exception as e:
            logger.error(f"Processing failed for document {doc.id}: {str(e)}", exc_info=True)
            doc.status = DocumentStatus.FAILED
            doc.error_message = sanitize_error_message(str(e))
            await db.commit()
            raise

    @staticmethod
    async def list_document_pages(
        db: AsyncSession,
        document_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[DocumentPage], int]:
        """List extracted pages for a document ordered by 1-based page number."""
        query = select(DocumentPage).where(DocumentPage.document_id == document_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        query = query.order_by(DocumentPage.page_number.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        pages = list(result.scalars().all())

        return pages, total

    @staticmethod
    async def get_document_page(
        db: AsyncSession,
        document_id: str,
        page_number: int
    ) -> Optional[DocumentPage]:
        """Retrieve a specific page record by 1-based page number."""
        query = select(DocumentPage).where(
            DocumentPage.document_id == document_id,
            DocumentPage.page_number == page_number
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
