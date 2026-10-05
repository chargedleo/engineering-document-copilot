import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.chunk import SearchRequest, SearchResponse
from app.services.search_service import SearchService

logger = logging.getLogger("engineering_copilot.api.search")
router = APIRouter()


@router.post("", response_model=ApiResponse[SearchResponse], status_code=status.HTTP_200_OK)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search engineering document chunks via keyword, vector, or hybrid retrieval
    with metadata filtering (document_id, document_type, part_number, revision, page_number).
    """
    try:
        response = await SearchService.execute_search(db, request)
        return ApiResponse(
            success=True,
            data=response,
            message=f"Found {response.total_results} matching chunks via {response.mode} search."
        )
    except Exception as e:
        logger.error(f"Search execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
