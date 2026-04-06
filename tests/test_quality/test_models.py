"""
Tests for Wiki quality assurance data models.

Tests the Issue, QualityReport, and HealthCheckResult models with various configurations and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from src.wiki.quality.models import (
    IssueType,
    IssueSeverity,
    Issue,
    QualityReport,
    HealthCheckResult
)


class TestIssue:
    """Tests for the Issue model."""

    def test_issue_creation_with_all_fields(self):
        """Test creating an issue with all fields populated."""
        issue = Issue(
            id="issue-1",
            issue_type=IssueType.ORPHAN_PAGE,
            severity=IssueSeverity.HIGH,
            page_id="page-123",
            description="This page has no incoming links",
            detected_at=datetime.now(),
            metadata={"link_count": 0}
        )
        assert issue.id == "issue-1"
        assert issue.issue_type == IssueType.ORPHAN_PAGE
        assert issue.severity == IssueSeverity.HIGH
        assert issue.page_id == "page-123"
        assert "no incoming links" in issue.description
        assert issue.metadata["link_count"] == 0

    def test_issue_creation_with_minimal_fields(self):
        """Test creating an issue with minimal required fields."""
        issue = Issue(
            id="issue-2",
            issue_type=IssueType.BROKEN_LINK,
            severity=IssueSeverity.CRITICAL,
            page_id="page-456",
            description="Broken link detected",
            detected_at=datetime.now()
        )
        assert issue.metadata == {}
        assert issue.issue_type == IssueType.BROKEN_LINK
        assert issue.severity == IssueSeverity.CRITICAL

    def test_issue_type_enum_values(self):
        """Test that IssueType enum has all expected values."""
        assert IssueType.ORPHAN_PAGE.value == "orphan_page"
        assert IssueType.BROKEN_LINK.value == "broken_link"
        assert IssueType.CIRCULAR_REF.value == "circular_ref"
        assert IssueType.DUPLICATE_CONTENT.value == "duplicate_content"
        assert IssueType.STALE_CONTENT.value == "stale_content"
        assert IssueType.MISSING_METADATA.value == "missing_metadata"
        assert IssueType.LOW_QUALITY.value == "low_quality"

    def test_issue_severity_enum_values(self):
        """Test that IssueSeverity enum has all expected values."""
        assert IssueSeverity.CRITICAL.value == "critical"
        assert IssueSeverity.HIGH.value == "high"
        assert IssueSeverity.MEDIUM.value == "medium"
        assert IssueSeverity.LOW.value == "low"

    def test_issue_serialization(self):
        """Test that Issue can be serialized to dict."""
        issue = Issue(
            id="issue-3",
            issue_type=IssueType.STALE_CONTENT,
            severity=IssueSeverity.MEDIUM,
            page_id="page-789",
            description="Content not updated in 45 days",
            detected_at=datetime.now(),
            metadata={"days_since_update": 45}
        )
        issue_dict = issue.model_dump()
        assert issue_dict["id"] == "issue-3"
        assert issue_dict["issue_type"] == "stale_content"
        assert issue_dict["severity"] == "medium"
        assert issue_dict["metadata"]["days_since_update"] == 45


class TestQualityReport:
    """Tests for the QualityReport model."""

    def test_quality_report_creation(self):
        """Test creating a comprehensive quality report."""
        report = QualityReport(
            overall_score=0.85,
            page_count=100,
            avg_page_quality=0.82,
            completeness_score=0.90,
            freshness_score=0.75,
            metadata_score=0.88,
            issues_found=15,
            recommendations=["Update stale pages", "Fix broken links"]
        )
        assert report.overall_score == 0.85
        assert report.page_count == 100
        assert report.avg_page_quality == 0.82
        assert report.completeness_score == 0.90
        assert report.freshness_score == 0.75
        assert report.metadata_score == 0.88
        assert report.issues_found == 15
        assert len(report.recommendations) == 2

    def test_quality_report_with_empty_recommendations(self):
        """Test quality report with no recommendations."""
        report = QualityReport(
            overall_score=1.0,
            page_count=50,
            avg_page_quality=1.0,
            completeness_score=1.0,
            freshness_score=1.0,
            metadata_score=1.0,
            issues_found=0,
            recommendations=[]
        )
        assert report.issues_found == 0
        assert len(report.recommendations) == 0
        assert report.overall_score == 1.0

    def test_quality_report_score_bounds(self):
        """Test that quality scores are within valid bounds."""
        # Test with valid scores
        report = QualityReport(
            overall_score=0.5,
            page_count=10,
            avg_page_quality=0.6,
            completeness_score=0.7,
            freshness_score=0.4,
            metadata_score=0.8,
            issues_found=5,
            recommendations=[]
        )
        assert 0.0 <= report.overall_score <= 1.0
        assert 0.0 <= report.avg_page_quality <= 1.0
        assert 0.0 <= report.completeness_score <= 1.0
        assert 0.0 <= report.freshness_score <= 1.0
        assert 0.0 <= report.metadata_score <= 1.0


class TestHealthCheckResult:
    """Tests for the HealthCheckResult model."""

    def test_health_check_result_creation_healthy(self):
        """Test creating a health check result with healthy status."""
        issues = [
            Issue(
                id="issue-1",
                issue_type=IssueType.ORPHAN_PAGE,
                severity=IssueSeverity.LOW,
                page_id="page-1",
                description="Minor orphan page",
                detected_at=datetime.now()
            )
        ]
        quality_report = QualityReport(
            overall_score=0.9,
            page_count=50,
            avg_page_quality=0.88,
            completeness_score=0.92,
            freshness_score=0.85,
            metadata_score=0.90,
            issues_found=1,
            recommendations=[]
        )
        result = HealthCheckResult(
            timestamp=datetime.now(),
            consistency_issues=issues,
            quality_report=quality_report,
            staleness_issues=[],
            total_issues=1,
            critical_issues=0,
            status="healthy"
        )
        assert result.status == "healthy"
        assert result.total_issues == 1
        assert result.critical_issues == 0
        assert len(result.consistency_issues) == 1
        assert len(result.staleness_issues) == 0

    def test_health_check_result_creation_degraded(self):
        """Test creating a health check result with degraded status."""
        issues = [
            Issue(
                id=f"issue-{i}",
                issue_type=IssueType.BROKEN_LINK,
                severity=IssueSeverity.HIGH,
                page_id=f"page-{i}",
                description="Broken link",
                detected_at=datetime.now()
            ) for i in range(5)
        ]
        quality_report = QualityReport(
            overall_score=0.65,
            page_count=50,
            avg_page_quality=0.70,
            completeness_score=0.75,
            freshness_score=0.60,
            metadata_score=0.65,
            issues_found=5,
            recommendations=["Fix broken links"]
        )
        result = HealthCheckResult(
            timestamp=datetime.now(),
            consistency_issues=issues,
            quality_report=quality_report,
            staleness_issues=[],
            total_issues=5,
            critical_issues=0,
            status="degraded"
        )
        assert result.status == "degraded"
        assert result.total_issues == 5
        assert result.quality_report.overall_score == 0.65

    def test_health_check_result_creation_unhealthy(self):
        """Test creating a health check result with unhealthy status."""
        critical_issues = [
            Issue(
                id=f"critical-{i}",
                issue_type=IssueType.BROKEN_LINK,
                severity=IssueSeverity.CRITICAL,
                page_id=f"page-{i}",
                description="Critical data integrity issue",
                detected_at=datetime.now()
            ) for i in range(3)
        ]
        quality_report = QualityReport(
            overall_score=0.3,
            page_count=50,
            avg_page_quality=0.35,
            completeness_score=0.40,
            freshness_score=0.30,
            metadata_score=0.35,
            issues_found=10,
            recommendations=["Immediate attention required"]
        )
        result = HealthCheckResult(
            timestamp=datetime.now(),
            consistency_issues=critical_issues,
            quality_report=quality_report,
            staleness_issues=[],
            total_issues=10,
            critical_issues=3,
            status="unhealthy"
        )
        assert result.status == "unhealthy"
        assert result.critical_issues == 3
        assert result.quality_report.overall_score < 0.5

    def test_health_check_result_aggregates_all_issues(self):
        """Test that health check result properly aggregates all issue types."""
        consistency_issues = [
            Issue(
                id="cons-1",
                issue_type=IssueType.ORPHAN_PAGE,
                severity=IssueSeverity.MEDIUM,
                page_id="page-1",
                description="Orphan page",
                detected_at=datetime.now()
            )
        ]
        staleness_issues = [
            Issue(
                id="stale-1",
                issue_type=IssueType.STALE_CONTENT,
                severity=IssueSeverity.HIGH,
                page_id="page-2",
                description="Stale content",
                detected_at=datetime.now()
            )
        ]
        quality_report = QualityReport(
            overall_score=0.75,
            page_count=20,
            avg_page_quality=0.78,
            completeness_score=0.80,
            freshness_score=0.70,
            metadata_score=0.75,
            issues_found=2,
            recommendations=[]
        )
        result = HealthCheckResult(
            timestamp=datetime.now(),
            consistency_issues=consistency_issues,
            quality_report=quality_report,
            staleness_issues=staleness_issues,
            total_issues=2,
            critical_issues=0,
            status="degraded"
        )
        assert len(result.consistency_issues) == 1
        assert len(result.staleness_issues) == 1
        assert result.total_issues == 2
