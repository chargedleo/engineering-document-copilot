from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chunk import SearchMode, SearchFilters


class RAGQueryRequest(BaseModel):
    """Input payload for grounded engineering RAG question answering."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Technical engineering question to answer from document intelligence"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of candidate chunks to retrieve and evaluate"
    )
    retrieval_mode: SearchMode = Field(
        default=SearchMode.HYBRID,
        description="Retrieval strategy: keyword, vector, or hybrid (RRF)"
    )
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional metadata filters (part_number, revision, document_type, etc.)"
    )


class CitationItem(BaseModel):
    """Grounding citation referencing exact source document, page, and chunk."""
    model_config = ConfigDict(from_attributes=True)

    citation_id: str = Field(..., description="In-text citation label e.g. C1, C2")
    document_id: str = Field(..., description="Source document UUID")
    filename: str = Field(..., description="Original filename of the engineering document")
    page_number: int = Field(..., ge=1, description="1-based page number where evidence was located")
    chunk_id: str = Field(..., description="Unique chunk UUID")
    chunk_index: int = Field(..., ge=0, description="Sequential chunk index in document")
    part_number: Optional[str] = Field(default=None, description="Engineering part or assembly number")
    revision: Optional[str] = Field(default=None, description="Document revision identifier")
    section: Optional[str] = Field(default=None, description="Section or subsection title if available")
    snippet: str = Field(..., description="Exemplary excerpt supporting the claim")


class RAGResponse(BaseModel):
    """Grounded RAG synthesis response containing answer, citations, and provenance."""
    query: str = Field(..., description="User query submitted")
    answer: str = Field(..., description="Grounded technical answer synthesized strictly from evidence")
    citations: List[CitationItem] = Field(
        default_factory=list,
        description="List of supporting citations referenced in the answer"
    )
    retrieved_chunks_count: int = Field(
        default=0,
        ge=0,
        description="Total chunks retrieved during search before filtering"
    )
    retrieval_mode: str = Field(..., description="Retrieval mode used (keyword, vector, hybrid)")
    sufficient_evidence: bool = Field(
        default=True,
        description="Indicates whether retrieved context contained sufficient evidence"
    )
    provider: str = Field(..., description="LLM provider used (e.g. local_mock, azure_openai)")
    model: str = Field(..., description="Model identifier used for generation")
    timing_ms: Optional[float] = Field(
        default=None,
        description="Total end-to-end RAG latency in milliseconds"
    )
