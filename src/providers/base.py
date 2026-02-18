from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract base class for LLM providers.

    Each provider implementation knows how to send chat completion requests
    to a specific API (OpenRouter, Anthropic, OpenAI, etc.).  Providers
    receive a plain model string — the provider prefix has already been
    stripped by the time a :class:`ModelRef` is resolved.
    """

    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a chat completion request.

        Parameters
        ----------
        model:
            Model identifier as understood by this provider
            (e.g. ``"google/gemini-flash-1.5"`` for OpenRouter).
        messages:
            Chat messages in OpenAI-compatible format.
        **kwargs:
            Additional provider-specific parameters.

        Returns
        -------
        dict:
            Raw response from the provider API.
        """
        ...
