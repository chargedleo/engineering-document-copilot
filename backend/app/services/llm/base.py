from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ChatMessage:
    """Message exchange payload for LLM completion requests."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Output from LLM chat generation."""
    content: str
    model: str
    provider: str
    finish_reason: Optional[str] = "stop"
    usage: Dict[str, int] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract interface for LLM text and chat generation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. 'local_mock', 'azure_openai')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model deployment name."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check whether provider has valid credentials / configuration."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate response from chat messages."""
        pass
