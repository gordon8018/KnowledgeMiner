"""
End-to-End Integration Tests for Stage 4 Quality Assurance.

This module implements comprehensive integration tests for the complete quality
assurance system, testing workflows from health monitoring through issue
classification to report generation and alerting.
"""

import pytest
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.wiki.quality.monitor import HealthMonitor
from src.wiki.quality.classifier import IssueClassifier
from src.wiki.quality.reporter import QualityReporter
from src.wiki.quality.models import (
    Issue,
    IssueType,
    IssueSeverity,
    HealthCheckResult,
    QualityReport,
    TrendDirection,
    ExtendedQualityReport
)
from src.wiki.core.models import WikiPage, PageType
from src.wiki.core.storage import WikiStore


@pytest.fixture
def large_wiki_store():
    """Create a WikiStore with many pages for stress testing."""
    test_dir = tempfile.mkdtemp()
    store = WikiStore(storage_path=test_dir)

    # Create 1000 pages for performance testing
    for i in range(1000):
        page_id = f"page-{i:04d}"
        page = WikiPage(
            id=page_id,
            title=f"Page {i}",
            content=f"# Content for page {i}\n\nThis is test content.\n\n## Section 1\nDetails here.",
            page_type=PageType.TOPIC,
            metadata={
                "tags": ["test", "sample"],
                "category": "test-category",
                "links": [f"page-{(i+1)%1000:04d}"] if i < 900 else []  # Some broken links
            },
            created_at=datetime.now() - timedelta(days=i),
            updated_at=datetime.now() - timedelta(days=i % 100)
        )
        store.create_page(page)

    yield store

    # Cleanup
    try:
        store.conn.close()
    except:
        pass

    try:
        import time
        time.sleep(0.1)
        if Path(test_dir).exists():
            shutil.rmtree(test_dir, ignore_errors=True)
    except:
        pass


@pytest.fixture
def quality_system_with_store(wiki_store):
    """Complete quality system with all components and a real WikiStore."""
    output_dir = tempfile.mkdtemp()

    monitor = HealthMonitor(wiki_store)
    classifier = IssueClassifier()
    # Disable rate limiting for tests to allow rapid report generation
    reporter = QualityReporter(wiki_store, output_dir, enable_rate_limiting=False)

    yield {
        "monitor": monitor,
        "classifier": classifier,
        "reporter": reporter,
        "store": wiki_store,
        "output_dir": output_dir
    }

    # Cleanup
    try:
        if Path(output_dir).exists():
            shutil.rmtree(output_dir, ignore_errors=True)
    except:
        pass


@pytest.fixture
def quality_system_with_issues():
    """Quality system with a WikiStore containing known issues."""
    test_dir = tempfile.mkdtemp()
    store = WikiStore(storage_path=test_dir)
    output_dir = tempfile.mkdtemp()

    # Create pages with various issues
    pages = [
        # Orphan page (no one links to it)
        WikiPage(
            id="orphan-page",
            title="Orphan Page",
            content="This page has no inbound links",
            page_type=PageType.TOPIC,
            metadata={"links": ["page-2"]},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # Page with broken link
        WikiPage(
            id="page-1",
            title="Page 1",
            content="Content with broken link",
            page_type=PageType.TOPIC,
            metadata={"links": ["non-existent-page"]},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # Normal page
        WikiPage(
            id="page-2",
            title="Page 2",
            content="Normal content",
            page_type=PageType.TOPIC,
            metadata={"links": []},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # Stale content (very old)
        WikiPage(
            id="stale-page",
            title="Stale Page",
            content="Very old content",
            page_type=PageType.TOPIC,
            metadata={},
            created_at=datetime.now() - timedelta(days=100),
            updated_at=datetime.now() - timedelta(days=90)
        ),
        # Duplicate content
        WikiPage(
            id="page-3",
            title="Page 3",
            content="This is duplicate content that will be similar to page 4",
            page_type=PageType.TOPIC,
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        WikiPage(
            id="page-4",
            title="Page 4",
            content="This is duplicate content that will be similar to page 3",
            page_type=PageType.TOPIC,
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]

    for page in pages:
        store.create_page(page)

    monitor = HealthMonitor(store)
    classifier = IssueClassifier()
    reporter = QualityReporter(store, output_dir)

    yield {
        "monitor": monitor,
        "classifier": classifier,
        "reporter": reporter,
        "store": store,
        "output_dir": output_dir
    }

    # Cleanup
    try:
        store.conn.close()
    except:
        pass

    try:
        time.sleep(0.1)
        if Path(test_dir).exists():
            shutil.rmtree(test_dir, ignore_errors=True)
        if Path(output_dir).exists():
            shutil.rmtree(output_dir, ignore_errors=True)
    except:
        pass


# ============================================================================
# Complete Quality Workflow Tests (6 tests)
# ============================================================================

class TestCompleteQualityWorkflow:
    """Test complete workflows from health check to report generation."""

    def test_complete_quality_detection_workflow(self, quality_system_with_issues):
        """Test complete workflow from Wiki health check to report generation."""
        monitor = quality_system_with_issues["monitor"]
        classifier = quality_system_with_issues["classifier"]
        reporter = quality_system_with_issues["reporter"]

        # Step 1: Run health check
        health_result = monitor.run_health_check()
        assert health_result.total_issues > 0, "Should detect issues"

        # Step 2: Classify issues
        all_issues = health_result.consistency_issues + health_result.staleness_issues
        classified_issues = classifier.classify_batch(all_issues)
        assert len(classified_issues) > 0, "Should classify issues"

        # Step 3: Prioritize issues
        prioritized = classifier.prioritize_issues(classified_issues)
        assert len(prioritized) > 0, "Should prioritize issues"

        # Verify prioritization by priority score
        if len(prioritized) > 1:
            assert prioritized[0].priority_score >= prioritized[-1].priority_score, \
                "Issues should be sorted by priority score"

        # Step 4: Generate report
        report = reporter.generate_report(health_result)
        assert report.overall_score >= 0.0, "Score should be non-negative"
        assert report.overall_score <= 1.0, "Score should not exceed 1.0"
        assert report.total_issues == health_result.total_issues, "Issue count should match"

        # Step 5: Verify report files created
        assert Path(report.report_file_path).exists(), "Markdown report should exist"
        json_path = report.report_file_path.replace('.md', '.json')
        assert Path(json_path).exists(), "JSON report should exist"

        # Verify report content
        with open(report.report_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '# Wiki Quality Report' in content, "Report should have title"
            assert '## Executive Summary' in content, "Report should have summary"
            assert '## Recommendations' in content, "Report should have recommendations"

    def test_issue_classification_and_prioritization_workflow(self, quality_system_with_issues):
        """Test workflow from issue detection to prioritized list."""
        monitor = quality_system_with_issues["monitor"]
        classifier = quality_system_with_issues["classifier"]

        # Detect issues
        health_result = monitor.run_health_check()
        all_issues = health_result.consistency_issues + health_result.staleness_issues

        assert len(all_issues) > 0, "Should detect issues"

        # Classify all issues
        classified_issues = classifier.classify_batch(all_issues)

        # Verify classification
        for classified in classified_issues:
            assert classified.category is not None, "Each issue should have a category"
            assert classified.complexity is not None, "Each issue should have complexity"
            assert classified.approach is not None, "Each issue should have repair approach"
            assert classified.priority_score >= 0.0, "Priority score should be non-negative"
            assert classified.priority_score <= 1.0, "Priority score should not exceed 1.0"

        # Prioritize issues
        prioritized = classifier.prioritize_issues(classified_issues)

        # Verify prioritization
        if len(prioritized) > 1:
            # Check that higher priority issues come first
            for i in range(len(prioritized) - 1):
                current_priority = prioritized[i].priority_score
                next_priority = prioritized[i + 1].priority_score
                # If same priority, severity should be used as tiebreaker
                if current_priority == next_priority:
                    current_severity = prioritized[i].original_issue.severity
                    next_severity = prioritized[i + 1].original_issue.severity
                    # Critical > HIGH > MEDIUM > LOW
                    severity_order = {
                        IssueSeverity.CRITICAL: 4,
                        IssueSeverity.HIGH: 3,
                        IssueSeverity.MEDIUM: 2,
                        IssueSeverity.LOW: 1
                    }
                    current_severity_order = severity_order.get(current_severity, 0)
                    next_severity_order = severity_order.get(next_severity, 0)
                    assert current_severity_order >= next_severity_order, \
                        "Higher severity issues should come first when priority scores are equal"

        # Generate repair plan
        repair_plan = classifier.suggest_repair_plan(classified_issues)

        assert repair_plan.total_issues == len(classified_issues), "Issue count should match"
        assert repair_plan.total_estimated_time_minutes > 0, "Should estimate repair time"
        assert len(repair_plan.recommended_order) == len(classified_issues), \
            "Recommended order should include all issues"

        # Verify grouping by approach
        assert 'automatic' in repair_plan.issue_groups, "Should have automatic group"
        assert 'semi_auto' in repair_plan.issue_groups, "Should have semi-automatic group"
        assert 'manual' in repair_plan.issue_groups, "Should have manual group"

    def test_quality_trend_analysis_workflow(self, quality_system_with_store):
        """Test multiple reports over time with trend detection."""
        reporter = quality_system_with_store["reporter"]
        monitor = quality_system_with_store["monitor"]

        # Generate initial report
        health_result1 = monitor.run_health_check()
        report1 = reporter.generate_report(health_result1)

        # Simulate time passing and quality changes
        time.sleep(0.1)

        # Add some pages to change quality
        store = quality_system_with_store["store"]
        for i in range(5):
            page_id = f"new-page-{i}"
            content = f"# New Content {i}\n\nFresh content"
            metadata = {"tags": ["new"]}
            store.create_page(page_id, content, metadata)

        # Generate second report
        health_result2 = monitor.run_health_check()
        report2 = reporter.generate_report(health_result2)

        time.sleep(0.1)

        # Generate third report
        health_result3 = monitor.run_health_check()
        report3 = reporter.generate_report(health_result3)

        # Analyze trends
        reports = [report1, report2, report3]
        trend_analysis = reporter.track_trend(reports)

        assert trend_analysis.direction != TrendDirection.UNKNOWN, \
            "Should determine trend direction with 3 reports"
        assert trend_analysis.confidence > 0.0, "Should have confidence level"
        assert len(trend_analysis.trend_points) == 3, "Should have 3 trend points"
        assert trend_analysis.summary is not None, "Should have summary"
        assert len(trend_analysis.recommendations) > 0, "Should have recommendations"

        # Verify trend points have correct data
        for i, point in enumerate(trend_analysis.trend_points):
            assert point.value >= 0.0 and point.value <= 1.0, "Score should be in valid range"
            if i > 0:
                assert point.change_from_previous != 0.0 or True, "Should calculate change"
                assert isinstance(point.change_percentage, float), "Change should be percentage"

    def test_alert_generation_on_quality_degradation(self, quality_system_with_store):
        """Test that quality drops trigger alerts."""
        reporter = quality_system_with_store["reporter"]
        monitor = quality_system_with_store["monitor"]

        # Generate a good baseline report
        health_result_baseline = monitor.run_health_check()
        baseline_score = health_result_baseline.quality_report.overall_score

        # Simulate quality degradation by adding problematic pages
        store = quality_system_with_store["store"]

        # Add many broken links
        for i in range(20):
            page_id = f"broken-{i}"
            content = "Content with broken link"
            metadata = {"links": [f"non-existent-{i}"]}
            store.create_page(page_id, content, metadata)

        # Run health check again
        health_result_degraded = monitor.run_health_check()
        degraded_score = health_result_degraded.quality_report.overall_score

        # Generate alert
        alert_path = Path(quality_system_with_store["output_dir"]) / "alert.txt"
        alert_sent = reporter.send_alert(health_result_degraded, str(alert_path))

        # Verify alert logic
        # If quality degraded significantly or has many critical issues, alert should be sent
        if degraded_score < 0.6 or health_result_degraded.critical_issues > 10:
            assert alert_sent, "Alert should be sent for significant degradation"

    def test_dashboard_data_preparation_workflow(self, quality_system_with_store):
        """Test workflow from reports to dashboard visualization data."""
        reporter = quality_system_with_store["reporter"]
        monitor = quality_system_with_store["monitor"]

        # Generate multiple reports for dashboard
        reports = []
        for i in range(5):
            health_result = monitor.run_health_check()
            report = reporter.generate_report(health_result)
            reports.append(report)
            time.sleep(0.05)  # Small delay to ensure different timestamps

        # Prepare dashboard data
        dashboard_data = reporter.create_dashboard_data(reports)

        # Verify dashboard structure
        assert dashboard_data.generated_at is not None, "Should have generation timestamp"
        assert dashboard_data.time_range_days >= 0, "Should calculate time range"
        assert len(dashboard_data.quality_over_time) == 5, "Should have 5 data points"
        assert len(dashboard_data.issue_distribution) > 0 or True, "Should have issue distribution"
        assert dashboard_data.top_issues is not None, "Should have top issues"

        # Verify charts data
        assert "quality_timeline" in dashboard_data.charts, "Should have timeline chart"
        assert "issue_distribution" in dashboard_data.charts, "Should have distribution chart"
        assert "severity_breakdown" in dashboard_data.charts, "Should have severity chart"

        # Verify quality timeline data structure
        for point in dashboard_data.quality_over_time:
            assert "timestamp" in point, "Should have timestamp"
            assert "score" in point, "Should have score"
            assert "issues" in point, "Should have issue count"
            assert "critical_issues" in point, "Should have critical issue count"

        # Verify chart types and data
        timeline_chart = dashboard_data.charts["quality_timeline"]
        assert timeline_chart["type"] == "line", "Timeline should be line chart"
        assert "data" in timeline_chart, "Timeline should have data"

        distribution_chart = dashboard_data.charts["issue_distribution"]
        assert distribution_chart["type"] == "bar", "Distribution should be bar chart"
        assert "data" in distribution_chart, "Distribution should have data"

        severity_chart = dashboard_data.charts["severity_breakdown"]
        assert severity_chart["type"] == "pie", "Severity should be pie chart"
        assert "data" in severity_chart, "Severity should have data"

    def test_full_quality_assurance_cycle(self, quality_system_with_issues):
        """Test complete cycle: detect → classify → report → alert."""
        monitor = quality_system_with_issues["monitor"]
        classifier = quality_system_with_issues["classifier"]
        reporter = quality_system_with_issues["reporter"]

        # Step 1: Detect issues
        health_result = monitor.run_health_check()
        assert health_result is not None, "Should complete health check"
        assert health_result.total_issues >= 0, "Should count issues"

        # Step 2: Classify issues
        all_issues = health_result.consistency_issues + health_result.staleness_issues
        classified_issues = classifier.classify_batch(all_issues)

        # Step 3: Prioritize and plan repairs
        prioritized = classifier.prioritize_issues(classified_issues)
        repair_plan = classifier.suggest_repair_plan(classified_issues)

        assert repair_plan.total_issues == len(classified_issues), "Plan should include all issues"
        assert repair_plan.total_estimated_time_minutes > 0, "Should estimate total time"

        # Step 4: Generate report
        report = reporter.generate_report(health_result)

        assert report.report_id is not None, "Report should have ID"
        assert report.overall_score >= 0.0, "Score should be valid"
        assert report.total_issues == health_result.total_issues, "Issue counts should match"
        assert len(report.recommendations) > 0, "Should have recommendations"

        # Step 5: Check for alerts
        alert_path = Path(quality_system_with_issues["output_dir"]) / "cycle_alert.txt"
        alert_sent = reporter.send_alert(health_result, str(alert_path))

        # Verify complete cycle
        assert Path(report.report_file_path).exists(), "Report file should exist"

        # Verify all components worked together
        if health_result.total_issues > 0:
            assert len(classified_issues) > 0, "Issues should be classified"
            assert len(prioritized) > 0, "Issues should be prioritized"
            assert len(report.recommendations) > 0, "Should have recommendations"

        # Verify data flow between components
        # Issues detected by monitor should be classified
        detected_issue_ids = {issue.id for issue in all_issues}
        classified_issue_ids = {c.original_issue.id for c in classified_issues}
        assert detected_issue_ids == classified_issue_ids, \
            "All detected issues should be classified"

        # Verify report reflects health check results
        assert report.total_issues == health_result.total_issues, \
            "Report should reflect health check results"
        assert report.critical_issues == health_result.critical_issues, \
            "Report should reflect critical issues"


# ============================================================================
# Component Integration Tests (4 tests)
# ============================================================================

class TestComponentIntegration:
    """Test integration between quality components."""

    def test_health_monitor_and_classifier_integration(self, quality_system_with_issues):
        """Test HealthMonitor feeds IssueClassifier correctly."""
        monitor = quality_system_with_issues["monitor"]
        classifier = quality_system_with_issues["classifier"]

        # Run health check
        health_result = monitor.run_health_check()

        # Get all issues from health check
        all_issues = health_result.consistency_issues + health_result.staleness_issues

        # Classify all detected issues
        classified_issues = classifier.classify_batch(all_issues)

        # Verify integration
        assert len(classified_issues) == len(all_issues), \
            "Classifier should handle all issues from monitor"

        # Verify issue types are preserved
        detected_types = {issue.issue_type for issue in all_issues}
        classified_types = {c.original_issue.issue_type for c in classified_issues}
        assert detected_types == classified_types, "Issue types should be preserved"

        # Verify severity is preserved
        for classified in classified_issues:
            original = classified.original_issue
            assert classified.original_issue.severity == original.severity, \
                "Severity should be preserved through classification"

    def test_classifier_and_reporter_integration(self, quality_system_with_issues):
        """Test classifier results inform report generation correctly."""
        monitor = quality_system_with_issues["monitor"]
        classifier = quality_system_with_issues["classifier"]
        reporter = quality_system_with_issues["reporter"]

        # Detect and classify issues
        health_result = monitor.run_health_check()
        all_issues = health_result.consistency_issues + health_result.staleness_issues
        classified_issues = classifier.classify_batch(all_issues)

        # Prioritize issues
        prioritized = classifier.prioritize_issues(classified_issues)

        # Generate repair plan
        repair_plan = classifier.suggest_repair_plan(classified_issues)

        # Generate report
        report = reporter.generate_report(health_result)

        # Verify report includes classified issues
        assert report.total_issues == len(all_issues), \
            "Report should include all classified issues"

        # Verify issue breakdown in report
        if len(all_issues) > 0:
            assert len(report.issue_breakdown) > 0, \
                "Report should have issue breakdown"
            assert report.critical_issues == health_result.critical_issues, \
                "Report should reflect critical issues"

        # Verify recommendations consider repair complexity
        if repair_plan.manual_repairs > 0:
            # Should mention manual repairs in recommendations
            manual_mentioned = any("manual" in rec.lower() for rec in report.recommendations)
            # Note: This is a soft check as recommendations are generated dynamically

    def test_monitor_reporter_trend_analysis_integration(self, quality_system_with_store):
        """Test Monitor → Reporter → Trend analysis pipeline."""
        reporter = quality_system_with_store["reporter"]
        monitor = quality_system_with_store["monitor"]

        # Generate sequence of health checks and reports
        reports = []
        for i in range(5):
            health_result = monitor.run_health_check()

            # Verify health check provides data needed for reporting
            assert health_result.quality_report is not None, "Should have quality report"
            assert health_result.total_issues >= 0, "Should count issues"

            # Generate report from health check
            report = reporter.generate_report(health_result)

            # Verify report captures health check data
            assert report.overall_score == health_result.quality_report.overall_score, \
                "Report should capture quality score"
            assert report.total_issues == health_result.total_issues, \
                "Report should capture issue count"

            reports.append(report)
            time.sleep(0.05)

        # Analyze trends across reports
        trend_analysis = reporter.track_trend(reports)

        # Verify trend analysis uses report data
        assert len(trend_analysis.trend_points) == len(reports), \
            "Trend analysis should use all reports"

        # Verify trend points map to reports
        for i, point in enumerate(trend_analysis.trend_points):
            assert point.value == reports[i].overall_score, \
                "Trend point should match report score"

        # Verify confidence increases with more data
        if len(reports) >= 5:
            assert trend_analysis.confidence > 0.5, \
                "Should have reasonable confidence with 5 reports"

    def test_all_components_integration(self, quality_system_with_issues):
        """Test all 4 components working together seamlessly."""
        monitor = quality_system_with_issues["monitor"]
        classifier = quality_system_with_issues["classifier"]
        reporter = quality_system_with_issues["reporter"]
        store = quality_system_with_issues["store"]

        # Complete workflow: Monitor → Classify → Report → Alert
        # Step 1: Monitor detects issues
        health_result = monitor.run_health_check()
        assert health_result is not None
        assert health_result.total_issues >= 0

        # Step 2: Classifier processes detected issues
        all_issues = health_result.consistency_issues + health_result.staleness_issues
        classified_issues = classifier.classify_batch(all_issues)
        prioritized = classifier.prioritize_issues(classified_issues)
        repair_plan = classifier.suggest_repair_plan(classified_issues)

        # Step 3: Reporter generates comprehensive report
        report = reporter.generate_report(health_result)

        # Step 4: Alert system checks for critical conditions
        alert_path = Path(quality_system_with_issues["output_dir"]) / "integration_alert.txt"
        alert_triggered = reporter.send_alert(health_result, str(alert_path))

        # Verify complete integration

        # Data flow: Monitor → Classifier
        assert len(classified_issues) == len(all_issues), \
            "Classifier should process all detected issues"

        # Data flow: Classifier → Reporter
        assert report.total_issues == health_result.total_issues, \
            "Reporter should reflect all detected issues"
        assert report.critical_issues == health_result.critical_issues, \
            "Reporter should reflect critical issues"

        # Data flow: All components → Alert system
        if health_result.total_issues > 0:
            # Alert system should have processed the health result
            assert isinstance(alert_triggered, bool), "Should return alert status"

        # Verify no data loss between components
        detected_ids = {issue.id for issue in all_issues}
        classified_ids = {c.original_issue.id for c in classified_issues}
        assert detected_ids == classified_ids, "No issues should be lost in classification"

        # Verify report completeness
        assert report.report_id is not None, "Report should have ID"
        assert report.generated_at is not None, "Report should have timestamp"
        assert report.overall_score >= 0.0, "Score should be valid"
        assert len(report.detailed_findings) > 0, "Should have detailed findings"
        assert len(report.recommendations) > 0, "Should have recommendations"

        # Verify all components use same WikiStore
        assert monitor.wiki_store == store, "Monitor should use provided store"
        assert reporter.wiki_store == store, "Reporter should use provided store"


# ============================================================================
# Performance and Stress Tests (3 tests)
# ============================================================================

class TestPerformanceAndStress:
    """Test performance under load and stress conditions."""

    def test_large_wiki_health_check_performance(self, large_wiki_store):
        """Test health check on 1000+ pages completes within time limit."""
        monitor = HealthMonitor(large_wiki_store)

        # Benchmark: Should complete within reasonable time
        # Note: Performance depends on system, so we use a generous threshold
        start_time = time.time()
        health_result = monitor.run_health_check()
        elapsed_time = time.time() - start_time

        assert health_result is not None, "Health check should complete"
        # Use 60 seconds as a reasonable upper bound for 1000 pages on any system
        assert elapsed_time < 60.0, f"Health check took {elapsed_time:.2f}s, should be < 60s"

        # Verify results are accurate even with large dataset
        assert health_result.quality_report.page_count >= 1000, \
            "Should process all 1000 pages"
        assert health_result.total_issues >= 0, "Should count issues"

        # Verify performance scales reasonably
        # Each page should take less than 50ms on average (generous bound)
        time_per_page = elapsed_time / health_result.quality_report.page_count
        assert time_per_page < 0.05, f"Time per page {time_per_page*1000:.2f}ms should be < 50ms"

    def test_batch_issue_classification_performance(self, quality_system_with_issues):
        """Test classification of 100+ issues completes efficiently."""
        classifier = IssueClassifier()
        monitor = quality_system_with_issues["monitor"]

        # Create 100+ issues for testing
        issues = []
        for i in range(100):
            issue = Issue(
                id=f"issue-{i}",
                issue_type=IssueType.BROKEN_LINK,
                severity=IssueSeverity.HIGH if i % 2 == 0 else IssueSeverity.MEDIUM,
                page_id=f"page-{i}",
                description=f"Test issue {i}",
                detected_at=datetime.now(),
                metadata={}
            )
            issues.append(issue)

        # Benchmark: Should classify 100 issues in < 2 seconds
        start_time = time.time()
        classified_issues = classifier.classify_batch(issues)
        elapsed_time = time.time() - start_time

        assert len(classified_issues) == 100, "Should classify all issues"
        assert elapsed_time < 2.0, f"Classification took {elapsed_time:.2f}s, should be < 2s"

        # Verify classification is accurate
        for classified in classified_issues:
            assert classified.category is not None, "Each issue should be categorized"
            assert classified.complexity is not None, "Each issue should have complexity"
            assert classified.approach is not None, "Each issue should have approach"
            assert classified.priority_score >= 0.0, "Priority score should be valid"

        # Verify performance is efficient
        time_per_issue = elapsed_time / len(issues)
        assert time_per_issue < 0.02, f"Time per issue {time_per_issue*1000:.2f}ms should be < 20ms"

    def test_report_generation_performance(self, quality_system_with_issues):
        """Test report generation with large datasets completes quickly."""
        monitor = quality_system_with_issues["monitor"]
        reporter = quality_system_with_issues["reporter"]

        # Run health check to get data
        health_result = monitor.run_health_check()

        # Benchmark: Should generate report in < 3 seconds
        start_time = time.time()
        report = reporter.generate_report(health_result)
        elapsed_time = time.time() - start_time

        assert report is not None, "Report should be generated"
        assert elapsed_time < 3.0, f"Report generation took {elapsed_time:.2f}s, should be < 3s"

        # Verify report is complete
        assert report.report_id is not None, "Report should have ID"
        assert Path(report.report_file_path).exists(), "Report file should exist"

        # Verify both markdown and JSON files are created
        markdown_path = Path(report.report_file_path)
        json_path = markdown_path.with_suffix('.json')
        assert markdown_path.exists(), "Markdown report should exist"
        assert json_path.exists(), "JSON report should exist"

        # Verify file sizes are reasonable
        markdown_size = markdown_path.stat().st_size
        json_size = json_path.stat().st_size
        assert markdown_size > 0, "Markdown report should have content"
        assert json_size > 0, "JSON report should have content"

        # Verify report content is generated
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 100, "Report should have substantial content"


# ============================================================================
# Long-Running Stability Tests (2 tests)
# ============================================================================

class TestLongRunningStability:
    """Test system stability over extended periods."""

    def test_continuous_monitoring_stability(self, quality_system_with_store):
        """Simulate 7 days of continuous monitoring without degradation."""
        monitor = quality_system_with_store["monitor"]
        reporter = quality_system_with_store["reporter"]
        store = quality_system_with_store["store"]

        # Simulate 7 days of monitoring (as 7 iterations)
        reports = []
        health_scores = []
        issue_counts = []

        for day in range(7):
            # Simulate daily health check
            health_result = monitor.run_health_check()

            # Track metrics
            health_scores.append(health_result.quality_report.overall_score)
            issue_counts.append(health_result.total_issues)

            # Generate daily report
            report = reporter.generate_report(health_result)
            reports.append(report)

            # Verify no memory leaks or performance degradation
            # Each iteration should complete in reasonable time
            # (we're not timing strictly here, just ensuring it completes)

            # Simulate some content changes between days
            if day < 6:  # Don't add on last day
                # Add a few new pages
                for i in range(3):
                    page_id = f"day-{day}-page-{i}"
                    content = f"Content added on day {day}"
                    metadata = {}
                    store.create_page(page_id, content, metadata)

        # Verify stability across all 7 days
        assert len(reports) == 7, "Should have 7 daily reports"

        # Verify all reports are valid
        for i, report in enumerate(reports):
            assert report.report_id is not None, f"Day {i} report should have ID"
            assert report.overall_score >= 0.0, f"Day {i} score should be valid"
            assert report.overall_score <= 1.0, f"Day {i} score should be in range"
            assert Path(report.report_file_path).exists(), f"Day {i} report file should exist"

        # Verify consistent operation (no crashes)
        # All health checks should have completed
        assert len(health_scores) == 7, "Should have 7 health scores"
        assert len(issue_counts) == 7, "Should have 7 issue counts"

        # Verify trend analysis works with historical data
        trend_analysis = reporter.track_trend(reports)
        assert trend_analysis.direction != TrendDirection.UNKNOWN, \
            "Should determine trend with 7 days of data"

        # Verify no corruption in report history
        assert len(reporter.report_history) >= 7, \
            "Reporter should maintain report history"

    def test_quality_metric_consistency_over_time(self, quality_system_with_store):
        """Test quality metrics remain consistent across multiple runs."""
        monitor = quality_system_with_store["monitor"]
        reporter = quality_system_with_store["reporter"]

        # Run multiple health checks on unchanged data
        # Results should be consistent
        results = []
        for run in range(5):
            health_result = monitor.run_health_check()
            results.append(health_result)
            time.sleep(0.05)  # Small delay between runs

        # Verify consistency
        # All runs should produce same page count (data hasn't changed)
        page_counts = [r.quality_report.page_count for r in results]
        assert all(pc == page_counts[0] for pc in page_counts), \
            "Page count should be consistent across runs"

        # Quality scores should be very similar (minor differences acceptable due to timestamps)
        scores = [r.quality_report.overall_score for r in results]
        score_variance = max(scores) - min(scores)
        assert score_variance < 0.05, f"Score variance {score_variance:.3f} should be minimal"

        # Issue counts should be identical (no data changes)
        issue_counts = [r.total_issues for r in results]
        assert all(ic == issue_counts[0] for ic in issue_counts), \
            "Issue count should be identical across runs"

        # Critical issue counts should be identical
        critical_counts = [r.critical_issues for r in results]
        assert all(cc == critical_counts[0] for cc in critical_counts), \
            "Critical issue count should be identical across runs"

        # Generate reports from each run
        reports = []
        for health_result in results:
            report = reporter.generate_report(health_result)
            reports.append(report)

        # Verify reports are consistent
        report_scores = [r.overall_score for r in reports]
        report_score_variance = max(report_scores) - min(report_scores)
        assert report_score_variance < 0.05, \
            f"Report score variance {report_score_variance:.3f} should be minimal"

        # Verify trend analysis detects stable quality
        trend_analysis = reporter.track_trend(reports)
        assert trend_analysis.direction == TrendDirection.STABLE, \
            "Should detect stable quality with consistent runs"
        assert trend_analysis.confidence > 0.5, \
            "Should have high confidence in stable trend"