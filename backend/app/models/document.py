import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
from sqlalchemy import (
    String,
    BigInteger,
    Enum,
    ForeignKey,
    JSON,
    Float,
    DateTime,
    Integer,
    Boolean,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DocumentType(str, enum.Enum):
    SPECIFICATION = "SPECIFICATION"
    MANUAL = "MANUAL"
    DATASHEET = "DATASHEET"
    DRAWING = "DRAWING"
    BOM = "BOM"
    OTHER = "OTHER"


class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExtractionMethod(str, enum.Enum):
    TEXT = "text"
    OCR = "ocr"


class Document(Base, TimestampMixin):
    """
    Foundational Document entity representing engineering specifications, manuals,
    datasheets, and technical documentation.
    """
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(50), default="SPECIFICATION", nullable=False, index=True)
    part_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    revision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="A")
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, default="application/pdf")
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.PENDING, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    metadata_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Document pages relationship (Milestone 3)
    pages: Mapped[List["DocumentPage"]] = relationship(
        "DocumentPage",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentPage.page_number",
        lazy="selectin"
    )

    # Document chunks relationship (Milestone 4)
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
        lazy="selectin"
    )

    # CAD metadata relationship (future extension, simplified for Milestone 2)
    cad_metadata: Mapped[List["CadMetadata"]] = relationship(
        "CadMetadata",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class DocumentPage(Base, TimestampMixin):
    """
    Page-level extracted text and OCR metadata for an engineering document.
    """
    __tablename__ = "document_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    extraction_method: Mapped[ExtractionMethod] = mapped_column(
        Enum(ExtractionMethod, name="extractionmethod", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ExtractionMethod.TEXT
    )
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ocr_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationship back to document
    document: Mapped["Document"] = relationship("Document", back_populates="pages")

    # Relationship to chunks
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_document_pages_document_page"),
    )


class DocumentChunk(Base, TimestampMixin):
    """
    Structural search chunk representing an engineering document subsection.
    Preserves page boundaries, document identity, character counts, and embedding vectors.
    """
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    page_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("document_pages.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    embedding_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    page: Mapped[Optional["DocumentPage"]] = relationship("DocumentPage", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_chunk_index"),
    )


class CadMetadata(Base, TimestampMixin):
    """
    Scaffold for future CAD metadata extensions.
    (Geometric kernel calculations deferred to future milestones)
    """
    __tablename__ = "cad_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    part_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    part_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    mass_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume_cm3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounding_box_dimensions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="cad_metadata")
