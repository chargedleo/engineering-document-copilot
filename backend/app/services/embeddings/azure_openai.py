import logging
from typing import List, Optional
import httpx

from app.core.config import settings
from app.services.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger("engineering_copilot.embeddings.azure")


class AzureOpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    Azure OpenAI embeddings provider using official REST endpoints.
    Requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        self.endpoint = (endpoint or settings.AZURE_OPENAI_ENDPOINT or "").rstrip("/")
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY or ""
        self.deployment = deployment or settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME or "text-embedding-3-large"
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION or "2024-02-15-preview"
        self._dimension = dimension or settings.EMBEDDING_DIMENSIONS

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env."
            )

        url = f"{self.endpoint}/openai/deployments/{self.deployment}/embeddings?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            # Order items by index
            sorted_items = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
            return [item["embedding"] for item in sorted_items]
