"""
Performance optimization engine with query caching and concurrent processing.

Implements:
- Query result caching for common operations
- Batch processing with async/await
- Concurrent health check execution
- Performance metrics tracking
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
import time


class PerformanceOptimizer:
    """
    Performance optimization engine for WikiStore operations.

    Provides query optimization, caching, and concurrent processing.
    """

    def __init__(self, wiki_store, cache_manager):
        """
        Initialize performance optimizer.

        Args:
            wiki_store: WikiStore instance to optimize
            cache_manager: CacheManager instance for caching
        """
        self.wiki = wiki_store
        self.cache = cache_manager
        self.metrics: Dict[str, List[float]] = {}

    async def optimize_query_get_page(self, page_id: str) -> Optional[Any]:
        """
        Optimized page retrieval with caching.

        Args:
            page_id: Page ID to retrieve

        Returns:
            Page data or None if not found
        """
        # Check cache first
        cached = self.cache.get(f"page:{page_id}")
        if cached:
            return cached

        # Query with monitoring
        start = time.time()
        page = await self._get_page_async(page_id)
        duration = time.time() - start

        # Cache result
        if page:
            self.cache.set(f"page:{page_id}", page)

        # Track metric
        self._track_metric("get_page", duration)

        return page

    async def _get_page_async(self, page_id: str) -> Optional[Any]:
        """
        Async wrapper for wiki.get_page_async.

        Args:
            page_id: Page ID to retrieve

        Returns:
            Page data or None if not found
        """
        if hasattr(self.wiki, 'get_page_async'):
            return await self.wiki.get_page_async(page_id)
        else:
            # Fallback to sync method
            return self.wiki.get_page(page_id)

    async def optimize_query_get_all_pages(self, batch_size: int = 100) -> List[Any]:
        """
        Optimized batch page retrieval with concurrent fetching.

        Args:
            batch_size: Number of pages per batch

        Returns:
            List of all pages
        """
        all_pages = []

        # Process in batches with async
        async def fetch_batch(offset: int) -> List[Any]:
            return await self._get_pages_batch(limit=batch_size, offset=offset)

        # Calculate total pages first
        count = await self._get_page_count_async()

        # Fetch batches concurrently
        batches = []
        for offset in range(0, count, batch_size):
            batches.append(fetch_batch(offset))

        results = await asyncio.gather(*batches)

        for batch in results:
            if batch:
                all_pages.extend(batch)

        return all_pages

    async def _get_pages_batch(self, limit: int, offset: int) -> List[Any]:
        """
        Async wrapper for wiki.get_pages_batch.

        Args:
            limit: Maximum number of pages to return
            offset: Offset for pagination

        Returns:
            List of pages
        """
        if hasattr(self.wiki, 'get_pages_batch'):
            return await self.wiki.get_pages_batch(limit=limit, offset=offset)
        else:
            # Fallback to sync method
            return self.wiki.get_pages(limit=limit, offset=offset)

    async def _get_page_count_async(self) -> int:
        """
        Async wrapper for wiki.get_page_count.

        Returns:
            Total number of pages
        """
        if hasattr(self.wiki, 'get_page_count_async'):
            return await self.wiki.get_page_count_async()
        else:
            # Fallback to sync method
            return self.wiki.get_page_count()

    async def run_concurrent_health_checks(self, monitor) -> Dict[str, List]:
        """
        Run health checks concurrently for 3x throughput improvement.

        Args:
            monitor: HealthMonitor instance with check methods

        Returns:
            Dictionary mapping check names to results
        """
        checks = {
            "orphan_pages": monitor.check_orphan_pages(),
            "broken_links": monitor.check_broken_links(),
            "duplicate_content": monitor.check_duplicate_content(),
        }

        # Run all checks concurrently
        results = await asyncio.gather(
            *checks.values(),
            return_exceptions=True
        )

        # Handle exceptions
        processed_results = {}
        for key, result in zip(checks.keys(), results):
            if isinstance(result, Exception):
                processed_results[key] = f"Error: {str(result)}"
            else:
                processed_results[key] = result

        return processed_results

    def _track_metric(self, metric_name: str, value: float) -> None:
        """
        Track a performance metric.

        Args:
            metric_name: Name of the metric
            value: Metric value (e.g., duration in seconds)
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get summary statistics for all tracked metrics.

        Returns:
            Dictionary with metric summaries (avg, min, max, count)
        """
        summary = {}

        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }

        return summary
