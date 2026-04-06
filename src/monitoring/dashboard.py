"""
Dashboard data preparation for knowledge compiler monitoring.

Provides structured data for visualization dashboards including
time series data, alert summaries, and system health metrics.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


@dataclass
class TimeSeriesPoint:
    """Single point in a time series."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class TimeSeries:
    """Time series data for visualization."""
    name: str
    description: str
    unit: str
    data_points: List[TimeSeriesPoint] = field(default_factory=list)
    aggregation: str = "avg"  # avg, sum, min, max, count


@dataclass
class DashboardPanel:
    """Dashboard panel configuration."""
    id: str
    title: str
    type: str  # "graph", "stat", "table", "gauge"
    query: str
    visualization: Dict[str, Any] = field(default_factory=dict)
    grid_pos: Dict[str, int] = field(default_factory=dict)


@dataclass
class Dashboard:
    """Dashboard configuration."""
    id: str
    title: str
    description: str
    panels: List[DashboardPanel] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    refresh_interval: int = 60  # seconds


class DashboardGenerator:
    """
    Generate dashboard data for monitoring visualization.

    Features:
    - Time series data aggregation
    - Alert summaries and trends
    - System health metrics
    - Performance metrics visualization
    - Multiple dashboard templates
    """

    def __init__(self):
        self.time_series_data: Dict[str, TimeSeries] = {}
        self.dashboard_templates = self._create_dashboard_templates()

    def add_time_series_point(
        self,
        series_name: str,
        value: float,
        timestamp: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        description: str = "",
        unit: str = ""
    ):
        """Add data point to time series."""
        timestamp = timestamp or datetime.utcnow()

        if series_name not in self.time_series_data:
            self.time_series_data[series_name] = TimeSeries(
                name=series_name,
                description=description,
                unit=unit
            )

        point = TimeSeriesPoint(
            timestamp=timestamp,
            value=value,
            labels=labels or {}
        )

        self.time_series_data[series_name].data_points.append(point)

    def get_time_series(
        self,
        series_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        aggregation: Optional[str] = None,
        bucket_size: Optional[timedelta] = None
    ) -> TimeSeries:
        """
        Get time series with optional aggregation.

        Args:
            series_name: Name of time series
            start_time: Start time for data (default: 24 hours ago)
            end_time: End time for data (default: now)
            aggregation: Aggregation method (avg, sum, min, max, count)
            bucket_size: Time bucket for aggregation

        Returns:
            Time series with aggregated data
        """
        if series_name not in self.time_series_data:
            return TimeSeries(name=series_name, description="", unit="")

        series = self.time_series_data[series_name]
        start_time = start_time or (datetime.utcnow() - timedelta(hours=24))
        end_time = end_time or datetime.utcnow()

        # Filter by time range
        filtered_points = [
            p for p in series.data_points
            if start_time <= p.timestamp <= end_time
        ]

        if aggregation and bucket_size:
            # Aggregate into buckets
            aggregated = self._aggregate_time_series(
                filtered_points,
                bucket_size,
                aggregation
            )
            return TimeSeries(
                name=series.name,
                description=series.description,
                unit=series.unit,
                data_points=aggregated,
                aggregation=aggregation
            )

        return TimeSeries(
            name=series.name,
            description=series.description,
            unit=series.unit,
            data_points=filtered_points
        )

    def _aggregate_time_series(
        self,
        points: List[TimeSeriesPoint],
        bucket_size: timedelta,
        aggregation: str
    ) -> List[TimeSeriesPoint]:
        """Aggregate time series points into buckets."""
        if not points:
            return []

        # Group points into buckets
        buckets: Dict[datetime, List[float]] = defaultdict(list)

        for point in points:
            # Calculate bucket timestamp
            bucket_timestamp = self._round_to_bucket(
                point.timestamp,
                bucket_size
            )
            buckets[bucket_timestamp].append(point.value)

        # Aggregate each bucket
        aggregated_points = []
        for bucket_timestamp, values in sorted(buckets.items()):
            if aggregation == "avg":
                agg_value = statistics.mean(values)
            elif aggregation == "sum":
                agg_value = sum(values)
            elif aggregation == "min":
                agg_value = min(values)
            elif aggregation == "max":
                agg_value = max(values)
            elif aggregation == "count":
                agg_value = len(values)
            else:
                agg_value = statistics.mean(values)

            aggregated_points.append(
                TimeSeriesPoint(
                    timestamp=bucket_timestamp,
                    value=agg_value
                )
            )

        return aggregated_points

    def _round_to_bucket(
        self,
        timestamp: datetime,
        bucket_size: timedelta
    ) -> datetime:
        """Round timestamp to bucket boundary."""
        timestamp_seconds = int(timestamp.timestamp())
        bucket_seconds = int(bucket_size.total_seconds())
        bucket_timestamp = (timestamp_seconds // bucket_seconds) * bucket_seconds
        return datetime.fromtimestamp(bucket_timestamp)

    def generate_dashboard_data(
        self,
        dashboard_type: str = "overview"
    ) -> Dict[str, Any]:
        """
        Generate dashboard data for visualization.

        Args:
            dashboard_type: Type of dashboard (overview, performance, alerts)

        Returns:
            Dashboard data with time series and stats
        """
        dashboard_data = {
            "dashboard_type": dashboard_type,
            "generated_at": datetime.utcnow().isoformat(),
            "time_series": [],
            "stats": {},
            "alerts": {}
        }

        if dashboard_type == "overview":
            dashboard_data.update(self._generate_overview_data())
        elif dashboard_type == "performance":
            dashboard_data.update(self._generate_performance_data())
        elif dashboard_type == "alerts":
            dashboard_data.update(self._generate_alerts_data())

        return dashboard_data

    def _generate_overview_data(self) -> Dict[str, Any]:
        """Generate overview dashboard data."""
        # Get recent time series
        recent_series = []
        for name, series in self.time_series_data.items():
            recent = self.get_time_series(
                name,
                bucket_size=timedelta(minutes=5),
                aggregation="avg"
            )
            if recent.data_points:
                recent_series.append({
                    "name": name,
                    "description": series.description,
                    "unit": series.unit,
                    "current_value": recent.data_points[-1].value,
                    "data": [
                        {
                            "timestamp": p.timestamp.isoformat(),
                            "value": p.value
                        }
                        for p in recent.data_points[-100:]  # Last 100 points
                    ]
                })

        # Calculate stats
        stats = {
            "total_metrics": len(self.time_series_data),
            "active_time_series": len(recent_series),
            "data_points": sum(
                len(series.data_points)
                for series in self.time_series_data.values()
            )
        }

        return {
            "time_series": recent_series,
            "stats": stats
        }

    def _generate_performance_data(self) -> Dict[str, Any]:
        """Generate performance dashboard data."""
        performance_metrics = [
            "document_processing_duration",
            "query_duration",
            "cache_hit_rate",
            "throughput"
        ]

        time_series = []
        for metric_name in performance_metrics:
            if metric_name in self.time_series_data:
                series = self.get_time_series(
                    metric_name,
                    bucket_size=timedelta(minutes=1),
                    aggregation="avg"
                )
                if series.data_points:
                    values = [p.value for p in series.data_points]
                    time_series.append({
                        "name": metric_name,
                        "current": values[-1] if values else 0,
                        "avg": statistics.mean(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                        "data": [
                            {
                                "timestamp": p.timestamp.isoformat(),
                                "value": p.value
                            }
                            for p in series.data_points[-60:]  # Last 60 minutes
                        ]
                    })

        return {
            "time_series": time_series,
            "stats": {
                "metrics_monitored": len(time_series)
            }
        }

    def _generate_alerts_data(self) -> Dict[str, Any]:
        """Generate alerts dashboard data."""
        # This would integrate with AlertManager
        # For now, return placeholder structure
        return {
            "time_series": [],
            "stats": {
                "active_alerts": 0,
                "resolved_today": 0,
                "total_alerts_24h": 0
            },
            "alerts": {
                "by_severity": {},
                "recent": []
            }
        }

    def _create_dashboard_templates(self) -> Dict[str, Dashboard]:
        """Create dashboard templates."""
        templates = {}

        # Overview dashboard
        overview = Dashboard(
            id="overview",
            title="Knowledge Compiler Overview",
            description="High-level system metrics and health",
            panels=[
                DashboardPanel(
                    id="throughput",
                    title="Documents Processed",
                    type="graph",
                    query="documents_processed_total",
                    grid_pos={"x": 0, "y": 0, "w": 12, "h": 8}
                ),
                DashboardPanel(
                    id="error_rate",
                    title="Error Rate",
                    type="graph",
                    query="error_rate",
                    visualization={"unit": "percent"},
                    grid_pos={"x": 12, "y": 0, "w": 12, "h": 8}
                ),
                DashboardPanel(
                    id="cache_efficiency",
                    title="Cache Hit Rate",
                    type="gauge",
                    query="cache_hit_rate",
                    visualization={
                        "min": 0,
                        "max": 100,
                        "unit": "percent"
                    },
                    grid_pos={"x": 0, "y": 8, "w": 6, "h": 4}
                ),
                DashboardPanel(
                    id="active_connections",
                    title="Active Connections",
                    type="stat",
                    query="active_connections",
                    grid_pos={"x": 6, "y": 8, "w": 6, "h": 4}
                )
            ]
        )
        templates["overview"] = overview

        # Performance dashboard
        performance = Dashboard(
            id="performance",
            title="Performance Metrics",
            description="Detailed performance and latency metrics",
            panels=[
                DashboardPanel(
                    id="processing_duration",
                    title="Document Processing Duration",
                    type="graph",
                    query="document_processing_duration_seconds",
                    visualization={"unit": "seconds"},
                    grid_pos={"x": 0, "y": 0, "w": 24, "h": 8}
                ),
                DashboardPanel(
                    id="query_duration",
                    title="Query Duration",
                    type="graph",
                    query="query_duration_seconds",
                    visualization={"unit": "seconds"},
                    grid_pos={"x": 0, "y": 8, "w": 12, "h": 8}
                ),
                DashboardPanel(
                    id="queue_depth",
                    title="Queue Depth",
                    type="graph",
                    query="queue_depth",
                    grid_pos={"x": 12, "y": 8, "w": 12, "h": 8}
                )
            ]
        )
        templates["performance"] = performance

        # Alerts dashboard
        alerts = Dashboard(
            id="alerts",
            title="Alerts and Incidents",
            description="Active alerts and alert history",
            panels=[
                DashboardPanel(
                    id="active_alerts",
                    title="Active Alerts",
                    type="table",
                    query="active_alerts",
                    grid_pos={"x": 0, "y": 0, "w": 24, "h": 8}
                ),
                DashboardPanel(
                    id="alert_rate",
                    title="Alert Rate",
                    type="graph",
                    query="alert_rate",
                    grid_pos={"x": 0, "y": 8, "w": 12, "h": 8}
                ),
                DashboardPanel(
                    id="alert_summary",
                    title="Alert Summary (24h)",
                    type="stat",
                    query="alert_summary_24h",
                    grid_pos={"x": 12, "y": 8, "w": 12, "h": 8}
                )
            ]
        )
        templates["alerts"] = alerts

        return templates

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard template by ID."""
        return self.dashboard_templates.get(dashboard_id)

    def list_dashboards(self) -> List[str]:
        """List available dashboard IDs."""
        return list(self.dashboard_templates.keys())

    def export_dashboard_config(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """Export dashboard configuration for Grafana/other tools."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return None

        return {
            "dashboard": {
                "id": dashboard.id,
                "title": dashboard.title,
                "description": dashboard.description,
                "refresh": f"{dashboard.refresh_interval}s",
                "panels": [
                    {
                        "id": panel.id,
                        "title": panel.title,
                        "type": panel.type,
                        "targets": [{"expr": panel.query}],
                        "fieldConfig": {
                            "defaults": {
                                "unit": panel.visualization.get("unit", "short")
                            }
                        },
                        "gridPos": panel.grid_pos
                    }
                    for panel in dashboard.panels
                ]
            }
        }
