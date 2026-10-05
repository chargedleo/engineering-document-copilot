import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.agent import AgentQueryRequest, AgentResponse
from app.services.agent_service import AgentService

logger = logging.getLogger("engineering_copilot.api.agent")
router = APIRouter()


@router.post("/query", response_model=ApiResponse[AgentResponse], status_code=status.HTTP_200_OK)
async def query_agent(
    request: AgentQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute autonomous LangGraph Engineering Copilot Agent query.

    The agent dynamically decides and routes across engineering tools:
    - Search Engineering Documents (M4 hybrid retrieval)
    - Document Metadata Lookup (PostgreSQL verified specs)
    - Engineering Calculator (deterministic unit conversions)

    Returns a grounded technical synthesis with citations, tool execution traces,
    and provenance metadata.
    """
    try:
        response = await AgentService.run_agent(db, request)
        message = (
            "Agent synthesized grounded response."
            if not response.should_abstain
            else "Agent abstained: insufficient engineering evidence."
        )
        return ApiResponse(
            success=True,
            data=response,
            message=message,
        )
    except ValueError as e:
        logger.warning(f"Agent query validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow failed: {str(e)}",
        )
