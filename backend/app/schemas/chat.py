from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.chat import MessageRole


class Citation(BaseModel):
    document_id: str
    document_title: str
    source_type: str  # e.g., 'SPECIFICATION', 'MANUAL', 'CAD_METADATA'
    page_number: Optional[int] = None
    section: Optional[str] = None
    snippet: str
    score: Optional[float] = None


class CadReference(BaseModel):
    cad_id: str
    part_number: str
    part_name: Optional[str] = None
    feature_name: Optional[str] = None
    bounding_box: Optional[Dict[str, Any]] = None


class ChatMessageBase(BaseModel):
    role: MessageRole
    content: str
    citations: Optional[List[Citation]] = None
    cad_references: Optional[List[CadReference]] = None


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    token_count: Optional[int] = None
    created_at: datetime


class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Engineering Inquiry"


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []


class ChatQueryRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    document_ids: Optional[List[str]] = None
    include_cad_context: bool = True
