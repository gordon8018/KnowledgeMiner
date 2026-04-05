"""LLM provider integration for Anthropic Claude and OpenAI GPT."""

import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from collections import deque
from datetime import datetime, timedelta

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

try:
    from jsonschema import validate, ValidationError as JSONSchemaValidationError
except ImportError:
    validate = None
    JSONSchemaValidationError = None


class RateLimiter:
    """Token bucket rate limiter to prevent exceeding API limits.

    This implements a token bucket algorithm where tokens are added at a fixed rate,
    and requests consume tokens. If no tokens are available, the request is blocked.
    """

    def __init__(self, rate: float, per: float = 60.0):
        """Initialize rate limiter.

        Args:
            rate: Maximum number of requests allowed
            per: Time period in seconds (default: 60 seconds)
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()

    def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False if rate limit exceeded

        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current

        # Add tokens based on time passed
        self.allowance += time_passed * (self.rate / self.per)

        # Don't exceed maximum allowance
        if self.allowance > self.rate:
            self.allowance = self.rate

        # Check if we have enough tokens
        if self.allowance < tokens:
            # Not enough tokens - rate limit exceeded
            raise RateLimitError(
                f"Rate limit exceeded: {tokens} tokens requested, "
                f"but only {self.allowance:.2f} available. "
                f"Limit: {self.rate} requests per {self.per} seconds."
            )

        # Consume tokens
        self.allowance -= tokens
        return True


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


def _is_retryable_error(exception: Exception) -> bool:
    """Check if an exception is retryable (transient/rate limit errors).

    Args:
        exception: The exception to check

    Returns:
        True if the error is retryable, False otherwise
    """
    # Check for rate limit errors (HTTP 429)
    if hasattr(exception, 'status_code'):
        if exception.status_code == 429:
            return True
        # Don't retry authentication errors (401), permission errors (403),
        # or client errors (4xx except 429)
        if 400 <= exception.status_code < 500 and exception.status_code != 429:
            return False

    # Check for rate limit error type
    if isinstance(exception, RateLimitError):
        return True

    # Check for specific API error types that indicate rate limiting
    error_str = str(exception).lower()
    if 'rate limit' in error_str or 'too many requests' in error_str:
        return True

    # Check for transient network errors (timeout, connection errors)
    if isinstance(exception, (TimeoutError, ConnectionError)):
        return True

    # Check for timeout-specific errors
    if 'timeout' in error_str or 'connection' in error_str:
        return True

    # Default: don't retry on unknown errors
    return False


def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2,
    timeout: Optional[int] = None
) -> Callable:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        timeout: Timeout in seconds (for informational purposes)

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

                    # Check if this error should be retried
                    if not _is_retryable_error(e):
                        # Don't retry on non-retryable errors
                        raise

                    if retry_count > max_retries:
                        # Exhausted retries
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (retry_count - 1)),
                        max_delay
                    )

                    # Sleep before retry
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
        api_key_env: Optional[str] = None,
        rate_limit: Optional[float] = None,
        rate_limit_period: float = 60.0
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
            rate_limit: Maximum requests per period (None = no limit)
            rate_limit_period: Time period for rate limit in seconds
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

        # Initialize rate limiter if rate limit is specified
        self.rate_limiter = None
        if rate_limit is not None:
            self.rate_limiter = RateLimiter(rate=rate_limit, per=rate_limit_period)

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
        api_key_env: str = "ANTHROPIC_API_KEY",
        rate_limit: Optional[float] = None,
        rate_limit_period: float = 60.0
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
            rate_limit: Maximum requests per period (None = no limit)
            rate_limit_period: Time period for rate limit in seconds
        """
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            api_key=api_key,
            api_key_env=api_key_env,
            rate_limit=rate_limit,
            rate_limit_period=rate_limit_period
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

        Raises:
            ImportError: If anthropic package is not installed
            RateLimitError: If rate limit is exceeded
            Exception: If API call fails after retries
        """
        self._ensure_client()

        # Check rate limit before making request
        if self.rate_limiter is not None:
            self.rate_limiter.acquire()

        @retry_with_exponential_backoff(
            max_retries=self.max_retries,
            timeout=self.timeout
        )
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

        Raises:
            ImportError: If anthropic package is not installed
            ValueError: If response is not valid JSON or doesn't match schema
            RateLimitError: If rate limit is exceeded
            Exception: If API call fails after retries
        """
        self._ensure_client()

        # Add schema instruction to prompt
        schema_instruction = (
            f"\n\nPlease respond with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )
        full_prompt = prompt + schema_instruction

        response_text = self.generate(full_prompt)

        # Parse JSON response
        try:
            response_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e

        # Validate response against schema if jsonschema is available
        if validate is not None:
            try:
                validate(instance=response_data, schema=schema)
            except JSONSchemaValidationError as e:
                raise ValueError(f"Response doesn't match schema: {e.message}") from e
        elif JSONSchemaValidationError is None:
            # If jsonschema is not available, do basic validation
            self._validate_schema_basic(response_data, schema)

        return response_data

    def _validate_schema_basic(self, response_data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Basic schema validation when jsonschema is not available.

        Args:
            response_data: Response data to validate
            schema: JSON schema

        Raises:
            ValueError: If response doesn't match schema
        """
        if 'properties' in schema:
            # Check that all required properties are present
            required = schema.get('required', [])
            for prop in required:
                if prop not in response_data:
                    raise ValueError(f"Missing required property: {prop}")

            # Check that no extra properties are present if additionalProperties is False
            if schema.get('additionalProperties', True) is False:
                allowed_props = set(schema['properties'].keys())
                actual_props = set(response_data.keys())
                extra_props = actual_props - allowed_props
                if extra_props:
                    raise ValueError(f"Unexpected properties: {extra_props}")


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
        api_key_env: str = "OPENAI_API_KEY",
        rate_limit: Optional[float] = None,
        rate_limit_period: float = 60.0
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
            rate_limit: Maximum requests per period (None = no limit)
            rate_limit_period: Time period for rate limit in seconds
        """
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            api_key=api_key,
            api_key_env=api_key_env,
            rate_limit=rate_limit,
            rate_limit_period=rate_limit_period
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

        Raises:
            ImportError: If openai package is not installed
            RateLimitError: If rate limit is exceeded
            Exception: If API call fails after retries
        """
        self._ensure_client()

        # Check rate limit before making request
        if self.rate_limiter is not None:
            self.rate_limiter.acquire()

        @retry_with_exponential_backoff(
            max_retries=self.max_retries,
            timeout=self.timeout
        )
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

        Raises:
            ImportError: If openai package is not installed
            ValueError: If response is not valid JSON or doesn't match schema
            RateLimitError: If rate limit is exceeded
            Exception: If API call fails after retries
        """
        self._ensure_client()

        # Add schema instruction to prompt
        schema_instruction = (
            f"\n\nPlease respond with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )
        full_prompt = prompt + schema_instruction

        response_text = self.generate(full_prompt)

        # Parse JSON response
        try:
            response_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e

        # Validate response against schema if jsonschema is available
        if validate is not None:
            try:
                validate(instance=response_data, schema=schema)
            except JSONSchemaValidationError as e:
                raise ValueError(f"Response doesn't match schema: {e.message}") from e
        elif JSONSchemaValidationError is None:
            # If jsonschema is not available, do basic validation
            self._validate_schema_basic(response_data, schema)

        return response_data

    def _validate_schema_basic(self, response_data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Basic schema validation when jsonschema is not available.

        Args:
            response_data: Response data to validate
            schema: JSON schema

        Raises:
            ValueError: If response doesn't match schema
        """
        if 'properties' in schema:
            # Check that all required properties are present
            required = schema.get('required', [])
            for prop in required:
                if prop not in response_data:
                    raise ValueError(f"Missing required property: {prop}")

            # Check that no extra properties are present if additionalProperties is False
            if schema.get('additionalProperties', True) is False:
                allowed_props = set(schema['properties'].keys())
                actual_props = set(response_data.keys())
                extra_props = actual_props - allowed_props
                if extra_props:
                    raise ValueError(f"Unexpected properties: {extra_props}")


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
