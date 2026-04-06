"""
Metrics collection for knowledge compiler monitoring.

Provides Prometheus-style metrics collection with counter, gauge,
histogram, and summary metric types.
"""

import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading


@dataclass
class MetricValue:
    """Single metric value with labels."""
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """
    Counter metric that only increases.

    Usage:
        counter = Counter("documents_processed", "Total documents processed")
        counter.inc({"language": "python"})
        counter.inc(5, {"language": "javascript"})
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._values: Dict[str, MetricValue] = {}
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment counter by amount."""
        label_key = self._label_key(labels or {})
        with self._lock:
            if label_key in self._values:
                self._values[label_key].value += amount
                self._values[label_key].timestamp = time.time()
            else:
                self._values[label_key] = MetricValue(
                    value=amount,
                    labels=labels or {}
                )

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value."""
        label_key = self._label_key(labels or {})
        return self._values.get(label_key, MetricValue(0.0)).value

    def get_all(self) -> List[MetricValue]:
        """Get all counter values."""
        return list(self._values.values())

    def _label_key(self, labels: Dict[str, str]) -> str:
        """Create hashable key from labels."""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Gauge:
    """
    Gauge metric that can increase or decrease.

    Usage:
        gauge = Gauge("active_connections", "Active database connections")
        gauge.set(10)
        gauge.inc()
        gauge.dec()
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._value: MetricValue = MetricValue(0.0)
        self._lock = threading.Lock()

    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value."""
        with self._lock:
            self._value = MetricValue(
                value=value,
                labels=labels or {}
            )

    def inc(self, amount: float = 1.0):
        """Increment gauge."""
        with self._lock:
            self._value.value += amount
            self._value.timestamp = time.time()

    def dec(self, amount: float = 1.0):
        """Decrement gauge."""
        with self._lock:
            self._value.value -= amount
            self._value.timestamp = time.time()

    def get(self) -> float:
        """Get gauge value."""
        return self._value.value

    def get_metric(self) -> MetricValue:
        """Get gauge metric value."""
        return self._value


class Histogram:
    """
    Histogram metric that counts observations in buckets.

    Usage:
        histogram = Histogram(
            "request_duration_seconds",
            "Request duration",
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0]
        )
        histogram.observe(0.23)
        histogram.observe(1.45)
    """

    def __init__(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None
    ):
        self.name = name
        self.description = description
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self.buckets.sort()
        self._bucket_counts: Dict[float, float] = {b: 0.0 for b in self.buckets}
        self._count = 0.0
        self._sum = 0.0
        self._lock = threading.Lock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value."""
        with self._lock:
            self._count += 1
            self._sum += value

            for bucket in self.buckets:
                if value <= bucket:
                    self._bucket_counts[bucket] += 1

    def get_count(self) -> float:
        """Get total count of observations."""
        return self._count

    def get_sum(self) -> float:
        """Get sum of all observations."""
        return self._sum

    def get_avg(self) -> float:
        """Get average of all observations."""
        return self._sum / self._count if self._count > 0 else 0.0

    def get_buckets(self) -> Dict[float, float]:
        """Get bucket counts."""
        return self._bucket_counts.copy()


class Summary:
    """
    Summary metric that calculates quantiles over a sliding window.

    Usage:
        summary = Summary("response_size", "Response size in bytes")
        summary.observe(1024)
        summary.observe(2048)
    """

    def __init__(
        self,
        name: str,
        description: str,
        window_size: int = 1000,
        quantiles: Optional[List[float]] = None
    ):
        self.name = name
        self.description = description
        self.window_size = window_size
        self.quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        self._values: List[float] = []
        self._count = 0.0
        self._sum = 0.0
        self._lock = threading.Lock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value."""
        with self._lock:
            self._values.append(value)
            self._count += 1
            self._sum += value

            # Keep window size
            if len(self._values) > self.window_size:
                removed = self._values.pop(0)
                self._sum -= removed

    def get_count(self) -> float:
        """Get total count of observations."""
        return self._count

    def get_sum(self) -> float:
        """Get sum of all observations."""
        return self._sum

    def get_avg(self) -> float:
        """Get average of all observations."""
        return self._sum / self._count if self._count > 0 else 0.0

    def get_quantile(self, q: float) -> float:
        """Get quantile value."""
        if not self._values:
            return 0.0

        sorted_values = sorted(self._values)
        pos = q * (len(sorted_values) - 1)
        lower = int(pos)
        upper = min(lower + 1, len(sorted_values) - 1)

        if lower == upper:
            return sorted_values[lower]

        return sorted_values[lower] * (upper - pos) + sorted_values[upper] * (pos - lower)


class MetricsRegistry:
    """
    Central registry for all metrics.

    Usage:
        registry = MetricsRegistry()

        # Define metrics
        registry.counter("documents_processed", "Total documents processed")
        registry.gauge("active_connections", "Active connections")
        registry.histogram("request_duration", "Request duration")

        # Use metrics
        registry.get_counter("documents_processed").inc()
        registry.get_histogram("request_duration").observe(0.23)

        # Export metrics
        metrics_data = registry.export_metrics()
    """

    def __init__(self):
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}
        self._lock = threading.Lock()

    def counter(self, name: str, description: str) -> Counter:
        """Create or get counter metric."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description)
            return self._counters[name]

    def gauge(self, name: str, description: str) -> Gauge:
        """Create or get gauge metric."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description)
            return self._gauges[name]

    def histogram(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None
    ) -> Histogram:
        """Create or get histogram metric."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, buckets)
            return self._histograms[name]

    def summary(
        self,
        name: str,
        description: str,
        window_size: int = 1000,
        quantiles: Optional[List[float]] = None
    ) -> Summary:
        """Create or get summary metric."""
        with self._lock:
            if name not in self._summaries:
                self._summaries[name] = Summary(name, description, window_size, quantiles)
            return self._summaries[name]

    def get_counter(self, name: str) -> Optional[Counter]:
        """Get counter by name."""
        return self._counters.get(name)

    def get_gauge(self, name: str) -> Optional[Gauge]:
        """Get gauge by name."""
        return self._gauges.get(name)

    def get_histogram(self, name: str) -> Optional[Histogram]:
        """Get histogram by name."""
        return self._histograms.get(name)

    def get_summary(self, name: str) -> Optional[Summary]:
        """Get summary by name."""
        return self._summaries.get(name)

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics as dictionary."""
        export = {
            "timestamp": datetime.utcnow().isoformat(),
            "counters": {},
            "gauges": {},
            "histograms": {},
            "summaries": {}
        }

        for name, counter in self._counters.items():
            export["counters"][name] = {
                "description": counter.description,
                "values": [
                    {
                        "value": v.value,
                        "labels": v.labels,
                        "timestamp": v.timestamp
                    }
                    for v in counter.get_all()
                ]
            }

        for name, gauge in self._gauges.items():
            metric = gauge.get_metric()
            export["gauges"][name] = {
                "description": gauge.description,
                "value": metric.value,
                "labels": metric.labels,
                "timestamp": metric.timestamp
            }

        for name, histogram in self._histograms.items():
            export["histograms"][name] = {
                "description": histogram.description,
                "count": histogram.get_count(),
                "sum": histogram.get_sum(),
                "avg": histogram.get_avg(),
                "buckets": histogram.get_buckets()
            }

        for name, summary in self._summaries.items():
            quantiles = {q: summary.get_quantile(q) for q in summary.quantiles}
            export["summaries"][name] = {
                "description": summary.description,
                "count": summary.get_count(),
                "sum": summary.get_sum(),
                "avg": summary.get_avg(),
                "quantiles": quantiles
            }

        return export


# Global metrics registry
_global_registry = MetricsRegistry()


def get_metrics_registry() -> MetricsRegistry:
    """Get global metrics registry."""
    return _global_registry
