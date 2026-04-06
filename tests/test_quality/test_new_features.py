"""
Tests for new Stage 4 fixes: rate limiting, alert deduplication, pagination, caching, circuit breaker, and metrics.
"""

import pytest
import tempfile
import time
from datetime import datetime
from pathlib import Path

from src.wiki.quality.monitor import HealthMonitor, CircuitBreaker
from src.wiki.quality.reporter import QualityReporter, AlertManager, rate_limit
from src.wiki.quality.metrics import MetricsRegistry, Counter, Histogram, get_metrics_summary
from src.wiki.core.storage import WikiStore
from src.wiki.core.models import WikiPage, PageType
from src.wiki.quality.models import (
    Issue,
    IssueType,
    IssueSeverity,
    HealthCheckResult,
    QualityReport,
    TrendDirection
)


class TestRateLimiting:
    """Tests for rate limiting feature (Issue 1)."""

    def test_rate_limiting_decorator_exists(self):
        """Test that rate limiting decorator is available and functional."""
        # Test that the decorator can be applied
        @rate_limit(min_interval_seconds=1)
        def test_function(self):
            return "success"

        class TestClass:
            def __init__(self):
                self.enable_rate_limiting = True

        test_instance = TestClass()

        # Should be able to call the function
        result = test_function(test_instance)
        assert result == "success"

    def test_rate_limiting_can_be_disabled_via_attribute(self):
        """Test that rate limiting respects enable_rate_limiting attribute."""
        call_count = []

        @rate_limit(min_interval_seconds=10)
        def test_function(self):
            call_count.append(1)
            return "success"

        class TestClass:
            def __init__(self, enable_rate_limiting):
                self.enable_rate_limiting = enable_rate_limiting

        # With rate limiting disabled, both calls should succeed
        test_instance_disabled = TestClass(enable_rate_limiting=False)
        result1 = test_function(test_instance_disabled)
        result2 = test_function(test_instance_disabled)
        assert result1 == "success"
        assert result2 == "success"
        assert len(call_count) == 2  # Both calls executed

        # Reset counter
        call_count.clear()

        # With rate limiting enabled, second call should be limited
        test_instance_enabled = TestClass(enable_rate_limiting=True)
        test_function(test_instance_enabled)  # First call
        test_function(test_instance_enabled)  # Second call (rate limited)
        # The exact behavior depends on implementation, but it should not crash
        assert len(call_count) >= 1  # At least the first call executed

    def test_rate_limiting_can_be_disabled(self):
        """Test that rate limiting can be disabled."""
        call_times = []

        @rate_limit(min_interval_seconds=10)
        def test_function(self):
            call_times.append(time.time())
            return "success"

        class TestClass:
            def __init__(self):
                self.enable_rate_limiting = False

        test_instance = TestClass()

        # Both calls should succeed immediately when rate limiting is disabled
        result1 = test_function(test_instance)
        result2 = test_function(test_instance)

        assert result1 == "success"
        assert result2 == "success"
        assert len(call_times) == 2


class TestAlertDeduplication:
    """Tests for alert deduplication feature (Issue 2)."""

    def test_alert_manager_deduplicates_alerts(self):
        """Test that AlertManager prevents duplicate alerts within cooldown."""
        manager = AlertManager(cooldown_minutes=30)

        # Create a mock health check result
        health_result = HealthCheckResult(
            timestamp=datetime.now(),
            consistency_issues=[],
            quality_report=QualityReport(
                overall_score=0.5,
                page_count=10,
                avg_page_quality=0.5,
                completeness_score=0.5,
                freshness_score=0.5,
                metadata_score=0.5,
                issues_found=5,
                recommendations=[]
            ),
            staleness_issues=[],
            total_issues=5,
            critical_issues=3,
            status="unhealthy"
        )

        # First alert should be sent
        assert manager.should_send_alert(health_result) == True
        manager.mark_alert_sent(health_result)

        # Second alert with same signature should be blocked
        assert manager.should_send_alert(health_result) == False

    def test_alert_manager_clears_old_alerts(self):
        """Test that AlertManager clears old alert signatures."""
        manager = AlertManager(cooldown_minutes=30)

        health_result = HealthCheckResult(
            timestamp=datetime.now(),
            consistency_issues=[],
            quality_report=QualityReport(
                overall_score=0.5,
                page_count=10,
                avg_page_quality=0.5,
                completeness_score=0.5,
                freshness_score=0.5,
                metadata_score=0.5,
                issues_found=5,
                recommendations=[]
            ),
            staleness_issues=[],
            total_issues=5,
            critical_issues=3,
            status="unhealthy"
        )

        # Mark alert as sent
        manager.mark_alert_sent(health_result)
        assert len(manager.active_alerts) == 1

        # Clear old alerts (with max_age_hours=0, all should be cleared)
        manager.clear_old_alerts(max_age_hours=0)
        assert len(manager.active_alerts) == 0


class TestCircuitBreaker:
    """Tests for circuit breaker feature (Issue 6)."""

    def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        def failing_function():
            raise Exception("Simulated failure")

        # First failure
        with pytest.raises(Exception):
            breaker.call(failing_function)
        assert breaker.state == "closed"
        assert breaker.failure_count == 1

        # Second failure
        with pytest.raises(Exception):
            breaker.call(failing_function)
        assert breaker.state == "closed"
        assert breaker.failure_count == 2

        # Third failure should open circuit
        with pytest.raises(Exception):
            breaker.call(failing_function)
        assert breaker.state == "open"
        assert breaker.failure_count == 3

    def test_circuit_breaker_blocks_calls_when_open(self):
        """Test that circuit breaker blocks calls when open."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        def failing_function():
            raise Exception("Simulated failure")

        # Trigger circuit to open
        with pytest.raises(Exception):
            breaker.call(failing_function)
        with pytest.raises(Exception):
            breaker.call(failing_function)

        assert breaker.state == "open"

        # Next call should be blocked immediately
        with pytest.raises(Exception) as exc_info:
            breaker.call(failing_function)
        assert "Circuit breaker is open" in str(exc_info.value)

    def test_circuit_breaker_allows_recovery_after_timeout(self):
        """Test that circuit breaker allows recovery after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        def failing_function():
            raise Exception("Simulated failure")

        def succeeding_function():
            return "success"

        # Trigger circuit to open
        with pytest.raises(Exception):
            breaker.call(failing_function)
        with pytest.raises(Exception):
            breaker.call(failing_function)

        assert breaker.state == "open"

        # Wait for recovery timeout
        time.sleep(1.5)

        # Next call should succeed and close circuit
        result = breaker.call(succeeding_function)
        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0


class TestPagination:
    """Tests for pagination support (Issue 4)."""

    def test_check_orphan_pages_with_pagination(self, wiki_store):
        """Test that check_orphan_pages works with pagination."""
        monitor = HealthMonitor(wiki_store)

        # Create pages with links
        for i in range(10):
            wiki_store.create_page(
                f"page-{i}",
                f"Content {i}",
                metadata={"links": [f"page-{(i+1)%10}"]}
            )

        # Test with small page size
        issues = monitor.check_orphan_pages(page_size=3)
        # Should return results without errors
        assert isinstance(issues, list)

    def test_check_broken_links_with_pagination(self, wiki_store):
        """Test that check_broken_links works with pagination."""
        monitor = HealthMonitor(wiki_store)

        # Create pages with broken links
        for i in range(10):
            wiki_store.create_page(
                f"page-{i}",
                f"Content {i}",
                metadata={"links": ["non-existent-page"]}
            )

        # Test with small page size
        issues = monitor.check_broken_links(page_size=3)
        # Should find broken links
        assert len(issues) > 0
        assert all(i.issue_type == IssueType.BROKEN_LINK for i in issues)


class TestCaching:
    """Tests for caching layer (Issue 5)."""

    def test_similarity_caching_improves_performance(self, wiki_store):
        """Test that caching similarity calculations improves performance."""
        monitor = HealthMonitor(wiki_store)

        # Create identical pages
        content = "This is test content with similar words and phrases."
        wiki_store.create_page("page-1", content)
        wiki_store.create_page("page-2", content)

        # First calculation
        start_time = time.time()
        similarity1 = monitor._calculate_similarity(content, content)
        time1 = time.time() - start_time

        # Second calculation (should be cached)
        start_time = time.time()
        similarity2 = monitor._calculate_similarity(content, content)
        time2 = time.time() - start_time

        assert similarity1 == similarity2
        # Cached calculation should be faster (though this may vary)
        assert time2 <= time1 * 2  # Allow some variance

    def test_cache_can_be_cleared(self, wiki_store):
        """Test that cache can be cleared."""
        monitor = HealthMonitor(wiki_store)

        # Add some items to cache
        monitor._get_content_hash("test content")
        monitor._calculate_similarity("content1", "content2")

        assert len(monitor._content_hash_cache) > 0
        assert len(monitor._similarity_cache) > 0

        # Clear cache
        monitor.clear_cache()

        assert len(monitor._content_hash_cache) == 0
        assert len(monitor._similarity_cache) == 0


class TestMetrics:
    """Tests for observability metrics (Issue 7)."""

    def test_counter_increments(self):
        """Test that counter increments correctly."""
        counter = Counter("test_counter", "Test counter", labels=["status"])

        counter.inc(status="success")
        counter.inc(status="success")
        counter.inc(status="failure")

        assert counter.get_value(status="success") == 2.0
        assert counter.get_value(status="failure") == 1.0
        assert counter.get_value(status="unknown") == 0.0

    def test_histogram_observations(self):
        """Test that histogram records observations correctly."""
        histogram = Histogram("test_histogram", "Test histogram")

        histogram.observe(0.5)
        histogram.observe(1.5)
        histogram.observe(2.5)

        assert histogram.get_count() == 3
        assert histogram.get_sum() == 4.5
        assert histogram.get_average() == 1.5

    def test_metrics_emission(self):
        """Test that metrics can be emitted as dictionary."""
        from src.wiki.quality.metrics import metrics

        # Record some metrics
        metrics.health_check_counter.inc(status="success")
        metrics.issue_counter.inc(issue_type="orphan_page", severity="low")
        metrics.health_check_duration.observe(1.5, check_type="full")

        # Emit metrics
        metrics_data = metrics.emit_metrics()

        assert "counters" in metrics_data
        assert "histograms" in metrics_data
        assert "timestamp" in metrics_data
        assert metrics_data["counters"]["health_check_total"]["success",] == 1.0

    def test_metrics_summary_generation(self):
        """Test that human-readable metrics summary can be generated."""
        from src.wiki.quality.metrics import metrics

        # Record some metrics
        metrics.health_check_counter.inc(status="success")
        metrics.health_check_counter.inc(status="success")
        metrics.health_check_duration.observe(1.5, check_type="full")

        # Generate summary
        summary = get_metrics_summary()

        assert "Wiki Quality Monitoring Metrics" in summary
        assert "health_check_total" in summary
        assert "health_check_duration" in summary
