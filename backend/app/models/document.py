import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
from sqlalchemy import String, BigInteger, Enum, ForeignKey, JSON, Float, DateTime
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
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


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

    # CAD metadata relationship (future extension, simplified for Milestone 2)
    cad_metadata: Mapped[List["CadMetadata"]] = relationship(
        "CadMetadata",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin"
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
