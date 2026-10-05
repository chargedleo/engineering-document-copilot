import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.rag import RAGQueryRequest, RAGResponse
from app.services.rag_service import RAGService

logger = logging.getLogger("engineering_copilot.api.rag")
router = APIRouter()


@router.post("/query", response_model=ApiResponse[RAGResponse], status_code=status.HTTP_200_OK)
async def query_rag(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute grounded Retrieval-Augmented Generation (RAG) query against indexed engineering documents.

    Retrieves evidence via hybrid keyword + vector search, constructs an isolated context,
    synthesizes a grounded answer with strict engineering precision, extracts citations,
    and reports evidence sufficiency.
    """
    try:
        response = await RAGService.answer_question(db, request)
        return ApiResponse(
            success=True,
            data=response,
            message="RAG answer synthesized successfully." if response.sufficient_evidence else "Insufficient evidence to answer query."
        )
    except ValueError as e:
        logger.warning(f"RAG query validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"RAG query execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG synthesis failed: {str(e)}"
        )
