from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic service liveness check."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0"
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(response: Response, db: AsyncSession = Depends(get_db)):
    """Readiness check validating database connectivity."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unreachable: {str(e)}"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "database": db_status,
        "azure_openai_configured": bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY),
        "azure_search_configured": bool(settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_API_KEY),
    }
