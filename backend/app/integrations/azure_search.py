"""
Azure AI Search Client Integration Scaffold
Provides connection utilities for hybrid search (vector + keyword) across documents and CAD metadata.
"""

from typing import Optional
from app.core.config import settings
from app.core.logging import logger


class AzureSearchClient:
    """Manages Azure AI Search index clients for hybrid retrieval."""

    def __init__(self):
        self.endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.api_key = settings.AZURE_SEARCH_API_KEY
        self.documents_index = settings.AZURE_SEARCH_DOCUMENTS_INDEX_NAME
        self.cad_index = settings.AZURE_SEARCH_CAD_INDEX_NAME

    def is_configured(self) -> bool:
        """Check if Azure AI Search service is configured."""
        return bool(self.endpoint and self.api_key)

    async def get_search_client(self, index_name: Optional[str] = None):
        """
        Returns initialized Azure AI Search client.
        (Will import azure.search.documents in AI implementation phase)
        """
        if not self.is_configured():
            logger.warning("Azure AI Search is not configured in environment variables.")
            return None
        return None


azure_search_client = AzureSearchClient()
