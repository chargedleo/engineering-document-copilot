import os
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.document import DocumentStatus
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.document import DocumentResponse, DocumentFilter, DocumentCreate, DocumentUpdate
from app.services.document_service import DocumentService

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginatedResponse[DocumentResponse]], status_code=status.HTTP_200_OK)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    document_type: Optional[str] = Query(None, description="Filter by document type (e.g. SPECIFICATION, MANUAL)"),
    part_number: Optional[str] = Query(None, description="Filter by part number"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by processing status"),
    search: Optional[str] = Query(None, description="Search in filename and part number"),
    db: AsyncSession = Depends(get_db)
):
    """List engineering document metadata with pagination and search filters."""
    filter_params = DocumentFilter(
        document_type=document_type,
        part_number=part_number,
        status=status,
        search_query=search
    )
    skip = (page - 1) * page_size
    documents, total = await DocumentService.list_documents(
        db,
        skip=skip,
        limit=page_size,
        filter_params=filter_params
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            items=[DocumentResponse.model_validate(d) for d in documents],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/{document_id}", response_model=ApiResponse[DocumentResponse], status_code=status.HTTP_200_OK)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve document metadata by unique ID."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found"
        )
    return ApiResponse(
        success=True,
        data=DocumentResponse.model_validate(doc)
    )


@router.post("", response_model=ApiResponse[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def create_document(doc_in: DocumentCreate, db: AsyncSession = Depends(get_db)):
    """
    Create engineering document metadata record (Milestone 2 foundational endpoint).
    Does not require physical PDF processing.
    """
    created_doc = await DocumentService.create_document(db, doc_in)
    return ApiResponse(
        success=True,
        message="Document metadata created successfully",
        data=DocumentResponse.model_validate(created_doc)
    )


@router.post("/upload", response_model=ApiResponse[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("SPECIFICATION"),
    part_number: Optional[str] = Form(None),
    revision: Optional[str] = Form("A"),
    db: AsyncSession = Depends(get_db)
):
    """Optional file upload endpoint staging files to data/documents/."""
    os.makedirs(settings.DOCUMENTS_STORAGE_DIR, exist_ok=True)
    destination_path = os.path.join(settings.DOCUMENTS_STORAGE_DIR, file.filename)

    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(destination_path)

    doc_create = DocumentCreate(
        filename=file.filename,
        document_type=document_type,
        part_number=part_number,
        revision=revision,
        file_path=destination_path,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=file_size,
        metadata_payload={"original_filename": file.filename}
    )

    created_doc = await DocumentService.create_document(db, doc_create)
    return ApiResponse(
        success=True,
        message="Document uploaded and metadata staged successfully.",
        data=DocumentResponse.model_validate(created_doc)
    )
