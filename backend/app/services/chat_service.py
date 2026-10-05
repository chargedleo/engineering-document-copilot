from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.schemas.chat import ChatQueryRequest, ChatMessageResponse, Citation, CadReference


class ChatService:
    @staticmethod
    async def get_or_create_session(db: AsyncSession, session_id: Optional[str] = None) -> ChatSession:
        if session_id:
            query = select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages))
            result = await db.execute(query)
            session = result.scalar_one_or_none()
            if session:
                return session

        new_session = ChatSession(title="Engineering Consultation")
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return new_session

    @staticmethod
    async def list_sessions(db: AsyncSession, limit: int = 20) -> List[ChatSession]:
        query = select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_session_history(db: AsyncSession, session_id: str) -> Optional[ChatSession]:
        query = select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def process_copilot_query(
        db: AsyncSession,
        request: ChatQueryRequest
    ) -> ChatMessage:
        """
        Processes user query through the copilot pipeline.
        (Note: AI orchestration with LangGraph, Azure OpenAI & Azure AI Search will be hooked here)
        """
        session = await ChatService.get_or_create_session(db, request.session_id)

        # 1. Record user message
        user_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.USER,
            content=request.query
        )
        db.add(user_message)
        await db.flush()

        # 2. Production AI Placeholder
        # Future: Call LangGraph compiled graph (agents.graph.app.ainvoke)
        copilot_response_content = (
            f"Engineering Copilot acknowledgment: Received inquiry '{request.query}'. "
            "AI reasoning and hybrid retrieval engine is staged and will be connected in the subsequent phase."
        )

        mock_citations = [
            {
                "document_id": "sample-spec-id",
                "document_title": "Turbine Specification v1.0",
                "source_type": "SPECIFICATION",
                "page_number": 4,
                "section": "Section 3.2: Thermal Limits",
                "snippet": "Maximum operating temperature is 1200 deg C under continuous load.",
                "score": 0.95
            }
        ]

        mock_cad_refs = [
            {
                "cad_id": "sample-cad-id",
                "part_number": "TS-402-C",
                "part_name": "Rotor Shaft Assembly",
                "feature_name": "Shaft Journal",
                "bounding_box": {"diameter_mm": 85.0, "length_mm": 420.0}
            }
        ] if request.include_cad_context else []

        assistant_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=copilot_response_content,
            citations=mock_citations,
            cad_references=mock_cad_refs,
            token_count=120
        )
        db.add(assistant_message)
        await db.commit()
        await db.refresh(assistant_message)

        return assistant_message
