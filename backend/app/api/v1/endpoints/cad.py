from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.cad import CadMetadataResponse, CadMetadataCreate, CadFilter
from app.services.cad_service import CadService

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginatedResponse[CadMetadataResponse]])
async def list_cad_metadata(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    part_number: Optional[str] = None,
    material: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List CAD parts and geometry metadata records."""
    filter_params = CadFilter(part_number=part_number, material=material, search_query=search)
    skip = (page - 1) * page_size
    records, total = await CadService.list_cad_metadata(db, skip=skip, limit=page_size, filter_params=filter_params)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            items=[CadMetadataResponse.model_validate(r) for r in records],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/{cad_id}", response_model=ApiResponse[CadMetadataResponse])
async def get_cad_metadata(cad_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve detailed CAD metadata by ID."""
    cad_record = await CadService.get_cad_metadata_by_id(db, cad_id)
    if not cad_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CAD metadata not found")
    return ApiResponse(success=True, data=CadMetadataResponse.model_validate(cad_record))


@router.get("/by-document/{document_id}", response_model=ApiResponse[List[CadMetadataResponse]])
async def get_cad_by_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve CAD records associated with a specific document."""
    records = await CadService.get_cad_by_document_id(db, document_id)
    return ApiResponse(
        success=True,
        data=[CadMetadataResponse.model_validate(r) for r in records]
    )
