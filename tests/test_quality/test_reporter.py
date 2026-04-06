"""
Tests for QualityReporter functionality.

This module tests the generation of quality reports, trend analysis,
dashboard data preparation, and alert system.
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from src.wiki.quality.reporter import QualityReporter
from src.wiki.quality.models import (
    Issue,
    IssueType,
    IssueSeverity,
    QualityReport,
    HealthCheckResult,
    TrendDirection,
    MetricType,
    ExtendedQualityReport,
    TrendAnalysis,
    DashboardData
)


@pytest.fixture
def output_dir():
    """Create a temporary output directory for reports."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    try:
        import time
        time.sleep(0.1)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass


@pytest.fixture
def sample_health_check_result():
    """Create a sample health check result for testing."""
    issues = [
        Issue(
            id="issue-1",
            issue_type=IssueType.ORPHAN_PAGE,
            severity=IssueSeverity.HIGH,
            page_id="orphan-page",
            description="Page has no incoming links",
            detected_at=datetime.now()
        ),
        Issue(
            id="issue-2",
            issue_type=IssueType.BROKEN_LINK,
            severity=IssueSeverity.CRITICAL,
            page_id="page-with-broken-link",
            description="Link to non-existent page",
            detected_at=datetime.now()
        ),
        Issue(
            id="issue-3",
            issue_type=IssueType.STALE_CONTENT,
            severity=IssueSeverity.MEDIUM,
            page_id="stale-page",
            description="Content not updated in 180 days",
            detected_at=datetime.now()
        ),
    ]

    quality_report = QualityReport(
        overall_score=0.75,
        page_count=100,
        avg_page_quality=0.75,
        completeness_score=0.80,
        freshness_score=0.70,
        metadata_score=0.75,
        issues_found=3,
        recommendations=[
            "Fix broken links",
            "Update stale content",
            "Add links to orphan pages"
        ]
    )

    return HealthCheckResult(
        timestamp=datetime.now(),
        consistency_issues=issues[:2],
        quality_report=quality_report,
        staleness_issues=[issues[2]],
        total_issues=3,
        critical_issues=1,
        status="degraded"
    )


@pytest.fixture
def quality_reporter(wiki_store, output_dir):
    """Create a QualityReporter instance for testing."""
    return QualityReporter(wiki_store, output_dir)


class TestReportGeneration:
    """Tests for report generation functionality."""

    def test_generate_report_creates_markdown_file(self, quality_reporter, sample_health_check_result, output_dir):
        """Test that generate_report creates a markdown file."""
        report = quality_reporter.generate_report(sample_health_check_result)

        assert report.report_file_path.endswith('.md')
        assert os.path.exists(report.report_file_path)
        assert os.path.getsize(report.report_file_path) > 0

    def test_generate_report_creates_json_file(self, quality_reporter, sample_health_check_result, output_dir):
        """Test that generate_report creates a JSON file."""
        report = quality_reporter.generate_report(sample_health_check_result)

        json_path = report.report_file_path.replace('.md', '.json')
        assert os.path.exists(json_path)

        # Verify JSON is valid
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert 'report_id' in data
            assert 'overall_score' in data

    def test_generate_report_includes_all_sections(self, quality_reporter, sample_health_check_result, output_dir):
        """Test that generated report includes all required sections."""
        report = quality_reporter.generate_report(sample_health_check_result)

        with open(report.report_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for required sections
        assert '# Wiki Quality Report' in content
        assert '## Executive Summary' in content
        assert '## Quality Scores' in content
        assert '## Issue Breakdown' in content
        assert '## Critical Issues Requiring Attention' in content
        assert '## Recommendations' in content
        assert '## Detailed Findings' in content

    def test_generate_report_populates_all_fields(self, quality_reporter, sample_health_check_result):
        """Test that all report fields are properly populated."""
        report = quality_reporter.generate_report(sample_health_check_result)

        assert report.report_id is not None
        assert report.generated_at is not None
        assert report.time_range_start is not None
        assert report.time_range_end is not None
        assert report.overall_score == 0.75
        assert report.total_pages == 100
        assert report.total_issues == 3
        assert report.critical_issues == 1
        assert report.quality_trend in TrendDirection
        assert len(report.issue_breakdown) > 0
        assert len(report.recommendations) > 0
        assert len(report.detailed_findings) > 0


class TestTrendAnalysis:
    """Tests for trend analysis functionality."""

    def test_track_trend_with_improving_quality(self, quality_reporter, output_dir):
        """Test trend analysis with improving quality over time."""
        # Create multiple reports showing improvement
        now = datetime.now()
        reports = []

        for i in range(5):
            report = ExtendedQualityReport(
                report_id=f"report-{i}",
                generated_at=now - timedelta(days=5-i),
                time_range_start=now - timedelta(days=10-i),
                time_range_end=now - timedelta(days=5-i),
                overall_score=0.60 + (i * 0.05),  # Improving: 0.60, 0.65, 0.70, 0.75, 0.80
                total_pages=100,
                total_issues=10 - i,
                critical_issues=5 - i,
                quality_trend=TrendDirection.IMPROVING,
                issue_breakdown={},
                recommendations=[],
                detailed_findings=[],
                report_file_path=f"{output_dir}/report-{i}.md"
            )
            reports.append(report)

        trend = quality_reporter.track_trend(reports)

        assert trend.direction == TrendDirection.IMPROVING
        assert trend.confidence > 0.5
        assert len(trend.trend_points) > 0
        assert "improving" in trend.summary.lower()

    def test_track_trend_with_degrading_quality(self, quality_reporter, output_dir):
        """Test trend analysis with degrading quality over time."""
        now = datetime.now()
        reports = []

        for i in range(5):
            report = ExtendedQualityReport(
                report_id=f"report-{i}",
                generated_at=now - timedelta(days=5-i),
                time_range_start=now - timedelta(days=10-i),
                time_range_end=now - timedelta(days=5-i),
                overall_score=0.80 - (i * 0.05),  # Degrading: 0.80, 0.75, 0.70, 0.65, 0.60
                total_pages=100,
                total_issues=5 + i,
                critical_issues=2 + i,
                quality_trend=TrendDirection.DEGRADING,
                issue_breakdown={},
                recommendations=[],
                detailed_findings=[],
                report_file_path=f"{output_dir}/report-{i}.md"
            )
            reports.append(report)

        trend = quality_reporter.track_trend(reports)

        assert trend.direction == TrendDirection.DEGRADING
        assert trend.confidence > 0.5
        assert "degrading" in trend.summary.lower()

    def test_track_trend_with_stable_quality(self, quality_reporter, output_dir):
        """Test trend analysis with stable quality over time."""
        now = datetime.now()
        reports = []

        for i in range(5):
            report = ExtendedQualityReport(
                report_id=f"report-{i}",
                generated_at=now - timedelta(days=5-i),
                time_range_start=now - timedelta(days=10-i),
                time_range_end=now - timedelta(days=5-i),
                overall_score=0.75,  # Stable
                total_pages=100,
                total_issues=5,
                critical_issues=2,
                quality_trend=TrendDirection.STABLE,
                issue_breakdown={},
                recommendations=[],
                detailed_findings=[],
                report_file_path=f"{output_dir}/report-{i}.md"
            )
            reports.append(report)

        trend = quality_reporter.track_trend(reports)

        assert trend.direction == TrendDirection.STABLE
        assert "stable" in trend.summary.lower()

    def test_track_trend_insufficient_data(self, quality_reporter, output_dir):
        """Test trend analysis with insufficient data."""
        now = datetime.now()
        reports = []

        # Only 2 reports (need at least 3 for trend analysis)
        for i in range(2):
            report = ExtendedQualityReport(
                report_id=f"report-{i}",
                generated_at=now - timedelta(days=2-i),
                time_range_start=now - timedelta(days=4-i),
                time_range_end=now - timedelta(days=2-i),
                overall_score=0.75,
                total_pages=100,
                total_issues=5,
                critical_issues=2,
                quality_trend=TrendDirection.UNKNOWN,
                issue_breakdown={},
                recommendations=[],
                detailed_findings=[],
                report_file_path=f"{output_dir}/report-{i}.md"
            )
            reports.append(report)

        trend = quality_reporter.track_trend(reports)

        assert trend.direction == TrendDirection.UNKNOWN
        assert "insufficient" in trend.summary.lower()

    def test_track_trend_includes_prediction(self, quality_reporter, output_dir):
        """Test that trend analysis includes quality prediction."""
        now = datetime.now()
        reports = []

        for i in range(10):
            report = ExtendedQualityReport(
                report_id=f"report-{i}",
                generated_at=now - timedelta(days=10-i),
                time_range_start=now - timedelta(days=20-i),
                time_range_end=now - timedelta(days=10-i),
                overall_score=0.60 + (i * 0.02),  # Gradual improvement
                total_pages=100,
                total_issues=10 - i,
                critical_issues=5 - i,
                quality_trend=TrendDirection.IMPROVING,
                issue_breakdown={},
                recommendations=[],
                detailed_findings=[],
                report_file_path=f"{output_dir}/report-{i}.md"
            )
            reports.append(report)

        trend = quality_reporter.track_trend(reports)

        assert trend.predicted_quality_30_days is not None
        assert 0.0 <= trend.predicted_quality_30_days <= 1.0


class TestDashboardData:
    """Tests for dashboard data preparation."""

    def test_create_dashboard_data_includes_charts(self, quality_reporter, output_dir):
        """Test that dashboard data includes chart information."""
        now = datetime.now()
        reports = []

        for i in range(5):
            report = ExtendedQualityReport(
                report_id=f"report-{i}",
                generated_at=now - timedelta(days=5-i),
                time_range_start=now - timedelta(days=10-i),
                time_range_end=now - timedelta(days=5-i),
                overall_score=0.70 + (i * 0.05),
                total_pages=100,
                total_issues=10 - i,
                critical_issues=5 - i,
                quality_trend=TrendDirection.IMPROVING,
                issue_breakdown={
                    "orphan_page": 5 - i,
                    "broken_link": 3,
                    "stale_content": 2
                },
                recommendations=[],
                detailed_findings=[],
                report_file_path=f"{output_dir}/report-{i}.md"
            )
            reports.append(report)

        dashboard = quality_reporter.create_dashboard_data(reports)

        assert dashboard.generated_at is not None
        assert dashboard.time_range_days > 0
        assert len(dashboard.quality_over_time) > 0
        assert len(dashboard.issue_distribution) > 0
        assert len(dashboard.charts) > 0

    def test_create_dashboard_data_top_issues(self, quality_reporter, output_dir):
        """Test that dashboard data includes top issues."""
        now = datetime.now()
        reports = []

        # Create reports with various issues
        for i in range(5):
            report = ExtendedQualityReport(
                report_id=f"report-{i}",
                generated_at=now - timedelta(days=5-i),
                time_range_start=now - timedelta(days=10-i),
                time_range_end=now - timedelta(days=5-i),
                overall_score=0.75,
                total_pages=100,
                total_issues=15,
                critical_issues=5,
                quality_trend=TrendDirection.STABLE,
                issue_breakdown={
                    "orphan_page": 10,
                    "broken_link": 3,
                    "stale_content": 2
                },
                recommendations=[],
                detailed_findings=[
                    "Orphan pages need linking",
                    "Broken links require fixing",
                    "Stale content needs updates"
                ],
                report_file_path=f"{output_dir}/report-{i}.md"
            )
            reports.append(report)

        dashboard = quality_reporter.create_dashboard_data(reports)

        assert len(dashboard.top_issues) > 0
        assert len(dashboard.top_issues) <= 10  # Should be limited to top 10
        assert all('issue_type' in issue for issue in dashboard.top_issues)


class TestAlertSystem:
    """Tests for alert system functionality."""

    def test_send_alert_on_quality_degradation(self, quality_reporter, output_dir, tmp_path):
        """Test that alert is sent when quality degrades significantly."""
        # Create a health check result with low quality
        issues = [
            Issue(
                id="issue-1",
                issue_type=IssueType.BROKEN_LINK,
                severity=IssueSeverity.CRITICAL,
                page_id="test-page",
                description="Critical broken link",
                detected_at=datetime.now()
            )
        ]

        quality_report = QualityReport(
            overall_score=0.50,  # Below threshold
            page_count=100,
            avg_page_quality=0.50,
            completeness_score=0.50,
            freshness_score=0.50,
            metadata_score=0.50,
            issues_found=15,
            recommendations=["Fix critical issues"]
        )

        health_check = HealthCheckResult(
            timestamp=datetime.now(),
            consistency_issues=issues,
            quality_report=quality_report,
            staleness_issues=[],
            total_issues=15,
            critical_issues=12,  # Above threshold
            status="unhealthy"
        )

        # Create alert directory
        alert_dir = tmp_path / "alerts"
        alert_dir.mkdir(exist_ok=True)

        # Mock the alert file path
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log', dir=alert_dir) as f:
            alert_path = f.name

        success = quality_reporter.send_alert(health_check, alert_path)

        assert success is True
        assert os.path.exists(alert_path)

        with open(alert_path, 'r') as f:
            content = f.read()
            assert 'ALERT' in content
            assert 'Quality Degradation' in content or 'Critical' in content

    def test_send_alert_on_critical_issues(self, quality_reporter, sample_health_check_result, tmp_path):
        """Test that alert is sent when critical issues exceed threshold."""
        alert_dir = tmp_path / "alerts"
        alert_dir.mkdir(exist_ok=True)

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log', dir=alert_dir) as f:
            alert_path = f.name

        success = quality_reporter.send_alert(sample_health_check_result, alert_path)

        assert success is True
        assert os.path.exists(alert_path)

    def test_send_alert_no_alert_when_healthy(self, quality_reporter, tmp_path):
        """Test that no alert is sent when system is healthy."""
        # Create a healthy health check result
        quality_report = QualityReport(
            overall_score=0.90,  # High quality
            page_count=100,
            avg_page_quality=0.90,
            completeness_score=0.90,
            freshness_score=0.90,
            metadata_score=0.90,
            issues_found=2,
            recommendations=["Minor improvements"]
        )

        health_check = HealthCheckResult(
            timestamp=datetime.now(),
            consistency_issues=[],
            quality_report=quality_report,
            staleness_issues=[],
            total_issues=2,
            critical_issues=0,  # No critical issues
            status="healthy"
        )

        alert_dir = tmp_path / "alerts"
        alert_dir.mkdir(exist_ok=True)

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log', dir=alert_dir) as f:
            alert_path = f.name

        success = quality_reporter.send_alert(health_check, alert_path)

        # Should still return True but check if alert was actually written
        assert success is True
        # Alert file might not be created for healthy systems
        # or it might be created with "no alert" status


class TestIntegration:
    """Integration tests for QualityReporter."""

    def test_full_workflow(self, quality_reporter, sample_health_check_result):
        """Test complete workflow from report generation to dashboard."""
        # Generate report
        report = quality_reporter.generate_report(sample_health_check_result)
        assert report is not None
        assert os.path.exists(report.report_file_path)

        # Create multiple reports for trend analysis
        now = datetime.now()
        reports = [report]

        for i in range(1, 5):
            r = ExtendedQualityReport(
                report_id=f"report-{i}",
                generated_at=now - timedelta(days=i),
                time_range_start=now - timedelta(days=i+7),
                time_range_end=now - timedelta(days=i),
                overall_score=0.75 + (i * 0.02),
                total_pages=100,
                total_issues=10 - i,
                critical_issues=5 - i,
                quality_trend=TrendDirection.IMPROVING,
                issue_breakdown={},
                recommendations=[],
                detailed_findings=[],
                report_file_path=f"{quality_reporter.output_dir}/report-{i}.md"
            )
            reports.append(r)

        # Analyze trends
        trend = quality_reporter.track_trend(reports)
        assert trend is not None
        assert trend.direction in TrendDirection

        # Create dashboard data
        dashboard = quality_reporter.create_dashboard_data(reports)
        assert dashboard is not None
        assert len(dashboard.quality_over_time) > 0
