"""LLM provider integration for Anthropic Claude and OpenAI GPT."""

import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from functools import wraps

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None


def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2
) -> Callable:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retry_count = 0
            last_exception = None

            while retry_count <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    retry_count += 1

                    # Check if this is a rate limit error or should be retried
                    should_retry = (
                        hasattr(e, 'status_code') and e.status_code == 429
                    ) or retry_count <= max_retries

                    if not should_retry:
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (retry_count - 1)),
                        max_delay
                    )

                    # Sleep before retry
                    if retry_count <= max_retries:
                        time.sleep(delay)

            # If we've exhausted retries, raise the last exception
            raise last_exception

        return wrapper
    return decorator


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 60,
        max_retries: int = 3,
        api_key: Optional[str] = None,
        api_key_env: Optional[str] = None
    ):
        """Initialize LLM provider.

        Args:
            model: Model name/identifier
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            api_key: API key (overrides environment variable)
            api_key_env: Environment variable name for API key
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_key_env = api_key_env or ""

        # API key: explicit parameter takes precedence over environment
        if api_key is not None:
            self.api_key = api_key
        elif api_key_env:
            self.api_key = os.getenv(api_key_env, "")
        else:
            self.api_key = ""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: Input prompt
            max_tokens: Override max_tokens for this call
            temperature: Override temperature for this call

        Returns:
            Generated text

        Raises:
            Exception: If API call fails after retries
        """
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured data from a prompt.

        Args:
            prompt: Input prompt
            schema: JSON schema for expected output format

        Returns:
            Generated data as dictionary

        Raises:
            ValueError: If response is not valid JSON
            Exception: If API call fails after retries
        """
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 60,
        max_retries: int = 3,
        api_key: Optional[str] = None,
        api_key_env: str = "ANTHROPIC_API_KEY"
    ):
        """Initialize Anthropic provider.

        Args:
            model: Claude model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            api_key: Anthropic API key
            api_key_env: Environment variable name for API key
        """
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            api_key=api_key,
            api_key_env=api_key_env
        )

    def _ensure_client(self):
        """Ensure anthropic package is available."""
        if anthropic is None:
            raise ImportError("anthropic package is required. Install with: pip install anthropic>=0.25.0")

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate text using Claude API.

        Args:
            prompt: Input prompt
            max_tokens: Override max_tokens for this call
            temperature: Override temperature for this call

        Returns:
            Generated text
        """
        self._ensure_client()

        @retry_with_exponential_backoff(max_retries=self.max_retries)
        def _make_request():
            client = anthropic.Anthropic(api_key=self.api_key)

            # Use override values if provided, otherwise use instance defaults
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            temp = temperature if temperature is not None else self.temperature

            response = client.messages.create(
                model=self.model,
                max_tokens=tokens,
                temperature=temp,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=self.timeout
            )

            # Extract text from response
            return response.content[0].text

        return _make_request()

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured data using Claude API.

        Args:
            prompt: Input prompt
            schema: JSON schema for expected output format

        Returns:
            Generated data as dictionary
        """
        # Add schema instruction to prompt
        schema_instruction = (
            f"\n\nPlease respond with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )
        full_prompt = prompt + schema_instruction

        response_text = self.generate(full_prompt)

        # Parse JSON response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e


class OpenAIProvider(LLMProvider):
    """OpenAI GPT API provider."""

    def __init__(
        self,
        model: str = "gpt-4-turbo",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 60,
        max_retries: int = 3,
        api_key: Optional[str] = None,
        api_key_env: str = "OPENAI_API_KEY"
    ):
        """Initialize OpenAI provider.

        Args:
            model: GPT model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            api_key: OpenAI API key
            api_key_env: Environment variable name for API key
        """
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            api_key=api_key,
            api_key_env=api_key_env
        )

    def _ensure_client(self):
        """Ensure openai package is available."""
        if openai is None:
            raise ImportError("openai package is required. Install with: pip install openai>=1.10.0")

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate text using GPT API.

        Args:
            prompt: Input prompt
            max_tokens: Override max_tokens for this call
            temperature: Override temperature for this call

        Returns:
            Generated text
        """
        self._ensure_client()

        @retry_with_exponential_backoff(max_retries=self.max_retries)
        def _make_request():
            client = openai.OpenAI(api_key=self.api_key)

            # Use override values if provided, otherwise use instance defaults
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            temp = temperature if temperature is not None else self.temperature

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=tokens,
                temperature=temp,
                timeout=self.timeout
            )

            # Extract text from response
            return response.choices[0].message.content

        return _make_request()

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured data using GPT API.

        Args:
            prompt: Input prompt
            schema: JSON schema for expected output format

        Returns:
            Generated data as dictionary
        """
        # Add schema instruction to prompt
        schema_instruction = (
            f"\n\nPlease respond with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )
        full_prompt = prompt + schema_instruction

        response_text = self.generate(full_prompt)

        # Parse JSON response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e


def get_llm_provider(
    provider: str = "anthropic",
    api_key_env: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """Factory function to get LLM provider instance.

    Args:
        provider: Provider name ('anthropic' or 'openai')
        api_key_env: Environment variable name for API key
        **kwargs: Additional arguments to pass to provider

    Returns:
        LLM provider instance

    Raises:
        ValueError: If provider name is unknown
    """
    provider = provider.lower()

    if provider == "anthropic":
        api_key = api_key_env or "ANTHROPIC_API_KEY"
        return AnthropicProvider(api_key_env=api_key, **kwargs)
    elif provider == "openai":
        api_key = api_key_env or "OPENAI_API_KEY"
        return OpenAIProvider(api_key_env=api_key, **kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. "
                        f"Supported providers: 'anthropic', 'openai'")
