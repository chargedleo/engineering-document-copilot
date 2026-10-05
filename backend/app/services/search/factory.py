import logging
from typing import Optional
from app.core.config import settings
from app.services.search.base import BaseSearchIndex
from app.services.search.local_index import LocalSearchIndex
from app.services.search.azure_search import AzureSearchIndex

logger = logging.getLogger("engineering_copilot.search")

_cached_search_index: Optional[BaseSearchIndex] = None


def get_search_index() -> BaseSearchIndex:
    """
    Factory resolving the appropriate search index.
    - If SEARCH_PROVIDER is 'local': returns in-process LocalSearchIndex.
    - If SEARCH_PROVIDER is 'azure' or 'auto': returns AzureSearchIndex if configured,
      otherwise falls back gracefully to LocalSearchIndex.
    """
    global _cached_search_index
    if _cached_search_index is not None:
        return _cached_search_index

    provider_pref = (settings.SEARCH_PROVIDER or "auto").lower()

    if provider_pref == "azure":
        logger.info("Initializing AzureSearchIndex per configuration.")
        _cached_search_index = AzureSearchIndex()
        return _cached_search_index

    if provider_pref == "local":
        logger.info("Initializing LocalSearchIndex per configuration.")
        _cached_search_index = LocalSearchIndex()
        return _cached_search_index

    # "auto" resolution
    if settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_API_KEY:
        logger.info("Azure Search credentials detected; using AzureSearchIndex.")
        _cached_search_index = AzureSearchIndex()
    else:
        logger.info("Azure Search credentials not configured; using in-process LocalSearchIndex.")
        _cached_search_index = LocalSearchIndex()

    return _cached_search_index


def reset_search_index() -> None:
    """Helper for testing to reset cached index instance."""
    global _cached_search_index
    if _cached_search_index is not None and isinstance(_cached_search_index, LocalSearchIndex):
        _cached_search_index.clear()
    _cached_search_index = None
