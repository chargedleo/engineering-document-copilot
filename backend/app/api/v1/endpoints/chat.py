from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.chat import (
    ChatQueryRequest,
    ChatMessageResponse,
    ChatSessionResponse,
    ChatSessionCreate
)
from app.services.chat_service import ChatService

router = APIRouter()


@router.get("/sessions", response_model=ApiResponse[List[ChatSessionResponse]])
async def list_sessions(limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """List recent copilot chat sessions."""
    sessions = await ChatService.list_sessions(db, limit=limit)
    return ApiResponse(
        success=True,
        data=[ChatSessionResponse.model_validate(s) for s in sessions]
    )


@router.post("/sessions", response_model=ApiResponse[ChatSessionResponse], status_code=status.HTTP_201_CREATED)
async def create_session(session_in: Optional[ChatSessionCreate] = None, db: AsyncSession = Depends(get_db)):
    """Create a new chat session."""
    session = await ChatService.get_or_create_session(db)
    return ApiResponse(success=True, data=ChatSessionResponse.model_validate(session))


@router.get("/sessions/{session_id}", response_model=ApiResponse[ChatSessionResponse])
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve full conversation history for a session."""
    session = await ChatService.get_session_history(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return ApiResponse(success=True, data=ChatSessionResponse.model_validate(session))


@router.post("/query", response_model=ApiResponse[ChatMessageResponse])
async def query_copilot(request: ChatQueryRequest, db: AsyncSession = Depends(get_db)):
    """Submit a query to the Engineering Copilot."""
    response_msg = await ChatService.process_copilot_query(db, request)
    return ApiResponse(
        success=True,
        data=ChatMessageResponse.model_validate(response_msg)
    )
