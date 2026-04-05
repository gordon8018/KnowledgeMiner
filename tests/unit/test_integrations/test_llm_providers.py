"""Unit tests for LLM provider integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.integrations.llm_providers import (
    LLMProvider,
    AnthropicProvider,
    OpenAIProvider,
    get_llm_provider,
    retry_with_exponential_backoff
)


class TestRetryDecorator:
    """Tests for retry decorator with exponential backoff."""

    def test_retry_success_on_first_attempt(self):
        """Test that successful calls work without retries."""
        @retry_with_exponential_backoff(max_retries=3)
        def successful_call():
            return "success"

        result = successful_call()
        assert result == "success"

    def test_retry_on_transient_error(self):
        """Test that transient errors trigger retries."""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3)
        def flaky_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Transient error")
            return "success"

        result = flaky_call()
        assert result == "success"
        assert call_count == 2

    def test_retry_exhausted(self):
        """Test that retries are exhausted after max attempts."""
        @retry_with_exponential_backoff(max_retries=2, base_delay=0.01)
        def failing_call():
            raise Exception("Persistent error")

        with pytest.raises(Exception, match="Persistent error"):
            failing_call()

    def test_rate_limit_error_handling(self):
        """Test that rate limit errors (429) are handled."""
        @retry_with_exponential_backoff(max_retries=2, base_delay=0.01)
        def rate_limited_call():
            # Simulate rate limit error
            error = Exception("Rate limit error")
            error.status_code = 429
            raise error

        # Should retry on rate limit errors
        with pytest.raises(Exception):
            rate_limited_call()


class TestLLMProviderBase:
    """Tests for LLMProvider abstract base class."""

    def test_cannot_instantiate_base_class(self):
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider()


class TestAnthropicProvider:
    """Tests for Anthropic provider implementation."""

    @patch('src.integrations.llm_providers.anthropic', create=True)
    def test_initialization_with_default_config(self, mock_anthropic):
        """Test AnthropicProvider initialization with defaults."""
        provider = AnthropicProvider()

        assert provider.model == "claude-sonnet-4-6"
        assert provider.temperature == 0.3
        assert provider.max_tokens == 4096
        assert provider.timeout == 60
        assert provider.max_retries == 3

    @patch('src.integrations.llm_providers.anthropic', create=True)
    def test_initialization_with_custom_config(self, mock_anthropic):
        """Test AnthropicProvider initialization with custom values."""
        provider = AnthropicProvider(
            model="claude-3-opus",
            temperature=0.7,
            max_tokens=2048,
            timeout=30,
            max_retries=5
        )

        assert provider.model == "claude-3-opus"
        assert provider.temperature == 0.7
        assert provider.max_tokens == 2048
        assert provider.timeout == 30
        assert provider.max_retries == 5

    @patch('src.integrations.llm_providers.anthropic', create=True)
    def test_initialization_with_api_key(self, mock_anthropic):
        """Test AnthropicProvider initialization with API key."""
        provider = AnthropicProvider(api_key="test-key-123")

        assert provider.api_key == "test-key-123"

    @patch('src.integrations.llm_providers.anthropic')
    def test_generate_success(self, mock_anthropic):
        """Test successful text generation."""
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Generated response")]
        mock_client.messages.create = MagicMock(return_value=mock_message)
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        provider = AnthropicProvider(api_key="test-key")
        result = provider.generate("Test prompt")

        assert result == "Generated response"
        mock_client.messages.create.assert_called_once()

    @patch('src.integrations.llm_providers.anthropic')
    def test_generate_with_custom_parameters(self, mock_anthropic):
        """Test generation with custom parameters."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Custom response")]
        mock_client.messages.create = MagicMock(return_value=mock_message)
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        provider = AnthropicProvider(api_key="test-key")
        result = provider.generate(
            "Test prompt",
            max_tokens=1000,
            temperature=0.8
        )

        assert result == "Custom response"
        # Verify the call included custom parameters
        call_args = mock_client.messages.create.call_args
        assert call_args[1]['max_tokens'] == 1000
        assert call_args[1]['temperature'] == 0.8

    @patch('src.integrations.llm_providers.anthropic')
    def test_generate_structured_success(self, mock_anthropic):
        """Test successful structured generation."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='{"name": "test", "value": 123}')]
        mock_client.messages.create = MagicMock(return_value=mock_message)
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        provider = AnthropicProvider(api_key="test-key")
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = provider.generate_structured("Generate data", schema)

        assert result == {"name": "test", "value": 123}

    @patch('src.integrations.llm_providers.anthropic')
    def test_generate_structured_invalid_json(self, mock_anthropic):
        """Test structured generation with invalid JSON response."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Not valid JSON")]
        mock_client.messages.create = MagicMock(return_value=mock_message)
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        provider = AnthropicProvider(api_key="test-key")
        schema = {"type": "object"}

        with pytest.raises(ValueError, match="Failed to parse JSON response"):
            provider.generate_structured("Generate data", schema)

    @patch('src.integrations.llm_providers.anthropic')
    def test_generate_api_error(self, mock_anthropic):
        """Test API error handling."""
        mock_client = MagicMock()
        mock_client.messages.create = MagicMock(
            side_effect=Exception("API error")
        )
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        provider = AnthropicProvider(api_key="test-key")

        with pytest.raises(Exception, match="API error"):
            provider.generate("Test prompt")

    @patch('src.integrations.llm_providers.anthropic')
    def test_generate_rate_limit_retry(self, mock_anthropic):
        """Test retry on rate limit errors."""
        mock_client = MagicMock()
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error = Exception("Rate limit")
                error.status_code = 429
                raise error
            mock_message = MagicMock()
            mock_message.content = [MagicMock(text="Success after retry")]
            return mock_message

        mock_client.messages.create = MagicMock(side_effect=side_effect)
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        provider = AnthropicProvider(api_key="test-key", max_retries=3)
        result = provider.generate("Test prompt")

        assert result == "Success after retry"
        assert call_count == 2

    @patch('src.integrations.llm_providers.anthropic', create=True)
    def test_missing_api_key(self, mock_anthropic):
        """Test behavior when API key is missing."""
        with patch.dict('os.environ', {}, clear=True):
            provider = AnthropicProvider()
            # Should have empty API key
            assert provider.api_key == ""


class TestOpenAIProvider:
    """Tests for OpenAI provider implementation."""

    @patch('src.integrations.llm_providers.openai', create=True)
    def test_initialization_with_default_config(self, mock_openai):
        """Test OpenAIProvider initialization with defaults."""
        provider = OpenAIProvider()

        assert provider.model == "gpt-4-turbo"
        assert provider.temperature == 0.3
        assert provider.max_tokens == 4096
        assert provider.timeout == 60
        assert provider.max_retries == 3

    @patch('src.integrations.llm_providers.openai', create=True)
    def test_initialization_with_custom_config(self, mock_openai):
        """Test OpenAIProvider initialization with custom values."""
        provider = OpenAIProvider(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=2048,
            timeout=30,
            max_retries=5
        )

        assert provider.model == "gpt-3.5-turbo"
        assert provider.temperature == 0.7
        assert provider.max_tokens == 2048
        assert provider.timeout == 30
        assert provider.max_retries == 5

    @patch('src.integrations.llm_providers.openai', create=True)
    def test_initialization_with_api_key(self, mock_openai):
        """Test OpenAIProvider initialization with API key."""
        provider = OpenAIProvider(api_key="test-key-456")

        assert provider.api_key == "test-key-456"

    @patch('src.integrations.llm_providers.openai')
    def test_generate_success(self, mock_openai):
        """Test successful text generation."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="OpenAI response"))]
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        provider = OpenAIProvider(api_key="test-key")
        result = provider.generate("Test prompt")

        assert result == "OpenAI response"
        mock_client.chat.completions.create.assert_called_once()

    @patch('src.integrations.llm_providers.openai')
    def test_generate_with_custom_parameters(self, mock_openai):
        """Test generation with custom parameters."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Custom response"))]
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        provider = OpenAIProvider(api_key="test-key")
        result = provider.generate(
            "Test prompt",
            max_tokens=1000,
            temperature=0.8
        )

        assert result == "Custom response"
        # Verify the call included custom parameters
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['max_tokens'] == 1000
        assert call_args[1]['temperature'] == 0.8

    @patch('src.integrations.llm_providers.openai')
    def test_generate_structured_success(self, mock_openai):
        """Test successful structured generation."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"result": "structured"}'))
        ]
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        provider = OpenAIProvider(api_key="test-key")
        schema = {"type": "object"}
        result = provider.generate_structured("Generate structured", schema)

        assert result == {"result": "structured"}

    @patch('src.integrations.llm_providers.openai')
    def test_generate_structured_invalid_json(self, mock_openai):
        """Test structured generation with invalid JSON response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Not valid JSON"))
        ]
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        provider = OpenAIProvider(api_key="test-key")
        schema = {"type": "object"}

        with pytest.raises(ValueError, match="Failed to parse JSON response"):
            provider.generate_structured("Generate data", schema)

    @patch('src.integrations.llm_providers.openai')
    def test_generate_api_error(self, mock_openai):
        """Test API error handling."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = MagicMock(
            side_effect=Exception("OpenAI API error")
        )
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        provider = OpenAIProvider(api_key="test-key")

        with pytest.raises(Exception, match="OpenAI API error"):
            provider.generate("Test prompt")

    @patch('src.integrations.llm_providers.openai')
    def test_generate_rate_limit_retry(self, mock_openai):
        """Test retry on rate limit errors."""
        mock_client = MagicMock()
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error = Exception("Rate limit")
                error.status_code = 429
                raise error
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="Success after retry"))
            ]
            return mock_response

        mock_client.chat.completions.create = MagicMock(side_effect=side_effect)
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        provider = OpenAIProvider(api_key="test-key", max_retries=3)
        result = provider.generate("Test prompt")

        assert result == "Success after retry"
        assert call_count == 2


class TestGetLLMProvider:
    """Tests for get_llm_provider factory function."""

    @patch('src.integrations.llm_providers.os.getenv')
    def test_get_anthropic_provider(self, mock_getenv):
        """Test getting Anthropic provider."""
        mock_getenv.return_value = "test-key"

        provider = get_llm_provider("anthropic")

        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == "test-key"

    @patch('src.integrations.llm_providers.os.getenv')
    def test_get_openai_provider(self, mock_getenv):
        """Test getting OpenAI provider."""
        mock_getenv.return_value = "test-key"

        provider = get_llm_provider("openai")

        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-key"

    def test_get_invalid_provider(self):
        """Test getting invalid provider raises error."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider("invalid_provider")

    @patch('src.integrations.llm_providers.os.getenv')
    def test_get_provider_from_config(self, mock_getenv):
        """Test getting provider from config."""
        mock_getenv.return_value = "config-key"

        provider = get_llm_provider(
            "anthropic",
            api_key_env="CUSTOM_API_KEY"
        )

        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == "config-key"
