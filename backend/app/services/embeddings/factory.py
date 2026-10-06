import logging
from app.core.config import settings
from app.services.embeddings.base import BaseEmbeddingProvider
from app.services.embeddings.local_mock import LocalMockEmbeddingProvider
from app.services.embeddings.azure_openai import AzureOpenAIEmbeddingProvider

logger = logging.getLogger("engineering_copilot.embeddings")

_cached_provider: BaseEmbeddingProvider = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    """
    Factory resolving the appropriate embedding provider.
    - If EMBEDDING_PROVIDER is 'local': returns deterministic LocalMockEmbeddingProvider.
    - If EMBEDDING_PROVIDER is 'azure' or 'auto': returns AzureOpenAIEmbeddingProvider if
      configured, else gracefully falls back to LocalMockEmbeddingProvider.
    """
    global _cached_provider
    if _cached_provider is not None:
        return _cached_provider

    provider_pref = (settings.EMBEDDING_PROVIDER or "auto").lower()

    if provider_pref == "azure":
        logger.info("Initializing AzureOpenAIEmbeddingProvider per configuration.")
        _cached_provider = AzureOpenAIEmbeddingProvider()
        return _cached_provider

    if provider_pref == "local":
        logger.info("Initializing LocalMockEmbeddingProvider per configuration.")
        _cached_provider = LocalMockEmbeddingProvider()
        return _cached_provider

    # "auto" resolution
    if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
        logger.info("Azure OpenAI credentials detected; using AzureOpenAIEmbeddingProvider.")
        _cached_provider = AzureOpenAIEmbeddingProvider()
    else:
        logger.info("Azure OpenAI credentials not configured; using deterministic LocalMockEmbeddingProvider.")
        _cached_provider = LocalMockEmbeddingProvider()

    return _cached_provider


def reset_embedding_provider() -> None:
    """Helper for testing to reset cached provider instance."""
    global _cached_provider
    _cached_provider = None
