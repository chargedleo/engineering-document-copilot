from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding generation."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate dense embedding vectors for a batch of texts."""
        pass

    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a single search query."""
        results = await self.embed_texts([query])
        return results[0] if results else [0.0] * self.dimension
