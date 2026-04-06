"""
Performance monitoring and reporting.

Tracks:
- Query execution times
- Cache effectiveness
- Throughput metrics
- Performance degradation alerts
"""

from typing import List, Dict, Any
import time


class PerformanceMonitor:
    """
    Performance tracking and reporting system.

    Monitors query execution times and generates performance summaries.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.query_times: List[Dict[str, Any]] = []
        self.cache_stats: List[Dict[str, Any]] = []
        self.start_time = time.time()

    def track_query(self, query_type: str, duration: float) -> None:
        """
        Track query execution time.

        Args:
            query_type: Type of query (e.g., "get_page", "search")
            duration: Execution time in seconds
        """
        self.query_times.append({
            "type": query_type,
            "duration": duration,
            "timestamp": time.time()
        })

    def track_cache_stats(self, stats: Dict[str, Any]) -> None:
        """
        Track cache statistics over time.

        Args:
            stats: Cache statistics from CacheManager.get_stats()
        """
        self.cache_stats.append({
            "stats": stats,
            "timestamp": time.time()
        })

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Generate performance summary from tracked metrics.

        Returns:
            Dictionary with performance statistics
        """
        if not self.query_times:
            return {
                "status": "no_data",
                "total_queries": 0,
                "uptime_seconds": time.time() - self.start_time
            }

        durations = [q["duration"] for q in self.query_times]

        # Calculate throughput
        total_time = sum(durations)
        queries_per_second = len(durations) / total_time if total_time > 0 else 0

        # Group by query type
        by_type: Dict[str, List[float]] = {}
        for query in self.query_times:
            query_type = query["type"]
            if query_type not in by_type:
                by_type[query_type] = []
            by_type[query_type].append(query["duration"])

        # Calculate stats per query type
        type_stats = {}
        for query_type, type_durations in by_type.items():
            type_stats[query_type] = {
                "count": len(type_durations),
                "avg": sum(type_durations) / len(type_durations),
                "min": min(type_durations),
                "max": max(type_durations)
            }

        return {
            "avg_query_time": sum(durations) / len(durations),
            "max_query_time": max(durations),
            "min_query_time": min(durations),
            "total_queries": len(self.query_times),
            "queries_per_second": queries_per_second,
            "uptime_seconds": time.time() - self.start_time,
            "by_type": type_stats
        }

    def get_cache_effectiveness(self) -> Dict[str, Any]:
        """
        Analyze cache effectiveness over time.

        Returns:
            Dictionary with cache performance metrics
        """
        if not self.cache_stats:
            return {"status": "no_cache_data"}

        # Get latest stats
        latest = self.cache_stats[-1]["stats"]

        # Calculate trends
        if len(self.cache_stats) >= 2:
            prev = self.cache_stats[-2]["stats"]
            hit_rate_change = latest["l1_hit_rate"] - prev["l1_hit_rate"]
        else:
            hit_rate_change = 0

        return {
            "latest_hit_rate": latest["l1_hit_rate"],
            "total_requests": latest["total_requests"],
            "cache_size": {
                "l1": latest["l1_size"],
                "l2": latest["l2_size"]
            },
            "hit_rate_trend": hit_rate_change,
            "samples": len(self.cache_stats)
        }

    def check_performance_degradation(self, threshold: float = 2.0) -> Dict[str, Any]:
        """
        Check for performance degradation (queries slower than threshold).

        Args:
            threshold: Multiplier of baseline average to alert on

        Returns:
            Dictionary with degradation status and details
        """
        if len(self.query_times) < 10:
            return {"status": "insufficient_data"}

        # Calculate baseline (first half of queries)
        mid_point = len(self.query_times) // 2
        baseline = self.query_times[:mid_point]
        recent = self.query_times[mid_point:]

        baseline_avg = sum(q["duration"] for q in baseline) / len(baseline)
        recent_avg = sum(q["duration"] for q in recent) / len(recent)

        degradation_factor = recent_avg / baseline_avg if baseline_avg > 0 else 0

        is_degraded = degradation_factor > threshold

        return {
            "status": "degraded" if is_degraded else "healthy",
            "baseline_avg": baseline_avg,
            "recent_avg": recent_avg,
            "degradation_factor": degradation_factor,
            "threshold": threshold,
            "alert": is_degraded
        }

    def generate_report(self) -> str:
        """
        Generate a human-readable performance report.

        Returns:
            Formatted report string
        """
        summary = self.get_performance_summary()
        cache_eff = self.get_cache_effectiveness()
        degradation = self.check_performance_degradation()

        lines = [
            "=== Performance Report ===",
            f"Total Queries: {summary.get('total_queries', 0)}",
            f"Average Query Time: {summary.get('avg_query_time', 0):.4f}s",
            f"Queries Per Second: {summary.get('queries_per_second', 0):.2f}",
            "",
            "Cache Performance:",
            f"  L1 Hit Rate: {cache_eff.get('latest_hit_rate', 0):.1%}",
            f"  L1 Size: {cache_eff.get('cache_size', {}).get('l1', 0)}",
            f"  L2 Size: {cache_eff.get('cache_size', {}).get('l2', 0)}",
            "",
            f"Status: {degradation.get('status', 'unknown').upper()}",
        ]

        if degradation.get("alert"):
            lines.append(
                f"  ⚠️  ALERT: Performance degraded by "
                f"{degradation.get('degradation_factor', 0):.2f}x"
            )

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all tracked metrics."""
        self.query_times = []
        self.cache_stats = []
        self.start_time = time.time()
