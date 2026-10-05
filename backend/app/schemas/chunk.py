import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class SearchMode(str, enum.Enum):
    KEYWORD = "keyword"
    VECTOR = "vector"
    HYBRID = "hybrid"


class DocumentChunkBase(BaseModel):
    document_id: str = Field(..., description="Parent document identifier")
    page_id: Optional[str] = Field(default=None, description="Parent document page identifier")
    chunk_index: int = Field(..., ge=0, description="Sequential 0-indexed position within the document")
    page_number: int = Field(..., ge=1, description="1-indexed human-friendly page number")
    content: str = Field(..., min_length=1, description="Text content of the chunk")
    character_count: int = Field(default=0, ge=0, description="Number of characters in content")
    word_count: int = Field(default=0, ge=0, description="Number of words in content")
    metadata_payload: Optional[Dict[str, Any]] = Field(default=None, description="Metadata tags, section title, parent info")
    embedding_status: str = Field(default="pending", description="Status of embedding generation: pending, completed, failed")


class DocumentChunkCreate(DocumentChunkBase):
    embedding: Optional[List[float]] = Field(default=None, description="Dense embedding vector")


class DocumentChunkResponse(DocumentChunkBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class ChunkGenerateResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    embeddings_generated: int
    indexed_count: int
    status: str


class SearchFilters(BaseModel):
    document_id: Optional[str] = Field(default=None, description="Filter by document ID")
    document_type: Optional[str] = Field(default=None, description="Filter by document type (e.g. SPECIFICATION, MANUAL)")
    part_number: Optional[str] = Field(default=None, description="Filter by engineering part number")
    revision: Optional[str] = Field(default=None, description="Filter by document revision")
    page_number: Optional[int] = Field(default=None, ge=1, description="Filter by specific page number")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Technical engineering search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of chunks to return")
    mode: SearchMode = Field(default=SearchMode.HYBRID, description="Retrieval mode: keyword, vector, or hybrid")
    filters: Optional[SearchFilters] = Field(default=None, description="Metadata filters")


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    page_id: Optional[str] = None
    page_number: int
    chunk_index: int
    filename: str
    document_type: str
    part_number: Optional[str] = None
    revision: Optional[str] = None
    content: str
    score: float
    retrieval_mode: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    mode: str
    total_results: int
    results: List[SearchResultItem]
