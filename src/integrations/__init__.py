"""External integrations for Knowledge Compiler."""

from .llm_providers import (
    LLMProvider,
    AnthropicProvider,
    OpenAIProvider,
    get_llm_provider
)

# Import providers when they become available in future tasks
# This file will be updated as modules are implemented

__all__ = [
    "LLMProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    "get_llm_provider",
    "EmbeddingGenerator",  # Will be available in Task 7
    "StorageBackend",      # Will be available in future phases
]
