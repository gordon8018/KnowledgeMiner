"""Unit tests for embedding generation functionality."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.ml.embeddings import EmbeddingGenerator, EmbeddingCache


class TestEmbeddingCache:
    """Test cases for EmbeddingCache class."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = EmbeddingCache()
        assert cache._cache == {}
        assert cache.max_size == 1000

    def test_cache_initialization_with_custom_size(self):
        """Test cache initialization with custom max size."""
        cache = EmbeddingCache(max_size=100)
        assert cache.max_size == 100

    def test_cache_get_miss(self):
        """Test cache get when key doesn't exist."""
        cache = EmbeddingCache()
        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_put_and_get(self):
        """Test putting and getting from cache."""
        cache = EmbeddingCache()
        embedding = np.array([0.1, 0.2, 0.3])
        cache.put("test_key", embedding)
        result = cache.get("test_key")
        assert np.array_equal(result, embedding)

    def test_cache_put_with_max_size_limit(self):
        """Test cache respects max size limit."""
        cache = EmbeddingCache(max_size=3)

        # Add 3 items
        for i in range(3):
            cache.put(f"key_{i}", np.array([i]))

        # Add 4th item - should evict oldest
        cache.put("key_3", np.array([3]))

        # First key should be evicted
        assert cache.get("key_0") is None
        # Last 3 keys should exist
        assert cache.get("key_1") is not None
        assert cache.get("key_2") is not None
        assert cache.get("key_3") is not None

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = EmbeddingCache()
        cache.put("key1", np.array([1.0]))
        cache.put("key2", np.array([2.0]))
        assert len(cache._cache) == 2

        cache.clear()
        assert len(cache._cache) == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_size(self):
        """Test cache size reporting."""
        cache = EmbeddingCache()
        assert cache.size() == 0

        cache.put("key1", np.array([1.0]))
        cache.put("key2", np.array([2.0]))
        assert cache.size() == 2

    def test_cache_contains(self):
        """Test cache contains check."""
        cache = EmbeddingCache()
        cache.put("existing_key", np.array([1.0]))

        assert "existing_key" in cache
        assert "nonexistent_key" not in cache


class TestEmbeddingGenerator:
    """Test cases for EmbeddingGenerator class."""

    def test_initialization_with_defaults(self):
        """Test generator initialization with default values."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            generator = EmbeddingGenerator()
            assert generator.model_name == "text-embedding-3-small"
            assert generator.dimensions is None
            assert generator.batch_size == 100

    def test_initialization_with_custom_config(self):
        """Test generator initialization with custom configuration."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            generator = EmbeddingGenerator(
                model_name="text-embedding-3-large",
                dimensions=3072,
                batch_size=50
            )
            assert generator.model_name == "text-embedding-3-large"
            assert generator.dimensions == 3072
            assert generator.batch_size == 50

    def test_initialization_without_api_key(self):
        """Test generator initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable"):
                EmbeddingGenerator()

    def test_generate_embedding_success(self):
        """Test successful embedding generation for single text."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                # Mock API response
                mock_response = MagicMock()
                mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
                mock_client.embeddings.create.return_value = mock_response

                generator = EmbeddingGenerator()
                result = generator.generate_embedding("test text")

                assert isinstance(result, np.ndarray)
                assert result.shape == (1536,)
                # Check values are approximately equal (allowing for float32 conversion)
                assert np.allclose(result, [0.1] * 1536)

                # Verify API was called correctly
                mock_client.embeddings.create.assert_called_once()
                call_args = mock_client.embeddings.create.call_args
                assert call_args[1]['input'] == "test text"
                assert call_args[1]['model'] == "text-embedding-3-small"

    def test_generate_embedding_with_dimensions(self):
        """Test embedding generation with custom dimensions."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            mock_embedding = np.array([0.1] * 512)

            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                mock_response = MagicMock()
                mock_response.data = [MagicMock(embedding=[0.1] * 512)]
                mock_client.embeddings.create.return_value = mock_response

                generator = EmbeddingGenerator(dimensions=512)
                result = generator.generate_embedding("test text")

                assert result.shape == (512,)

                # Verify dimensions parameter was passed
                call_args = mock_client.embeddings.create.call_args
                assert call_args[1]['dimensions'] == 512

    def test_generate_embedding_cache_hit(self):
        """Test embedding generation with cache hit."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            mock_embedding = np.array([0.1] * 1536)

            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                mock_response = MagicMock()
                mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
                mock_client.embeddings.create.return_value = mock_response

                generator = EmbeddingGenerator()

                # First call - cache miss
                result1 = generator.generate_embedding("test text")
                assert mock_client.embeddings.create.call_count == 1

                # Second call - cache hit
                result2 = generator.generate_embedding("test text")
                assert mock_client.embeddings.create.call_count == 1  # No additional call

                # Results should be identical
                assert np.array_equal(result1, result2)

    def test_generate_embeddings_single_batch(self):
        """Test embedding generation for multiple texts in single batch."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            texts = ["text1", "text2", "text3"]

            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                mock_response = MagicMock()
                mock_response.data = [
                    MagicMock(embedding=[0.1] * 1536),
                    MagicMock(embedding=[0.2] * 1536),
                    MagicMock(embedding=[0.3] * 1536)
                ]
                mock_client.embeddings.create.return_value = mock_response

                generator = EmbeddingGenerator()
                results = generator.generate_embeddings(texts)

                assert len(results) == 3
                for i, result in enumerate(results):
                    assert isinstance(result, np.ndarray)
                    assert result.shape == (1536,)

                # Verify batch API call
                mock_client.embeddings.create.assert_called_once()
                call_args = mock_client.embeddings.create.call_args
                assert call_args[1]['input'] == texts

    def test_generate_embeddings_multiple_batches(self):
        """Test embedding generation with multiple batches."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            # Create 150 texts with batch size of 100
            texts = [f"text_{i}" for i in range(150)]

            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                def create_mock_embeddings(**kwargs):
                    input_texts = kwargs['input']
                    return MagicMock(data=[
                        MagicMock(embedding=[0.1] * 1536) for _ in input_texts
                    ])

                mock_client.embeddings.create.side_effect = create_mock_embeddings

                generator = EmbeddingGenerator(batch_size=100)
                results = generator.generate_embeddings(texts)

                assert len(results) == 150
                assert mock_client.embeddings.create.call_count == 2  # 2 batches

                # Verify batch sizes
                first_call_args = mock_client.embeddings.create.call_args_list[0]
                assert len(first_call_args[1]['input']) == 100

                second_call_args = mock_client.embeddings.create.call_args_list[1]
                assert len(second_call_args[1]['input']) == 50

    def test_generate_embeddings_empty_list(self):
        """Test embedding generation with empty list."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            generator = EmbeddingGenerator()
            results = generator.generate_embeddings([])
            assert results == []

    def test_generate_embeddings_with_cache(self):
        """Test that batch generation uses cache."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            texts = ["text1", "text2", "text1"]  # text1 repeated

            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                def create_mock_embeddings(**kwargs):
                    input_texts = kwargs['input']
                    return MagicMock(data=[
                        MagicMock(embedding=[0.1] * 1536) for _ in input_texts
                    ])

                mock_client.embeddings.create.side_effect = create_mock_embeddings

                generator = EmbeddingGenerator()
                results = generator.generate_embeddings(texts)

                # Should only make 1 API call (all unique texts in one batch)
                # The cache is checked within the batch, so duplicates are handled
                assert mock_client.embeddings.create.call_count == 1

                # Results should be consistent for repeated text
                assert np.array_equal(results[0], results[2])

    def test_generate_embedding_api_error(self):
        """Test embedding generation with API error."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                # Simulate API error
                mock_client.embeddings.create.side_effect = Exception("API Error")

                generator = EmbeddingGenerator()

                with pytest.raises(RuntimeError, match="Failed to generate embedding"):
                    generator.generate_embedding("test text")

    def test_generate_embedding_retry_logic(self):
        """Test embedding generation with retry logic."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                # Fail twice, then succeed
                mock_response = MagicMock()
                mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
                mock_client.embeddings.create.side_effect = [
                    Exception("API Error"),
                    Exception("API Error"),
                    mock_response
                ]

                generator = EmbeddingGenerator(max_retries=3)
                result = generator.generate_embedding("test text")

                assert isinstance(result, np.ndarray)
                assert mock_client.embeddings.create.call_count == 3

    def test_generate_embedding_max_retries_exceeded(self):
        """Test embedding generation when max retries exceeded."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                # Always fail
                mock_client.embeddings.create.side_effect = Exception("API Error")

                generator = EmbeddingGenerator(max_retries=2)

                with pytest.raises(RuntimeError, match="Failed to generate embedding"):
                    generator.generate_embedding("test text")

                # Should have tried initial + 2 retries = 3 total
                assert mock_client.embeddings.create.call_count == 3

    def test_cache_key_generation(self):
        """Test cache key generation for different texts."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            generator = EmbeddingGenerator()

            key1 = generator._get_cache_key("test text")
            key2 = generator._get_cache_key("test text")
            key3 = generator._get_cache_key("different text")

            # Same text should produce same key
            assert key1 == key2
            # Different text should produce different key
            assert key1 != key3

    def test_clear_cache(self):
        """Test cache clearing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                mock_response = MagicMock()
                mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
                mock_client.embeddings.create.return_value = mock_response

                generator = EmbeddingGenerator()
                generator.generate_embedding("test text")
                assert generator.cache.size() > 0

                generator.clear_cache()
                assert generator.cache.size() == 0

    def test_get_cache_stats(self):
        """Test cache statistics."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            with patch('src.ml.embeddings.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                mock_response = MagicMock()
                mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
                mock_client.embeddings.create.return_value = mock_response

                generator = EmbeddingGenerator()

                # Initial stats
                stats = generator.get_cache_stats()
                assert stats['size'] == 0
                assert stats['max_size'] == 1000

                generator.generate_embedding("test text")

                # Stats after embedding
                stats = generator.get_cache_stats()
                assert stats['size'] == 1
