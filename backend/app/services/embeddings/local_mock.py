import hashlib
import re
from typing import List
import numpy as np

from app.core.config import settings
from app.services.embeddings.base import BaseEmbeddingProvider


class LocalMockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic in-memory embedding generator for local development and testing.

    Uses random projection hashing to generate unit-normalized dense vectors:
    - Same input text always produces the exact identical vector.
    - Texts sharing semantic engineering terms produce higher cosine similarity.
    - Runs in pure Python/NumPy with zero network or cloud credentials.
    """

    def __init__(self, dimension: int = None, dimensions: int = None):
        self._dim = dimension or dimensions or settings.EMBEDDING_DIMENSIONS

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for text in texts:
            vec = self._compute_deterministic_vector(text)
            embeddings.append(vec.tolist())
        return embeddings

    def _compute_deterministic_vector(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            # Return stable normalized pseudo-zero vector
            vec = np.zeros(self._dim, dtype=np.float32)
            vec[0] = 1.0
            return vec

        # Tokenize words and n-grams
        tokens = re.findall(r"\b[A-Za-z0-9_\-\.\/+]+\b", text.lower())
        if not tokens:
            tokens = [text.strip().lower()]

        dense_vec = np.zeros(self._dim, dtype=np.float32)

        for token in tokens:
            # Deterministic hash of each token into 4 pseudo-random feature indices and signs
            token_bytes = token.encode("utf-8")
            h = hashlib.sha256(token_bytes).digest()

            # Extract 4 independent seeds from hash
            for i in range(4):
                idx_seed = int.from_bytes(h[i * 4 : (i + 1) * 4], byteorder="little")
                index = idx_seed % self._dim
                sign = 1.0 if (idx_seed % 2 == 0) else -1.0
                dense_vec[index] += sign

        # Compute L2 norm
        norm = np.linalg.norm(dense_vec)
        if norm > 1e-6:
            dense_vec /= norm
        else:
            dense_vec[0] = 1.0

        return dense_vec
