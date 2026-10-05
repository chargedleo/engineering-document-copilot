import logging
from typing import Optional

from app.core.config import settings
from app.services.llm.base import BaseLLMProvider
from app.services.llm.local_mock import LocalMockChatProvider
from app.services.llm.azure_openai import AzureOpenAIChatProvider

logger = logging.getLogger("engineering_copilot.llm")

_cached_llm_provider: Optional[BaseLLMProvider] = None


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory resolving the appropriate LLM provider.
    - If LLM_PROVIDER is 'local': returns deterministic LocalMockChatProvider.
    - If LLM_PROVIDER is 'azure': returns AzureOpenAIChatProvider.
    - If LLM_PROVIDER is 'auto': returns AzureOpenAIChatProvider if credentials exist,
      otherwise gracefully falls back to LocalMockChatProvider.
    """
    global _cached_llm_provider
    if _cached_llm_provider is not None:
        return _cached_llm_provider

    provider_pref = (settings.LLM_PROVIDER or "auto").lower()

    if provider_pref == "azure":
        logger.info("Initializing AzureOpenAIChatProvider per configuration.")
        _cached_llm_provider = AzureOpenAIChatProvider()
        return _cached_llm_provider

    if provider_pref == "local":
        logger.info("Initializing LocalMockChatProvider per configuration.")
        _cached_llm_provider = LocalMockChatProvider()
        return _cached_llm_provider

    # "auto" resolution
    if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
        logger.info("Azure OpenAI credentials detected; using AzureOpenAIChatProvider.")
        _cached_llm_provider = AzureOpenAIChatProvider()
    else:
        logger.info("Azure OpenAI credentials not configured; using offline LocalMockChatProvider.")
        _cached_llm_provider = LocalMockChatProvider()

    return _cached_llm_provider


def reset_llm_provider() -> None:
    """Helper to reset cached provider between tests."""
    global _cached_llm_provider
    _cached_llm_provider = None
