import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document, DocumentStatus, DocumentPage, DocumentChunk, ExtractionMethod
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentFilter
from app.schemas.chunk import ChunkGenerateResponse
from app.services.chunking import EngineeringDocumentChunker, PageInput
from app.services.embeddings import get_embedding_provider
from app.services.search import get_search_index
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

    @staticmethod
    async def generate_document_chunks(
        db: AsyncSession,
        document_id: str
    ) -> ChunkGenerateResponse:
        """
        Transform a processed document's DocumentPage records into structural chunks,
        generate dense embeddings, persist DocumentChunk records, and index into search index.
        """
        doc = await DocumentService.get_document_by_id(db, document_id)
        if not doc:
            raise ValueError(f"Document with ID {document_id} not found.")

        pages_query = select(DocumentPage).where(
            DocumentPage.document_id == document_id
        ).order_by(DocumentPage.page_number.asc())
        pages_result = await db.execute(pages_query)
        pages = list(pages_result.scalars().all())

        if not pages:
            raise ValueError(f"Document {document_id} has no extracted pages to chunk. Run document processing first.")

        # 1. Chunk document pages using structural engineering chunker
        chunker = EngineeringDocumentChunker(
            chunk_size_chars=settings.CHUNK_SIZE_CHARS,
            chunk_overlap_chars=settings.CHUNK_OVERLAP_CHARS,
        )
        page_inputs = [
            PageInput(page_id=p.id, page_number=p.page_number, text=p.text)
            for p in pages
        ]
        doc_metadata = {
            "document_id": doc.id,
            "filename": doc.filename,
            "document_type": doc.document_type,
            "part_number": doc.part_number,
            "revision": doc.revision,
        }
        chunk_outputs = chunker.chunk_document_pages(pages=page_inputs, document_metadata=doc_metadata)

        # 2. Clean up any existing chunks for this document (idempotent re-generation)
        delete_stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        await db.execute(delete_stmt)
        await db.flush()

        search_index = get_search_index()
        await search_index.delete_document_chunks(document_id)

        if not chunk_outputs:
            await db.commit()
            return ChunkGenerateResponse(
                document_id=doc.id,
                filename=doc.filename,
                chunks_created=0,
                embeddings_generated=0,
                indexed_count=0,
                status="completed",
            )

        # 3. Generate embeddings for each chunk
        texts_to_embed = [c.content for c in chunk_outputs]
        embedding_provider = get_embedding_provider()
        embeddings = await embedding_provider.embed_texts(texts_to_embed)

        # 4. Persist DocumentChunk records to database
        db_chunks: List[DocumentChunk] = []
        for c_out, emb in zip(chunk_outputs, embeddings):
            db_chunk = DocumentChunk(
                document_id=doc.id,
                page_id=c_out.page_id,
                chunk_index=c_out.chunk_index,
                page_number=c_out.page_number,
                content=c_out.content,
                character_count=c_out.character_count,
                word_count=c_out.word_count,
                metadata_payload=c_out.metadata_payload,
                embedding=emb,
                embedding_status="completed",
            )
            db.add(db_chunk)
            db_chunks.append(db_chunk)

        await db.commit()
        for chunk in db_chunks:
            await db.refresh(chunk)

        # 5. Push to search index
        index_records = [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "page_id": chunk.page_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "filename": doc.filename,
                "document_type": doc.document_type,
                "part_number": doc.part_number,
                "revision": doc.revision,
                "content": chunk.content,
                "embedding": chunk.embedding,
                "metadata": chunk.metadata_payload or {},
            }
            for chunk in db_chunks
        ]
        indexed_count = await search_index.index_chunks(index_records)

        logger.info(
            f"Successfully generated {len(db_chunks)} chunks and {len(embeddings)} embeddings "
            f"for document {doc.id} ({doc.filename}); {indexed_count} indexed into search."
        )

        return ChunkGenerateResponse(
            document_id=doc.id,
            filename=doc.filename,
            chunks_created=len(db_chunks),
            embeddings_generated=len(embeddings),
            indexed_count=indexed_count,
            status="completed",
        )

    @staticmethod
    async def list_document_chunks(
        db: AsyncSession,
        document_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[DocumentChunk], int]:
        """List chunks for a document ordered by chunk_index."""
        query = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        query = query.order_by(DocumentChunk.chunk_index.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        chunks = list(result.scalars().all())

        return chunks, total

    @staticmethod
    async def get_document_chunk(
        db: AsyncSession,
        chunk_id: str
    ) -> Optional[DocumentChunk]:
        """Retrieve a specific chunk record by UUID."""
        query = select(DocumentChunk).where(DocumentChunk.id == chunk_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

