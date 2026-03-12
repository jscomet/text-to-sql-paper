"""LLM service clients for OpenAI and DashScope APIs."""
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional

import httpx
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """Initialize the LLM client.

        Args:
            api_key: The API key for authentication.
            base_url: Optional base URL for the API.
        """
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt.
            model_config: Optional model configuration (temperature, max_tokens, etc.).

        Returns:
            The generated text response.
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text from a prompt with streaming.

        Args:
            prompt: The input prompt.
            model_config: Optional model configuration.

        Yields:
            Chunks of generated text.
        """
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: str = "gpt-3.5-turbo",
    ):
        """Initialize the OpenAI client.

        Args:
            api_key: The OpenAI API key.
            base_url: Optional custom base URL (for proxy or compatible APIs).
            default_model: Default model to use.
        """
        super().__init__(api_key, base_url)
        self.default_model = default_model

        # Initialize OpenAI client
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = AsyncOpenAI(**client_kwargs)

    @retry(
        retry=retry_if_exception_type((
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError,
        )),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate text using OpenAI API.

        Args:
            prompt: The input prompt.
            model_config: Optional configuration including:
                - model: Model name (default: gpt-3.5-turbo)
                - temperature: Sampling temperature (default: 0.7)
                - max_tokens: Maximum tokens (default: 2000)
                - top_p: Nucleus sampling parameter
                - frequency_penalty: Frequency penalty
                - presence_penalty: Presence penalty

        Returns:
            The generated text response.

        Raises:
            Exception: If the API call fails after retries.
        """
        config = model_config or {}
        model = config.get("model", self.default_model)
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)

        try:
            logger.debug(f"Calling OpenAI API with model: {model}")

            messages = [{"role": "user", "content": prompt}]

            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=config.get("top_p"),
                frequency_penalty=config.get("frequency_penalty"),
                presence_penalty=config.get("presence_penalty"),
            )

            result = response.choices[0].message.content
            logger.debug(f"OpenAI API response received, tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    @retry(
        retry=retry_if_exception_type((
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError,
        )),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_stream(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text using OpenAI API with streaming.

        Args:
            prompt: The input prompt.
            model_config: Optional model configuration.

        Yields:
            Chunks of generated text.
        """
        config = model_config or {}
        model = config.get("model", self.default_model)
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)

        try:
            logger.debug(f"Calling OpenAI API with streaming, model: {model}")

            messages = [{"role": "user", "content": prompt}]

            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=config.get("top_p"),
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI API streaming error: {str(e)}")
            raise


class DashScopeClient(BaseLLMClient):
    """Alibaba DashScope API client (OpenAI-compatible mode)."""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DEFAULT_MODEL = "qwen2.5-coder-32b-instruct"

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
    ):
        """Initialize the DashScope client.

        Args:
            api_key: The DashScope API key.
            base_url: Optional custom base URL.
            default_model: Default model to use.
        """
        super().__init__(api_key, base_url or self.DEFAULT_BASE_URL)
        self.default_model = default_model

        # DashScope uses OpenAI-compatible API
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.base_url,
        )

    @retry(
        retry=retry_if_exception_type((
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError,
        )),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate text using DashScope API.

        Args:
            prompt: The input prompt.
            model_config: Optional configuration including:
                - model: Model name (default: qwen2.5-coder-32b-instruct)
                - temperature: Sampling temperature (default: 0.7)
                - max_tokens: Maximum tokens (default: 2000)
                - top_p: Nucleus sampling parameter
                - repetition_penalty: Repetition penalty

        Returns:
            The generated text response.

        Raises:
            Exception: If the API call fails after retries.
        """
        config = model_config or {}
        model = config.get("model", self.default_model)
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)

        try:
            logger.debug(f"Calling DashScope API with model: {model}")

            messages = [{"role": "user", "content": prompt}]

            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=config.get("top_p"),
                extra_body={
                    "repetition_penalty": config.get("repetition_penalty"),
                } if config.get("repetition_penalty") else None,
            )

            result = response.choices[0].message.content
            logger.debug(f"DashScope API response received")
            return result

        except Exception as e:
            logger.error(f"DashScope API error: {str(e)}")
            raise

    @retry(
        retry=retry_if_exception_type((
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError,
        )),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_stream(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text using DashScope API with streaming.

        Args:
            prompt: The input prompt.
            model_config: Optional model configuration.

        Yields:
            Chunks of generated text.
        """
        config = model_config or {}
        model = config.get("model", self.default_model)
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)

        try:
            logger.debug(f"Calling DashScope API with streaming, model: {model}")

            messages = [{"role": "user", "content": prompt}]

            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=config.get("top_p"),
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"DashScope API streaming error: {str(e)}")
            raise


def get_llm_client(
    provider: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMClient:
    """Factory function to get the appropriate LLM client.

    Args:
        provider: The LLM provider ('openai' or 'dashscope').
        api_key: Optional API key. If not provided, uses settings.
        base_url: Optional base URL override.
        model: Optional default model override.

    Returns:
        An instance of the appropriate LLM client.

    Raises:
        ValueError: If the provider is not supported or API key is missing.
    """
    provider = provider.lower()

    if provider == "openai":
        key = api_key or settings.openai_api_key
        if not key:
            raise ValueError("OpenAI API key not provided")
        return OpenAIClient(
            api_key=key,
            base_url=base_url or settings.openai_base_url,
            default_model=model or settings.openai_model,
        )

    elif provider == "dashscope":
        key = api_key or settings.dashscope_api_key
        if not key:
            raise ValueError("DashScope API key not provided")
        return DashScopeClient(
            api_key=key,
            base_url=base_url or settings.dashscope_base_url,
            default_model=model or settings.dashscope_model,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
