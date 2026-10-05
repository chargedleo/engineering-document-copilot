from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SearchHit:
    chunk_id: str
    document_id: str
    page_id: Optional[str]
    page_number: int
    chunk_index: int
    filename: str
    document_type: str
    part_number: Optional[str]
    revision: Optional[str]
    content: str
    score: float
    retrieval_mode: str  # "keyword", "vector", "hybrid"
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSearchIndex(ABC):
    """Abstract interface for hybrid search indexing and retrieval."""

    @abstractmethod
    async def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Add or update chunks in the search index."""
        pass

    @abstractmethod
    async def delete_document_chunks(self, document_id: str) -> None:
        """Remove all chunks associated with a document from the search index."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        mode: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchHit]:
        """Perform keyword, vector, or hybrid retrieval."""
        pass
