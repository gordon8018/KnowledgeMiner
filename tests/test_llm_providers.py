"""Tests for LLM provider integration."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from src.integrations.llm_providers import (
    AnthropicProvider,
    OpenAIProvider,
    RateLimiter,
    RateLimitError,
    retry_with_exponential_backoff,
    _is_retryable_error
)


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_rate_limiter_acquire_within_limit(self):
        """Test acquiring tokens within rate limit."""
        limiter = RateLimiter(rate=10, per=60.0)

        # Should allow acquisition
        assert limiter.acquire(1) is True
        assert limiter.acquire(5) is True

    def test_rate_limiter_exceed_limit(self):
        """Test that rate limit is enforced."""
        limiter = RateLimiter(rate=5, per=60.0)

        # Use up all tokens
        assert limiter.acquire(5) is True

        # Next request should exceed limit
        with pytest.raises(RateLimitError) as exc_info:
            limiter.acquire(1)

        assert "Rate limit exceeded" in str(exc_info.value)

    def test_rate_limiter_refill_over_time(self):
        """Test that tokens are refilled over time."""
        # Use a short period for testing
        limiter = RateLimiter(rate=2, per=0.1)  # 2 requests per 0.1 seconds

        # Use up tokens
        assert limiter.acquire(2) is True

        # Should exceed limit immediately
        with pytest.raises(RateLimitError):
            limiter.acquire(1)

        # Wait for refill
        time.sleep(0.15)

        # Should have tokens again
        assert limiter.acquire(1) is True

    def test_rate_limiter_multiple_tokens(self):
        """Test acquiring multiple tokens at once."""
        limiter = RateLimiter(rate=10, per=60.0)

        # Acquire multiple tokens
        assert limiter.acquire(5) is True
        assert limiter.acquire(3) is True

        # Only 2 tokens left
        assert limiter.acquire(2) is True

        # Should exceed limit
        with pytest.raises(RateLimitError):
            limiter.acquire(1)


class TestRetryLogic:
    """Test retry logic and error classification."""

    def test_is_retryable_rate_limit_error(self):
        """Test that rate limit errors are retryable."""
        # Create mock exception with status_code
        mock_error = Mock()
        mock_error.status_code = 429

        assert _is_retryable_error(mock_error) is True

    def test_is_retryable_authentication_error(self):
        """Test that authentication errors are not retryable."""
        # Create mock exception with status_code
        mock_error = Mock()
        mock_error.status_code = 401

        assert _is_retryable_error(mock_error) is False

    def test_is_retryable_permission_error(self):
        """Test that permission errors are not retryable."""
        # Create mock exception with status_code
        mock_error = Mock()
        mock_error.status_code = 403

        assert _is_retryable_error(mock_error) is False

    def test_is_retryable_client_error(self):
        """Test that client errors (4xx) are not retryable."""
        # Create mock exception with status_code
        mock_error = Mock()
        mock_error.status_code = 400

        assert _is_retryable_error(mock_error) is False

    def test_is_retryable_rate_limit_error_instance(self):
        """Test that RateLimitError is retryable."""
        error = RateLimitError("Rate limit exceeded")

        assert _is_retryable_error(error) is True

    def test_is_retryable_timeout_error(self):
        """Test that timeout errors are retryable."""
        assert _is_retryable_error(TimeoutError()) is True
        assert _is_retryable_error(ConnectionError()) is True

    def test_is_retryable_string_based_detection(self):
        """Test retryable error detection from error strings."""
        # Create mock exceptions with specific strings
        error1 = Exception("rate limit exceeded")
        error2 = Exception("too many requests")
        error3 = Exception("connection timeout")

        assert _is_retryable_error(error1) is True
        assert _is_retryable_error(error2) is True
        assert _is_retryable_error(error3) is True

    def test_is_not_retryable_generic_error(self):
        """Test that generic errors are not retryable."""
        error = ValueError("Some random error")

        assert _is_retryable_error(error) is False

    def test_retry_decorator_success_on_first_try(self):
        """Test that successful function calls return immediately."""
        @retry_with_exponential_backoff(max_retries=3)
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_retry_decorator_retries_on_retryable_error(self):
        """Test that retryable errors trigger retries."""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError("Rate limit exceeded")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2

    def test_retry_decorator_fails_on_non_retryable_error(self):
        """Test that non-retryable errors fail immediately."""
        @retry_with_exponential_backoff(max_retries=3)
        def test_func():
            raise ValueError("Non-retryable error")

        with pytest.raises(ValueError) as exc_info:
            test_func()

        assert "Non-retryable error" in str(exc_info.value)

    def test_retry_decorator_exhausts_retries(self):
        """Test that retries are exhausted after max attempts."""
        @retry_with_exponential_backoff(max_retries=2, base_delay=0.01)
        def test_func():
            raise RateLimitError("Rate limit exceeded")

        with pytest.raises(RateLimitError):
            test_func()


class TestAnthropicProvider:
    """Test Anthropic provider functionality."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        provider = AnthropicProvider()

        assert provider.model == "claude-sonnet-4-6"
        assert provider.temperature == 0.3
        assert provider.max_tokens == 4096
        assert provider.timeout == 60
        assert provider.max_retries == 3
        assert provider.rate_limiter is None

    def test_init_with_rate_limit(self):
        """Test initialization with rate limiting."""
        provider = AnthropicProvider(rate_limit=10, rate_limit_period=60.0)

        assert provider.rate_limiter is not None
        assert provider.rate_limiter.rate == 10
        assert provider.rate_limiter.per == 60.0

    def test_ensure_client_without_package(self):
        """Test error when anthropic package is not available."""
        provider = AnthropicProvider()

        with patch('src.integrations.llm_providers.anthropic', None):
            with pytest.raises(ImportError) as exc_info:
                provider._ensure_client()

            assert "anthropic package is required" in str(exc_info.value)

    def test_generate_with_rate_limiting(self):
        """Test that rate limiting is applied during generation."""
        provider = AnthropicProvider(rate_limit=10, rate_limit_period=60.0)

        with patch('src.integrations.llm_providers.anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Generated text")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.Anthropic.return_value = mock_client

            # First call should succeed
            result = provider.generate("Test prompt")
            assert result == "Generated text"

            # Use up remaining tokens
            for _ in range(9):
                provider.generate("Test prompt")

            # Next call should exceed rate limit
            with pytest.raises(RateLimitError):
                provider.generate("Test prompt")

    def test_generate_structured_with_schema_validation(self):
        """Test structured generation with schema validation."""
        provider = AnthropicProvider()

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name", "value"]
        }

        valid_response = '{"name": "test", "value": 42}'

        with patch('src.integrations.llm_providers.anthropic'):
            with patch.object(provider, 'generate') as mock_generate:
                mock_generate.return_value = valid_response

                result = provider.generate_structured("Test prompt", schema)

                assert result == {"name": "test", "value": 42}

    def test_generate_structured_invalid_json(self):
        """Test that invalid JSON raises ValueError."""
        provider = AnthropicProvider()

        schema = {"type": "object"}

        with patch('src.integrations.llm_providers.anthropic'):
            with patch.object(provider, 'generate') as mock_generate:
                mock_generate.return_value = "Not valid JSON"

                with pytest.raises(ValueError) as exc_info:
                    provider.generate_structured("Test prompt", schema)

                assert "Failed to parse JSON" in str(exc_info.value)

    def test_generate_structured_missing_required_field(self):
        """Test that missing required fields are detected."""
        provider = AnthropicProvider()

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name", "value"]
        }

        invalid_response = '{"name": "test"}'  # Missing 'value'

        with patch('src.integrations.llm_providers.anthropic'):
            with patch.object(provider, 'generate') as mock_generate:
                mock_generate.return_value = invalid_response

                with pytest.raises(ValueError) as exc_info:
                    provider.generate_structured("Test prompt", schema)

                assert "Missing required property" in str(exc_info.value)

    def test_generate_structured_unexpected_properties(self):
        """Test that unexpected properties are detected when additionalProperties is False."""
        provider = AnthropicProvider()

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "additionalProperties": False
        }

        invalid_response = '{"name": "test", "extra": "field"}'  # Unexpected 'extra'

        with patch('src.integrations.llm_providers.anthropic'):
            with patch.object(provider, 'generate') as mock_generate:
                mock_generate.return_value = invalid_response

                with pytest.raises(ValueError) as exc_info:
                    provider.generate_structured("Test prompt", schema)

                assert "Unexpected properties" in str(exc_info.value)


class TestOpenAIProvider:
    """Test OpenAI provider functionality."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        provider = OpenAIProvider()

        assert provider.model == "gpt-4-turbo"
        assert provider.temperature == 0.3
        assert provider.max_tokens == 4096
        assert provider.timeout == 60
        assert provider.max_retries == 3
        assert provider.rate_limiter is None

    def test_init_with_rate_limit(self):
        """Test initialization with rate limiting."""
        provider = OpenAIProvider(rate_limit=10, rate_limit_period=60.0)

        assert provider.rate_limiter is not None
        assert provider.rate_limiter.rate == 10
        assert provider.rate_limiter.per == 60.0

    def test_ensure_client_without_package(self):
        """Test error when openai package is not available."""
        provider = OpenAIProvider()

        with patch('src.integrations.llm_providers.openai', None):
            with pytest.raises(ImportError) as exc_info:
                provider._ensure_client()

            assert "openai package is required" in str(exc_info.value)

    def test_generate_with_rate_limiting(self):
        """Test that rate limiting is applied during generation."""
        provider = OpenAIProvider(rate_limit=10, rate_limit_period=60.0)

        with patch('src.integrations.llm_providers.openai') as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Generated text"
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.OpenAI.return_value = mock_client

            # First call should succeed
            result = provider.generate("Test prompt")
            assert result == "Generated text"

            # Use up remaining tokens
            for _ in range(9):
                provider.generate("Test prompt")

            # Next call should exceed rate limit
            with pytest.raises(RateLimitError):
                provider.generate("Test prompt")

    def test_generate_structured_with_schema_validation(self):
        """Test structured generation with schema validation."""
        provider = OpenAIProvider()

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name", "value"]
        }

        valid_response = '{"name": "test", "value": 42}'

        with patch('src.integrations.llm_providers.openai'):
            with patch.object(provider, 'generate') as mock_generate:
                mock_generate.return_value = valid_response

                result = provider.generate_structured("Test prompt", schema)

                assert result == {"name": "test", "value": 42}

    def test_generate_structured_invalid_json(self):
        """Test that invalid JSON raises ValueError."""
        provider = OpenAIProvider()

        schema = {"type": "object"}

        with patch('src.integrations.llm_providers.openai'):
            with patch.object(provider, 'generate') as mock_generate:
                mock_generate.return_value = "Not valid JSON"

                with pytest.raises(ValueError) as exc_info:
                    provider.generate_structured("Test prompt", schema)

                assert "Failed to parse JSON" in str(exc_info.value)

    def test_generate_structured_missing_required_field(self):
        """Test that missing required fields are detected."""
        provider = OpenAIProvider()

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name", "value"]
        }

        invalid_response = '{"name": "test"}'  # Missing 'value'

        with patch('src.integrations.llm_providers.openai'):
            with patch.object(provider, 'generate') as mock_generate:
                mock_generate.return_value = invalid_response

                with pytest.raises(ValueError) as exc_info:
                    provider.generate_structured("Test prompt", schema)

                assert "Missing required property" in str(exc_info.value)


class TestErrorHandling:
    """Test error handling across providers."""

    def test_retry_on_rate_limit_error(self):
        """Test that rate limit errors are retried."""
        # Test retry logic at the decorator level
        call_count = 0

        # Create a proper exception
        class MockRateLimitError(Exception):
            def __init__(self):
                self.status_code = 429
                super().__init__("Rate limit exceeded")

        @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise MockRateLimitError()
            return "Success"

        result = test_func()

        assert result == "Success"
        assert call_count == 2

    def test_no_retry_on_auth_error(self):
        """Test that authentication errors are not retried."""
        provider = AnthropicProvider()

        with patch('src.integrations.llm_providers.anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_error = Mock()
            mock_error.status_code = 401
            mock_client.messages.create.side_effect = mock_error
            mock_anthropic.Anthropic.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                provider.generate("Test prompt")

            # Should only be called once (no retries)
            assert mock_client.messages.create.call_count == 1
