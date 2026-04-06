"""
Observability and metrics for Wiki quality monitoring.

This module provides Prometheus-style metrics for monitoring system health,
performance, and quality indicators.
"""

import time
from typing import Dict, Callable, Any, Optional
from functools import wraps
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Counter:
    """
    A counter metric that only increases.
    """

    def __init__(self, name: str, description: str, labels: Optional[list] = None):
        """
        Initialize counter.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names
        """
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[tuple, float] = defaultdict(float)

    def inc(self, value: float = 1.0, **label_values):
        """
        Increment counter by value.

        Args:
            value: Amount to increment (default: 1.0)
            **label_values: Label values
        """
        label_key = tuple(label_values.get(label, "") for label in self.labels)
        self._values[label_key] += value

    def get_value(self, **label_values) -> float:
        """
        Get current counter value.

        Args:
            **label_values: Label values

        Returns:
            Current counter value
        """
        label_key = tuple(label_values.get(label, "") for label in self.labels)
        return self._values.get(label_key, 0.0)

    def reset(self):
        """Reset counter to zero."""
        self._values.clear()


class Histogram:
    """
    A histogram metric that counts observations in buckets.
    """

    def __init__(self, name: str, description: str, buckets: Optional[list] = None, labels: Optional[list] = None):
        """
        Initialize histogram.

        Args:
            name: Metric name
            description: Metric description
            buckets: Bucket boundaries (default: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
            labels: Optional label names
        """
        self.name = name
        self.description = description
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self.labels = labels or []
        self._observations: Dict[tuple, list] = defaultdict(list)
        self._sum: Dict[tuple, float] = defaultdict(float)
        self._count: Dict[tuple, float] = defaultdict(float)

    def observe(self, value: float, **label_values):
        """
        Observe a value.

        Args:
            value: Value to observe
            **label_values: Label values
        """
        label_key = tuple(label_values.get(label, "") for label in self.labels)
        self._observations[label_key].append(value)
        self._sum[label_key] += value
        self._count[label_key] += 1

    def get_count(self, **label_values) -> float:
        """
        Get total count of observations.

        Args:
            **label_values: Label values

        Returns:
            Total count
        """
        label_key = tuple(label_values.get(label, "") for label in self.labels)
        return self._count.get(label_key, 0.0)

    def get_sum(self, **label_values) -> float:
        """
        Get sum of all observations.

        Args:
            **label_values: Label values

        Returns:
            Sum of observations
        """
        label_key = tuple(label_values.get(label, "") for label in self.labels)
        return self._sum.get(label_key, 0.0)

    def get_average(self, **label_values) -> float:
        """
        Get average of observations.

        Args:
            **label_values: Label values

        Returns:
            Average value
        """
        count = self.get_count(**label_values)
        sum_value = self.get_sum(**label_values)
        return sum_value / count if count > 0 else 0.0

    def reset(self):
        """Reset histogram."""
        self._observations.clear()
        self._sum.clear()
        self._count.clear()


class MetricsRegistry:
    """
    Registry for quality monitoring metrics.
    """

    def __init__(self):
        """Initialize metrics registry."""
        # Counters
        self.health_check_counter = Counter(
            "health_check_total",
            "Total number of health checks performed",
            labels=["status"]
        )

        self.issue_counter = Counter(
            "issues_total",
            "Total number of issues detected",
            labels=["issue_type", "severity"]
        )

        self.alert_counter = Counter(
            "alerts_total",
            "Total number of alerts sent",
            labels=["alert_type"]
        )

        self.report_counter = Counter(
            "reports_total",
            "Total number of reports generated",
            labels=["report_type"]
        )

        # Histograms
        self.health_check_duration = Histogram(
            "health_check_duration_seconds",
            "Time taken to perform health check",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            labels=["check_type"]
        )

        self.issue_detection_duration = Histogram(
            "issue_detection_duration_seconds",
            "Time taken to detect issues",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels=["issue_type"]
        )

        self.report_generation_duration = Histogram(
            "report_generation_duration_seconds",
            "Time taken to generate reports",
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0],
            labels=["report_type"]
        )

        self.quality_score = Histogram(
            "quality_score",
            "Wiki quality scores",
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            labels=["dimension"]
        )

    def emit_metrics(self) -> Dict[str, Any]:
        """
        Emit all metrics as dictionary.

        Returns:
            Dictionary with all metric values
        """
        return {
            "counters": {
                "health_check_total": self._get_counter_values(self.health_check_counter),
                "issues_total": self._get_counter_values(self.issue_counter),
                "alerts_total": self._get_counter_values(self.alert_counter),
                "reports_total": self._get_counter_values(self.report_counter),
            },
            "histograms": {
                "health_check_duration": self._get_histogram_values(self.health_check_duration),
                "issue_detection_duration": self._get_histogram_values(self.issue_detection_duration),
                "report_generation_duration": self._get_histogram_values(self.report_generation_duration),
                "quality_score": self._get_histogram_values(self.quality_score),
            },
            "timestamp": datetime.now().isoformat()
        }

    def _get_counter_values(self, counter: Counter) -> Dict[str, float]:
        """Get all counter values."""
        return counter._values.copy() if hasattr(counter, '_values') else {}

    def _get_histogram_values(self, histogram: Histogram) -> Dict[str, Any]:
        """Get all histogram values."""
        return {
            "count": histogram._count.copy() if hasattr(histogram, '_count') else {},
            "sum": histogram._sum.copy() if hasattr(histogram, '_sum') else {},
        }

    def reset_all(self):
        """Reset all metrics."""
        self.health_check_counter.reset()
        self.issue_counter.reset()
        self.alert_counter.reset()
        self.report_counter.reset()
        self.health_check_duration.reset()
        self.issue_detection_duration.reset()
        self.report_generation_duration.reset()
        self.quality_score.reset()


# Global metrics registry instance
metrics = MetricsRegistry()


def emit_metrics(metric_type: str, **label_values):
    """
    Decorator to emit metrics for function calls.

    Args:
        metric_type: Type of metric to emit
        **label_values: Label values for the metric

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Record success metrics
                duration = time.time() - start_time

                if metric_type == "health_check":
                    metrics.health_check_counter.inc(**label_values, status="success")
                    metrics.health_check_duration.observe(duration, **label_values)
                elif metric_type == "issue_detection":
                    metrics.issue_detection_duration.observe(duration, **label_values)
                elif metric_type == "report_generation":
                    metrics.report_counter.inc(**label_values)
                    metrics.report_generation_duration.observe(duration, **label_values)

                return result

            except Exception as e:
                # Record failure metrics
                if metric_type == "health_check":
                    metrics.health_check_counter.inc(**label_values, status="failure")
                raise

        return wrapper
    return decorator


def get_metrics_summary() -> str:
    """
    Get human-readable metrics summary.

    Returns:
        Formatted metrics summary string
    """
    metrics_data = metrics.emit_metrics()

    summary = ["=== Wiki Quality Monitoring Metrics ==="]
    summary.append(f"Timestamp: {metrics_data['timestamp']}")

    summary.append("\n--- Counters ---")
    for counter_name, counter_values in metrics_data['counters'].items():
        if counter_values:
            summary.append(f"\n{counter_name}:")
            for labels, value in counter_values.items():
                label_str = ", ".join(f"{k}={v}" for k, v in zip(labels, range(len(labels))) if v)
                summary.append(f"  {label_str or '(no labels)'}: {value}")

    summary.append("\n--- Histograms ---")
    for hist_name, hist_values in metrics_data['histograms'].items():
        if hist_values['count']:
            summary.append(f"\n{hist_name}:")
            for labels, count in hist_values['count'].items():
                sum_value = hist_values['sum'].get(labels, 0)
                avg = sum_value / count if count > 0 else 0
                label_str = ", ".join(f"{k}={v}" for k, v in zip(labels, range(len(labels))) if v)
                summary.append(f"  {label_str or '(no labels)'}: count={count}, sum={sum_value:.2f}, avg={avg:.2f}")

    return "\n".join(summary)
