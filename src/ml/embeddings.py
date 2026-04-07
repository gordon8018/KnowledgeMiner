"""Embedding generation using OpenAI's API."""

import os
import hashlib
import time
from typing import List, Optional, Dict, Any
import numpy as np
import openai


class EmbeddingCache:
    """Cache for storing embeddings to avoid redundant API calls."""

    def __init__(self, max_size: int = 1000):
        """Initialize the embedding cache.

        Args:
            max_size: Maximum number of embeddings to store in cache
        """
        self._cache: Dict[str, np.ndarray] = {}
        self.max_size = max_size

    def get(self, key: str) -> Optional[np.ndarray]:
        """Get embedding from cache.

        Args:
            key: Cache key (hash of text)

        Returns:
            Cached embedding or None if not found
        """
        return self._cache.get(key)

    def put(self, key: str, embedding: np.ndarray) -> None:
        """Store embedding in cache.

        Args:
            key: Cache key (hash of text)
            embedding: Embedding vector to cache
        """
        # Evict oldest entries if cache is full
        if len(self._cache) >= self.max_size and key not in self._cache:
            # Remove first (oldest) entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[key] = embedding

    def clear(self) -> None:
        """Clear all cached embeddings."""
        self._cache.clear()

    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of cached embeddings
        """
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists in cache
        """
        return key in self._cache


class EmbeddingGenerator:
    """Generate embeddings using OpenAI's API."""

    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        dimensions: Optional[int] = None,
        batch_size: int = 100,
        max_retries: int = 3,
        cache_max_size: int = 1000
    ):
        """Initialize the embedding generator.

        Args:
            model_name: OpenAI embedding model to use
            dimensions: Embedding dimensions (None for model default)
            batch_size: Number of texts to process in each batch
            max_retries: Maximum number of retries for API failures
            cache_max_size: Maximum size of embedding cache

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set when needed
        """
        self.model_name = model_name
        self.dimensions = dimensions
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.cache = EmbeddingCache(max_size=cache_max_size)

        # Delay client initialization until first use
        self.client = None
        self._client_initialized = False

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text.

        Args:
            text: Text to generate key for

        Returns:
            MD5 hash of the text
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _ensure_client(self):
        """Ensure OpenAI client is initialized.

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
        """
        if not self._client_initialized:
            # Check for API key
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required for embedding generation")

            # Initialize OpenAI client
            self.client = openai.OpenAI(api_key=api_key)
            self._client_initialized = True

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as numpy array

        Raises:
            RuntimeError: If API call fails after max retries
            ValueError: If OPENAI_API_KEY environment variable is not set
        """
        # Ensure client is initialized
        self._ensure_client()

        # Check cache first
        cache_key = self._get_cache_key(text)
        cached_embedding = self.cache.get(cache_key)

        if cached_embedding is not None:
            return cached_embedding

        # Generate new embedding
        embedding = self._generate_embedding_with_retry(text)

        # Cache the result
        self.cache.put(cache_key, embedding)

        return embedding

    def _generate_embedding_with_retry(self, text: str) -> np.ndarray:
        """Generate embedding with retry logic.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as numpy array

        Raises:
            RuntimeError: If API call fails after max retries
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.embeddings.create(
                    input=text,
                    model=self.model_name,
                    dimensions=self.dimensions
                )
                embedding = response.data[0].embedding
                return np.array(embedding, dtype=np.float32)

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    break

        raise RuntimeError(f"Failed to generate embedding after {self.max_retries + 1} attempts: {last_error}")

    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors as numpy arrays
        """
        if not texts:
            return []

        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._generate_batch_embeddings(batch)
            embeddings.extend(batch_embeddings)

        return embeddings

    def _generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: Batch of texts to process

        Returns:
            List of embedding vectors
        """
        # Separate cached and uncached texts
        cache_keys = [self._get_cache_key(text) for text in texts]
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, key in enumerate(cache_keys):
            cached = self.cache.get(key)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(texts[i])

        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = self._generate_batch_with_retry(uncached_texts)

            # Cache and place results
            for idx, text, embedding in zip(uncached_indices, uncached_texts, new_embeddings):
                cache_key = cache_keys[idx]
                self.cache.put(cache_key, embedding)
                results[idx] = embedding

        return results

    def _generate_batch_with_retry(self, texts: List[str]) -> List[np.ndarray]:
        """Generate batch embeddings with retry logic.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors

        Raises:
            RuntimeError: If API call fails after max retries
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.model_name,
                    dimensions=self.dimensions
                )
                embeddings = [np.array(item.embedding, dtype=np.float32) for item in response.data]
                return embeddings

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    break

        raise RuntimeError(f"Failed to generate embeddings after {self.max_retries + 1} attempts: {last_error}")

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats (size, max_size)
        """
        return {
            'size': self.cache.size(),
            'max_size': self.cache.max_size
        }
