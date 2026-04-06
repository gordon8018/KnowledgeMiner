"""
Multi-level caching system for performance optimization.

Implements L1 (in-memory) and L2 (disk) caching with:
- Automatic L2-to-L1 promotion on access
- TTL-based expiration
- Pattern-based invalidation
- Cache statistics and hit rate tracking
"""

from functools import lru_cache
from typing import Optional, Any, Dict
import hashlib
import json
import time
from pathlib import Path


class CacheManager:
    """Multi-level caching system with L1 (memory) and L2 (disk) layers."""

    def __init__(self, l1_max_size: int = 1000, l2_cache_path: Optional[str] = None):
        """
        Initialize cache manager.

        Args:
            l1_max_size: Maximum number of items in L1 cache
            l2_cache_path: Path to L2 cache file (None to disable)
        """
        self.l1_cache: Dict[str, Any] = {}  # In-memory cache
        self.l1_max_size = l1_max_size
        self.l2_cache_path = l2_cache_path
        self.l2_cache: Dict[str, Dict[str, Any]] = {}
        self._load_l2_cache()

        self.stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "evictions": 0
        }

    def _load_l2_cache(self) -> None:
        """Load L2 cache from disk."""
        if self.l2_cache_path:
            try:
                cache_file = Path(self.l2_cache_path)
                if cache_file.exists():
                    with open(cache_file, 'r') as f:
                        self.l2_cache = json.load(f)
            except Exception:
                self.l2_cache = {}

    def _save_l2_cache(self) -> None:
        """Save L2 cache to disk."""
        if self.l2_cache_path:
            try:
                with open(self.l2_cache_path, 'w') as f:
                    json.dump(self.l2_cache, f)
            except Exception:
                pass  # Fail silently - cache is optional

    def _set_l1(self, key: str, value: Any) -> None:
        """Set value in L1 cache with eviction."""
        # Evict if over limit (simple FIFO)
        if len(self.l1_cache) >= self.l1_max_size:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self.l1_cache))
            del self.l1_cache[oldest_key]
            self.stats["evictions"] += 1

        self.l1_cache[key] = value

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L1 → L2 → miss).

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        # Try L1 cache first
        if key in self.l1_cache:
            self.stats["l1_hits"] += 1
            return self.l1_cache[key]

        # Try L2 cache
        if key in self.l2_cache:
            entry = self.l2_cache[key]

            # Check expiration
            if time.time() > entry.get("expires", float('inf')):
                # Expired - remove and return miss
                del self.l2_cache[key]
                self._save_l2_cache()
                self.stats["l2_misses"] += 1
                self.stats["l1_misses"] += 1
                return None

            self.stats["l2_hits"] += 1

            # Promote to L1
            self._set_l1(key, entry["value"])
            return entry["value"]

        # Cache miss
        self.stats["l1_misses"] += 1
        self.stats["l2_misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set value in cache (both L1 and L2).

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        # Set in L1
        self._set_l1(key, value)

        # Set in L2
        if self.l2_cache_path:
            self.l2_cache[key] = {
                "value": value,
                "expires": time.time() + ttl
            }
            self._save_l2_cache()

    def invalidate(self, pattern: str) -> None:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match (sub-string matching)
        """
        # Invalidate from L1
        to_remove = [k for k in self.l1_cache.keys() if pattern in k]
        for k in to_remove:
            del self.l1_cache[k]
            self.stats["evictions"] += 1

        # Invalidate from L2
        if self.l2_cache_path:
            for k in list(self.l2_cache.keys()):
                if pattern in k:
                    del self.l2_cache[k]
            self._save_l2_cache()

    def get_stats(self) -> Dict[str, Any]:
        """
        Return cache statistics.

        Returns:
            Dictionary with cache stats including hit rates
        """
        # L1 hit rate: hits / (hits + misses) at L1 level
        l1_requests = self.stats["l1_hits"] + self.stats["l1_misses"]
        l1_hit_rate = (self.stats["l1_hits"] / l1_requests
                       if l1_requests > 0 else 0)

        # L2 hit rate: hits / (hits + misses) at L2 level
        l2_requests = self.stats["l2_hits"] + self.stats["l2_misses"]
        l2_hit_rate = (self.stats["l2_hits"] / l2_requests
                       if l2_requests > 0 else 0)

        # Total unique get requests (not double-counting L2 misses)
        total_requests = l1_requests + self.stats["l2_hits"]

        return {
            "l1_hit_rate": l1_hit_rate,
            "l2_hit_rate": l2_hit_rate,
            "total_requests": total_requests,
            "l1_size": len(self.l1_cache),
            "l2_size": len(self.l2_cache),
            "evictions": self.stats["evictions"]
        }
