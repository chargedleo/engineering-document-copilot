from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.document import DocumentStatus, ExtractionMethod


class DocumentBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Name of the engineering document file")
    document_type: str = Field(default="SPECIFICATION", max_length=50, description="Type: SPECIFICATION, MANUAL, DATASHEET, DRAWING, BOM, etc.")
    part_number: Optional[str] = Field(default=None, max_length=100, description="Associated engineering part or assembly number")
    revision: Optional[str] = Field(default="A", max_length=50, description="Engineering revision identifier (e.g., Rev A, Rev 2.1)")
    file_path: Optional[str] = Field(default=None, max_length=1024, description="Local or remote storage path if staged")
    mime_type: Optional[str] = Field(default="application/pdf", max_length=128, description="MIME content type")
    file_size_bytes: Optional[int] = Field(default=0, ge=0, description="File size in bytes")
    metadata_payload: Optional[Dict[str, Any]] = Field(default=None, description="Arbitrary technical metadata, tags, author, etc.")


class DocumentCreate(DocumentBase):
    """Schema for creating foundational document metadata."""
    pass


class DocumentUpdate(BaseModel):
    document_type: Optional[str] = None
    part_number: Optional[str] = None
    revision: Optional[str] = None
    status: Optional[DocumentStatus] = None
    error_message: Optional[str] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class DocumentPageBase(BaseModel):
    page_number: int = Field(..., ge=1, description="Human-friendly 1-indexed PDF page number")
    extraction_method: ExtractionMethod = Field(default=ExtractionMethod.TEXT, description="Method used: text or ocr")
    ocr_used: bool = Field(default=False, description="Whether OCR was triggered for this page")
    character_count: int = Field(default=0, ge=0, description="Extracted character count")
    word_count: int = Field(default=0, ge=0, description="Extracted word count")
    text: str = Field(default="", description="Cleaned extracted text content")


class DocumentPageResponse(DocumentPageBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    created_at: datetime
    updated_at: datetime


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: DocumentStatus
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    page_count: Optional[int] = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    page_count: int
    processed_page_count: int
    ocr_page_count: int


class DocumentFilter(BaseModel):
    document_type: Optional[str] = None
    part_number: Optional[str] = None
    status: Optional[DocumentStatus] = None
    search_query: Optional[str] = None
