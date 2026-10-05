import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.document import DocumentStatus
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.document import (
    DocumentResponse,
    DocumentFilter,
    DocumentCreate,
    DocumentPageResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService
from app.services.document_processing.pdf_extractor import PDFValidationError
from app.services.document_processing.ocr import TesseractNotFoundError
from app.services.document_processing.processor import DocumentProcessingError

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginatedResponse[DocumentResponse]], status_code=status.HTTP_200_OK)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    document_type: Optional[str] = Query(None, description="Filter by document type (e.g. SPECIFICATION, MANUAL)"),
    part_number: Optional[str] = Query(None, description="Filter by part number"),
    status_filter: Optional[DocumentStatus] = Query(None, alias="status", description="Filter by processing status"),
    search: Optional[str] = Query(None, description="Search in filename and part number"),
    db: AsyncSession = Depends(get_db)
):
    """List engineering document metadata with pagination and search filters."""
    filter_params = DocumentFilter(
        document_type=document_type,
        part_number=part_number,
        status=status_filter,
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
    Create engineering document metadata record (Foundational endpoint).
    Does not require physical PDF processing.
    """
    created_doc = await DocumentService.create_document(db, doc_in)
    return ApiResponse(
        success=True,
        message="Document metadata created successfully",
        data=DocumentResponse.model_validate(created_doc)
    )


@router.post("/upload", response_model=ApiResponse[DocumentUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="Engineering PDF file to upload and process"),
    document_type: str = Form("SPECIFICATION", description="Document type (SPECIFICATION, MANUAL, etc.)"),
    part_number: Optional[str] = Form(None, description="Engineering part number"),
    revision: Optional[str] = Form("A", description="Engineering revision identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process an engineering PDF document (Milestone 3 Pipeline):
    - Validates file format and limits.
    - Stores file under local safe storage (data/documents/{document_id}/{filename}).
    - Extracts text page-by-page (PyMuPDF native text + OpenCV/Tesseract OCR fallback).
    - Persists DocumentPage records to database.
    - Updates Document processing status to PROCESSED.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents (.pdf) are supported."
        )

    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty (0 bytes)."
        )

    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file content. Header does not match standard PDF specification."
        )

    try:
        doc, result = await DocumentService.process_and_store_document(
            db=db,
            file_bytes=file_bytes,
            original_filename=file.filename,
            document_type=document_type,
            part_number=part_number,
            revision=revision,
        )

        upload_response = DocumentUploadResponse(
            document_id=doc.id,
            filename=doc.filename,
            status=doc.status,
            page_count=result.total_pages,
            processed_page_count=result.processed_pages,
            ocr_page_count=result.ocr_pages,
        )

        return ApiResponse(
            success=True,
            message="Document uploaded and processed successfully.",
            data=upload_response
        )

    except PDFValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except TesseractNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OCR service unavailable: {str(e)}"
        )
    except DocumentProcessingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{document_id}/pages", response_model=ApiResponse[PaginatedResponse[DocumentPageResponse]], status_code=status.HTTP_200_OK)
async def list_document_pages(
    document_id: str,
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """List extracted pages for a document ordered by 1-based PDF page number."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found"
        )

    skip = (page - 1) * page_size
    pages, total = await DocumentService.list_document_pages(
        db,
        document_id=document_id,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            items=[DocumentPageResponse.model_validate(p) for p in pages],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/{document_id}/pages/{page_number}", response_model=ApiResponse[DocumentPageResponse], status_code=status.HTTP_200_OK)
async def get_document_page(
    document_id: str,
    page_number: int,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve extracted text and metadata for a specific 1-based page number."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found"
        )

    page_obj = await DocumentService.get_document_page(db, document_id, page_number)
    if not page_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_number} for document '{document_id}' not found"
        )

    return ApiResponse(
        success=True,
        data=DocumentPageResponse.model_validate(page_obj)
    )
