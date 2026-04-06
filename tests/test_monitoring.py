"""
Tests for monitoring and alerting system (Task 5.2).
"""

import pytest
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.monitoring.structured_logger import (
    StructuredLogger,
    StructuredFormatter,
    get_logger
)
from src.monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    MetricsRegistry
)
from src.monitoring.alerts import (
    AlertManager,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    Alert,
    AlertNotification
)
from src.monitoring.dashboard import (
    DashboardGenerator,
    TimeSeriesPoint,
    TimeSeries,
    Dashboard
)


class TestStructuredLogger:
    """Test structured logging functionality."""

    def test_logger_creation(self):
        """Test creating logger with and without file."""
        # Logger without file
        logger = StructuredLogger("test_logger")
        assert logger.logger.name == "test_logger"
        assert len(logger.logger.handlers) == 1  # Console only

        # Logger with file
        with patch("pathlib.Path.mkdir"):
            logger_with_file = StructuredLogger(
                "test_logger_file",
                log_file="test.log"
            )
            assert len(logger_with_file.logger.handlers) == 2  # Console + file

    def test_logger_levels(self):
        """Test different log levels."""
        logger = StructuredLogger("test_levels")
        assert logger.logger.level == 20  # INFO level

        logger_debug = StructuredLogger("test_debug", level=10)  # DEBUG
        assert logger_debug.logger.level == 10

    def test_context_manager(self):
        """Test context-aware logging."""
        logger = StructuredLogger("test_context")

        with logger.context(operation="test", document_id="123"):
            assert logger._context == {"operation": "test", "document_id": "123"}
            logger.info("Processing document")

        # Context should be cleared
        assert logger._context == {}

    def test_nested_context(self):
        """Test nested context contexts."""
        logger = StructuredLogger("test_nested")

        with logger.context(level1="value1"):
            assert logger._context == {"level1": "value1"}

            with logger.context(level2="value2"):
                assert logger._context == {
                    "level1": "value1",
                    "level2": "value2"
                }

            # Inner context cleared
            assert logger._context == {"level1": "value1"}

        # All contexts cleared
        assert logger._context == {}

    def test_measure_time(self):
        """Test performance timing context manager."""
        logger = StructuredLogger("test_timing")
        logger.info = Mock()  # Mock logger.info to capture calls

        with logger.measure_time("test_operation"):
            time.sleep(0.01)

        # Should have called info twice (start and end)
        assert logger.info.call_count == 2

        # Last call should have duration in kwargs
        last_call = logger.info.call_args_list[-1]
        # The kwargs are passed directly as keyword arguments
        call_kwargs = last_call[1]
        assert "duration_seconds" in call_kwargs
        assert call_kwargs["duration_seconds"] > 0
        assert "operation" in call_kwargs
        assert call_kwargs["operation"] == "test_operation"

    def test_structured_formatter(self):
        """Test JSON log formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        log_entry = json.loads(formatted)

        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test message"
        assert log_entry["logger"] == "test"
        assert "timestamp" in log_entry

    def test_get_logger_factory(self):
        """Test logger factory function."""
        logger = get_logger("factory_test")
        assert isinstance(logger, StructuredLogger)


class TestMetrics:
    """Test metrics collection."""

    def test_counter_inc(self):
        """Test counter increment."""
        counter = Counter("test_counter", "Test counter")
        assert counter.get() == 0.0

        counter.inc()
        assert counter.get() == 1.0

        counter.inc(5)
        assert counter.get() == 6.0

    def test_counter_with_labels(self):
        """Test counter with labels."""
        counter = Counter("test_counter", "Test counter")
        counter.inc(labels={"status": "success"})
        counter.inc(labels={"status": "error"})

        values = counter.get_all()
        assert len(values) == 2

        # Check label-specific values
        assert counter.get(labels={"status": "success"}) == 1.0
        assert counter.get(labels={"status": "error"}) == 1.0

    def test_gauge_set(self):
        """Test gauge set operations."""
        gauge = Gauge("test_gauge", "Test gauge")
        assert gauge.get() == 0.0

        gauge.set(10)
        assert gauge.get() == 10.0

        gauge.set(5.5)
        assert gauge.get() == 5.5

    def test_gauge_inc_dec(self):
        """Test gauge increment and decrement."""
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(10)

        gauge.inc()
        assert gauge.get() == 11.0

        gauge.dec(3)
        assert gauge.get() == 8.0

    def test_histogram_observe(self):
        """Test histogram observation."""
        histogram = Histogram(
            "test_histogram",
            "Test histogram",
            buckets=[1.0, 5.0, 10.0]
        )

        histogram.observe(0.5)
        histogram.observe(2.0)
        histogram.observe(7.0)
        histogram.observe(15.0)

        assert histogram.get_count() == 4.0
        assert histogram.get_sum() == 24.5
        assert histogram.get_avg() == pytest.approx(6.125)

        buckets = histogram.get_buckets()
        assert buckets[1.0] == 1.0  # Only 0.5 <= 1.0
        assert buckets[5.0] == 2.0  # 0.5, 2.0 <= 5.0
        assert buckets[10.0] == 3.0  # 0.5, 2.0, 7.0 <= 10.0

    def test_summary_quantiles(self):
        """Test summary quantile calculation."""
        summary = Summary("test_summary", "Test summary")

        # Add values
        for i in range(100):
            summary.observe(float(i))

        assert summary.get_count() == 100.0
        assert summary.get_sum() == 4950.0  # Sum of 0-99
        assert summary.get_avg() == 49.5

        # Check quantiles
        assert summary.get_quantile(0.5) == pytest.approx(49.5, rel=0.1)
        assert summary.get_quantile(0.9) == pytest.approx(89.1, rel=0.1)
        assert summary.get_quantile(0.95) == pytest.approx(94.05, rel=0.1)

    def test_metrics_registry(self):
        """Test metrics registry."""
        registry = MetricsRegistry()

        # Create metrics
        counter = registry.counter("test_counter", "Test counter")
        gauge = registry.gauge("test_gauge", "Test gauge")
        histogram = registry.histogram("test_histogram", "Test histogram")
        summary = registry.summary("test_summary", "Test summary")

        # Use metrics
        counter.inc()
        gauge.set(10)
        histogram.observe(5.0)
        summary.observe(3.0)

        # Retrieve metrics
        assert registry.get_counter("test_counter") is counter
        assert registry.get_gauge("test_gauge") is gauge
        assert registry.get_histogram("test_histogram") is histogram
        assert registry.get_summary("test_summary") is summary

        # Export metrics
        export = registry.export_metrics()
        assert "counters" in export
        assert "gauges" in export
        assert "histograms" in export
        assert "summaries" in export
        assert "test_counter" in export["counters"]
        assert "test_gauge" in export["gauges"]


class TestAlerts:
    """Test alert management."""

    def test_alert_rule_creation(self):
        """Test creating alert rules."""
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING
        )

        assert rule.name == "test_rule"
        assert rule.condition == "gt"
        assert rule.threshold == 10.0
        assert rule.enabled is True

    def test_alert_manager_add_remove_rule(self):
        """Test adding and removing alert rules."""
        manager = AlertManager()
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING
        )

        manager.add_rule(rule)
        assert "test_rule" in manager.rules

        manager.remove_rule("test_rule")
        assert "test_rule" not in manager.rules

    def test_evaluate_rule_condition_met(self):
        """Test evaluating rule when condition is met."""
        manager = AlertManager()
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING,
            duration_seconds=0  # Immediate trigger
        )

        manager.add_rule(rule)

        # Condition met
        alert = manager.evaluate_rule(rule, 15.0)
        assert alert is not None
        assert alert.rule_name == "test_rule"
        assert alert.severity == AlertSeverity.WARNING

    def test_evaluate_rule_condition_not_met(self):
        """Test evaluating rule when condition is not met."""
        manager = AlertManager()
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING
        )

        manager.add_rule(rule)

        # Condition not met
        alert = manager.evaluate_rule(rule, 5.0)
        assert alert is None

    def test_alert_cooldown(self):
        """Test alert cooldown period."""
        manager = AlertManager()
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING,
            cooldown_seconds=60,
            duration_seconds=0  # Immediate trigger for testing
        )

        manager.add_rule(rule)

        # First alert
        alert1 = manager.evaluate_rule(rule, 15.0)
        assert alert1 is not None

        # Immediate re-evaluation (should be in cooldown)
        alert2 = manager.evaluate_rule(rule, 15.0)
        assert alert2 is None  # In cooldown

    def test_alert_duration_requirement(self):
        """Test alert duration requirement."""
        manager = AlertManager()
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING,
            duration_seconds=2  # Must persist for 2 seconds
        )

        manager.add_rule(rule)

        # First evaluation (condition met but not long enough)
        alert1 = manager.evaluate_rule(rule, 15.0)
        assert alert1 is None  # Duration not met

        # Wait for duration
        time.sleep(2.1)

        # Second evaluation (duration met)
        alert2 = manager.evaluate_rule(rule, 15.0)
        assert alert2 is not None  # Duration met

    def test_alert_acknowledgement(self):
        """Test alert acknowledgement."""
        manager = AlertManager()
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING,
            duration_seconds=0
        )

        manager.add_rule(rule)
        alert = manager.evaluate_rule(rule, 15.0)
        assert alert is not None

        # Acknowledge alert
        manager.acknowledge_alert(alert.id, "test_user")
        acknowledged_alert = manager.active_alerts[alert.id]
        assert acknowledged_alert.status == AlertStatus.ACKNOWLEDGED
        assert acknowledged_alert.acknowledged_at is not None

    def test_alert_resolution(self):
        """Test alert resolution."""
        manager = AlertManager()
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING,
            duration_seconds=0
        )

        manager.add_rule(rule)
        alert = manager.evaluate_rule(rule, 15.0)
        alert_id = alert.id

        # Resolve alert
        manager.resolve_alert(alert_id)
        assert alert_id not in manager.active_alerts

        # Check history
        resolved_alert = [a for a in manager.alert_history if a.id == alert_id][0]
        assert resolved_alert.status == AlertStatus.RESOLVED
        assert resolved_alert.resolved_at is not None

    def test_log_notification(self):
        """Test log notification."""
        manager = AlertManager()

        # Add log notification
        notification = AlertNotification(
            name="log_notification",
            type="log",
            config={},
            min_severity=AlertSeverity.WARNING
        )
        manager.add_notification(notification)

        # Create and send alert
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING,
            duration_seconds=0
        )

        manager.add_rule(rule)
        alert = manager.evaluate_rule(rule, 15.0)

        # Send notification (should not raise exception)
        manager.send_alert(alert)

    def test_alert_stats(self):
        """Test alert statistics."""
        manager = AlertManager()

        # Create multiple alerts
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            metric_name="test_metric",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.WARNING,
            cooldown_seconds=0,  # No cooldown for testing
            duration_seconds=0    # Immediate trigger
        )

        manager.add_rule(rule)

        # Create 3 alerts and resolve them
        for i in range(3):
            # Use different values to avoid cooldown issues
            alert = manager.evaluate_rule(rule, 15.0 + float(i))
            assert alert is not None, f"Alert {i} should have been triggered"
            manager.resolve_alert(alert.id)

        stats = manager.get_alert_stats()
        assert stats["total_alerts"] == 3
        assert stats["active_alerts"] == 0
        assert stats["by_severity"]["warning"] == 3


class TestDashboard:
    """Test dashboard generation."""

    def test_add_time_series_point(self):
        """Test adding time series data points."""
        generator = DashboardGenerator()

        generator.add_time_series_point(
            "test_metric",
            10.0,
            description="Test metric",
            unit="requests"
        )

        assert "test_metric" in generator.time_series_data
        assert len(generator.time_series_data["test_metric"].data_points) == 1

    def test_time_series_aggregation(self):
        """Test time series aggregation."""
        generator = DashboardGenerator()

        # Add multiple points
        now = datetime.utcnow()
        for i in range(10):
            timestamp = now + timedelta(seconds=i * 10)
            generator.add_time_series_point(
                "test_metric",
                float(i),
                timestamp=timestamp
            )

        # Get aggregated series (5-second buckets)
        series = generator.get_time_series(
            "test_metric",
            bucket_size=timedelta(seconds=30),
            aggregation="avg"
        )

        # Should have fewer points due to aggregation
        assert len(series.data_points) <= 10
        assert series.aggregation == "avg"

    def test_dashboard_overview_data(self):
        """Test generating overview dashboard data."""
        generator = DashboardGenerator()

        # Add some data
        now = datetime.utcnow()
        for i in range(5):
            timestamp = now - timedelta(minutes=i)
            generator.add_time_series_point(
                "test_metric",
                float(i),
                timestamp=timestamp
            )

        dashboard_data = generator.generate_dashboard_data("overview")

        assert dashboard_data["dashboard_type"] == "overview"
        assert "time_series" in dashboard_data
        assert "stats" in dashboard_data
        assert "generated_at" in dashboard_data

    def test_dashboard_performance_data(self):
        """Test generating performance dashboard data."""
        generator = DashboardGenerator()

        # Add performance metrics
        generator.add_time_series_point("document_processing_duration", 0.5)
        generator.add_time_series_point("query_duration", 0.1)

        dashboard_data = generator.generate_dashboard_data("performance")

        assert dashboard_data["dashboard_type"] == "performance"
        assert "time_series" in dashboard_data

    def test_dashboard_templates(self):
        """Test dashboard templates."""
        generator = DashboardGenerator()

        dashboard_ids = generator.list_dashboards()
        assert "overview" in dashboard_ids
        assert "performance" in dashboard_ids
        assert "alerts" in dashboard_ids

        overview = generator.get_dashboard("overview")
        assert isinstance(overview, Dashboard)
        assert overview.id == "overview"
        assert len(overview.panels) > 0

    def test_export_dashboard_config(self):
        """Test exporting dashboard configuration."""
        generator = DashboardGenerator()

        config = generator.export_dashboard_config("overview")
        assert config is not None
        assert "dashboard" in config
        assert "panels" in config["dashboard"]

    def test_time_series_filtering(self):
        """Test time series time range filtering."""
        generator = DashboardGenerator()

        now = datetime.utcnow()
        # Add points at different times
        for hours_ago in [48, 24, 12, 6, 1]:
            timestamp = now - timedelta(hours=hours_ago)
            generator.add_time_series_point(
                "test_metric",
                float(hours_ago),
                timestamp=timestamp
            )

        # Get last 24 hours
        start_time = now - timedelta(hours=24)
        series = generator.get_time_series(
            "test_metric",
            start_time=start_time
        )

        # Should only have points from last 24 hours
        assert len(series.data_points) == 4  # 24, 12, 6, 1 hours ago


class TestIntegration:
    """Integration tests for monitoring system."""

    def test_end_to_end_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        # Setup
        logger = get_logger("integration_test")
        registry = MetricsRegistry()
        alert_manager = AlertManager()
        dashboard_gen = DashboardGenerator()

        # Create metrics
        doc_counter = registry.counter("documents_processed", "Documents processed")
        error_gauge = registry.gauge("errors_total", "Total errors")
        duration_histogram = registry.histogram(
            "processing_duration_seconds",
            "Processing duration"
        )

        # Create alert rule
        error_rule = AlertRule(
            name="high_error_rate",
            description="High error rate detected",
            metric_name="errors_total",
            condition="gt",
            threshold=10.0,
            severity=AlertSeverity.CRITICAL,
            duration_seconds=0
        )
        alert_manager.add_rule(error_rule)

        # Simulate activity
        with logger.context(operation="process_document"):
            logger.info("Processing document")

            doc_counter.inc()
            duration_histogram.observe(0.23)

            # Add error
            error_gauge.set(15)

            # Check for alert
            alert = alert_manager.evaluate_rule(error_rule, error_gauge.get())
            if alert:
                logger.warning(f"Alert triggered: {alert.message}")

            # Update dashboard
            dashboard_gen.add_time_series_point(
                "documents_processed",
                doc_counter.get()
            )
            dashboard_gen.add_time_series_point(
                "errors_total",
                error_gauge.get()
            )

        # Verify
        assert doc_counter.get() == 1.0
        assert error_gauge.get() == 15.0
        assert duration_histogram.get_count() == 1.0
        assert alert is not None

        # Generate dashboard
        dashboard_data = dashboard_gen.generate_dashboard_data("overview")
        assert "time_series" in dashboard_data

        # Export metrics
        metrics_export = registry.export_metrics()
        assert "documents_processed" in metrics_export["counters"]
        assert "errors_total" in metrics_export["gauges"]
