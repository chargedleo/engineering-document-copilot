import logging
from typing import List, Optional
import httpx

from app.core.config import settings
from app.services.llm.base import BaseLLMProvider, ChatMessage, LLMResponse

logger = logging.getLogger("engineering_copilot.llm.azure")


class AzureOpenAIChatProvider(BaseLLMProvider):
    """
    Azure OpenAI Chat Completions provider using official REST endpoints.
    Requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        self.endpoint = (endpoint or settings.AZURE_OPENAI_ENDPOINT or "").rstrip("/")
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY or ""
        self.deployment = (
            deployment
            or deployment_name
            or settings.AZURE_OPENAI_CHAT_DEPLOYMENT
            or settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
            or "gpt-4o"
        )
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION or "2024-02-15-preview"

    @property
    def name(self) -> str:
        return "azure_openai"

    @property
    def model_name(self) -> str:
        return self.deployment

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    async def generate(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        if not self.is_configured():
            raise ValueError(
                "Azure OpenAI Chat is not configured. Set AZURE_OPENAI_ENDPOINT and "
                "AZURE_OPENAI_API_KEY in .env."
            )

        url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", "stop")
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=self.deployment,
                provider=self.name,
                finish_reason=finish_reason,
                usage=usage,
            )
