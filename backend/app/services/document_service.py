from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentFilter


class DocumentService:
    """Service layer for engineering document management."""

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
