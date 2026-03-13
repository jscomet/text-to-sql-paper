"""LLM service clients for various LLM providers."""
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional

import httpx
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

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
    """OpenAI-compatible API client.

    Supports any provider that uses the OpenAI API format:
    - OpenAI
    - DeepSeek
    - DashScope (Alibaba)
    - vLLM
    - Any other OpenAI-compatible service
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: str = "gpt-3.5-turbo",
    ):
        """Initialize the OpenAI-compatible client.

        Args:
            api_key: The API key.
            base_url: Optional custom base URL.
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
        """Generate text using OpenAI-compatible API.

        Args:
            prompt: The input prompt.
            model_config: Optional configuration including:
                - model: Model name
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
            logger.debug(f"Calling OpenAI-compatible API with model: {model}")

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
            logger.debug(f"OpenAI-compatible API response received, tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
            return result

        except Exception as e:
            logger.error(f"OpenAI-compatible API error: {str(e)}")
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
        """Generate text using OpenAI-compatible API with streaming.

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
            logger.debug(f"Calling OpenAI-compatible API with streaming, model: {model}")

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
            logger.error(f"OpenAI-compatible API streaming error: {str(e)}")
            raise


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client.

    Uses the Anthropic Messages API format.
    """

    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_MODEL = "claude-3-sonnet-20240229"

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
    ):
        """Initialize the Anthropic client.

        Args:
            api_key: The Anthropic API key.
            base_url: Optional custom base URL.
            default_model: Default model to use.
        """
        super().__init__(api_key, base_url or self.DEFAULT_BASE_URL)
        self.default_model = default_model

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
        """Generate text using Anthropic API.

        Args:
            prompt: The input prompt.
            model_config: Optional configuration including:
                - model: Model name (default: claude-3-sonnet-20240229)
                - temperature: Sampling temperature (default: 0.7)
                - max_tokens: Maximum tokens (default: 2000)

        Returns:
            The generated text response.
        """
        config = model_config or {}
        model = config.get("model", self.default_model)
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)

        try:
            logger.debug(f"Calling Anthropic API with model: {model}")

            import httpx
            async with httpx.AsyncClient() as client:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }

                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                if config.get("top_p"):
                    payload["top_p"] = config["top_p"]

                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()

                result = data["content"][0]["text"]
                logger.debug(f"Anthropic API response received, usage: {data.get('usage', 'N/A')}")
                return result

        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
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
        """Generate text using Anthropic API with streaming.

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
            logger.debug(f"Calling Anthropic API with streaming, model: {model}")

            import httpx
            async with httpx.AsyncClient() as client:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }

                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                }

                if config.get("top_p"):
                    payload["top_p"] = config["top_p"]

                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=60.0,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                import json
                                data = json.loads(data_str)
                                if data.get("type") == "content_block_delta":
                                    delta = data.get("delta", {})
                                    if delta.get("text"):
                                        yield delta["text"]
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"Anthropic API streaming error: {str(e)}")
            raise


class VLLMClient(OpenAIClient):
    """vLLM API client.

    vLLM uses OpenAI-compatible API format, so we extend OpenAIClient
    with vLLM-specific defaults and behaviors.
    """

    DEFAULT_MODEL = "meta-llama/Llama-2-7b-chat-hf"

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
    ):
        """Initialize the vLLM client.

        Args:
            api_key: The API key (can be a placeholder for local vLLM).
            base_url: The vLLM server base URL (required).
            default_model: Default model to use.
        """
        # vLLM typically runs locally without auth, but accepts any key format
        super().__init__(api_key, base_url, default_model)

    async def generate(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate text using vLLM OpenAI-compatible API."""
        logger.debug(f"Calling vLLM API with model: {self.default_model}")
        return await super().generate(prompt, model_config)

    async def generate_stream(
        self,
        prompt: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text using vLLM API with streaming."""
        logger.debug(f"Calling vLLM API with streaming, model: {self.default_model}")
        async for chunk in super().generate_stream(prompt, model_config):
            yield chunk


def get_llm_client(
    provider: str,
    api_key: str,
    format_type: str = "openai",
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMClient:
    """Factory function to get LLM client based on format_type.

    Args:
        provider: Provider name for display/logging (e.g., 'deepseek', 'openai').
        api_key: The API key for authentication.
        format_type: The API format type that determines the client class:
            - 'openai': OpenAI-compatible format (OpenAI, DeepSeek, DashScope, etc.)
            - 'anthropic': Anthropic Claude format
            - 'vllm': vLLM OpenAI-compatible format
        base_url: Optional custom base URL.
        model: Optional default model name.

    Returns:
        An instance of the appropriate LLM client.

    Raises:
        ValueError: If the format_type is not supported or API key is missing.
    """
    if not api_key:
        raise ValueError(f"API key not provided for provider: {provider}")

    format_type = format_type.lower()

    if format_type == "openai":
        return OpenAIClient(
            api_key=api_key,
            base_url=base_url,
            default_model=model or "gpt-3.5-turbo",
        )
    elif format_type == "anthropic":
        return AnthropicClient(
            api_key=api_key,
            base_url=base_url,
            default_model=model or "claude-3-sonnet-20240229",
        )
    elif format_type == "vllm":
        return VLLMClient(
            api_key=api_key,
            base_url=base_url,
            default_model=model or "meta-llama/Llama-2-7b-chat-hf",
        )
    else:
        raise ValueError(
            f"Unsupported format_type: {format_type}. "
            f"Must be one of: openai, anthropic, vllm"
        )
