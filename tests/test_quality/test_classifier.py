"""
Tests for IssueClassifier that classifies and prioritizes detected issues.

This test suite validates the intelligent issue triage system that categorizes
issues by type, severity, and repair complexity.
"""

import pytest
from datetime import datetime
from src.wiki.quality.models import (
    Issue,
    IssueType,
    IssueSeverity,
    IssueCategory,
    RepairComplexity,
    RepairApproach,
    ClassifiedIssue,
    RepairPlan
)
from src.wiki.quality.classifier import IssueClassifier


class TestClassifyIssue:
    """Test individual issue classification."""

    def test_classify_issue_orphan_page(self):
        """Test classification of orphan page issues."""
        classifier = IssueClassifier()
        issue = Issue(
            id="issue-1",
            issue_type=IssueType.ORPHAN_PAGE,
            severity=IssueSeverity.MEDIUM,
            page_id="page-1",
            description="Page has no inbound links",
            detected_at=datetime.now()
        )

        classified = classifier.classify_issue(issue)

        assert classified.category == IssueCategory.STRUCTURAL
        assert classified.complexity == RepairComplexity.MEDIUM
        assert classified.approach == RepairApproach.SEMI_AUTOMATIC
        assert 0.4 <= classified.priority_score <= 0.7  # MEDIUM severity
        assert classified.estimated_repair_time_minutes == 30  # MEDIUM base time
        assert len(classified.suggested_actions) > 0
        assert isinstance(classified.dependencies, list)

    def test_classify_issue_broken_link(self):
        """Test classification of broken link issues."""
        classifier = IssueClassifier()
        issue = Issue(
            id="issue-2",
            issue_type=IssueType.BROKEN_LINK,
            severity=IssueSeverity.HIGH,
            page_id="page-2",
            description="Link to non-existent page",
            detected_at=datetime.now()
        )

        classified = classifier.classify_issue(issue)

        assert classified.category == IssueCategory.DATA_INTEGRITY
        assert classified.complexity == RepairComplexity.SIMPLE
        assert classified.approach == RepairApproach.AUTOMATIC
        assert 0.6 <= classified.priority_score <= 0.9  # HIGH severity
        assert classified.estimated_repair_time_minutes == 22  # 15 base × 1.5 HIGH multiplier
        assert classified.can_repair_automatically is True

    def test_classify_issue_circular_ref(self):
        """Test classification of circular reference issues."""
        classifier = IssueClassifier()
        issue = Issue(
            id="issue-3",
            issue_type=IssueType.CIRCULAR_REF,
            severity=IssueSeverity.CRITICAL,
            page_id="page-3",
            description="Circular reference detected",
            detected_at=datetime.now()
        )

        classified = classifier.classify_issue(issue)

        assert classified.category == IssueCategory.STRUCTURAL
        assert classified.complexity == RepairComplexity.COMPLEX
        assert classified.approach == RepairApproach.MANUAL
        assert 0.9 <= classified.priority_score <= 1.0  # CRITICAL severity
        assert classified.estimated_repair_time_minutes == 240  # 120 base × 2.0 CRITICAL multiplier
        assert classified.can_repair_automatically is False

    def test_classify_issue_duplicate_content(self):
        """Test classification of duplicate content issues."""
        classifier = IssueClassifier()
        issue = Issue(
            id="issue-4",
            issue_type=IssueType.DUPLICATE_CONTENT,
            severity=IssueSeverity.HIGH,
            page_id="page-4",
            description="Duplicate content found",
            detected_at=datetime.now()
        )

        classified = classifier.classify_issue(issue)

        assert classified.category == IssueCategory.DATA_INTEGRITY
        assert classified.complexity == RepairComplexity.MEDIUM
        assert classified.approach == RepairApproach.SEMI_AUTOMATIC
        assert 0.7 <= classified.priority_score <= 0.9  # HIGH severity
        assert classified.estimated_repair_time_minutes == 45  # 30 base × 1.5 HIGH multiplier

    def test_classify_issue_stale_content(self):
        """Test classification of stale content issues."""
        classifier = IssueClassifier()
        issue = Issue(
            id="issue-5",
            issue_type=IssueType.STALE_CONTENT,
            severity=IssueSeverity.LOW,
            page_id="page-5",
            description="Content not updated in 2 years",
            detected_at=datetime.now()
        )

        classified = classifier.classify_issue(issue)

        assert classified.category == IssueCategory.CONTENT_QUALITY
        assert classified.complexity == RepairComplexity.SIMPLE
        assert classified.approach == RepairApproach.AUTOMATIC
        assert 0.0 <= classified.priority_score <= 0.4  # LOW severity
        assert classified.estimated_repair_time_minutes == 7  # 15 base × 0.5 LOW multiplier (rounded)
        assert classified.can_repair_automatically is True

    def test_classify_issue_missing_metadata(self):
        """Test classification of missing metadata issues."""
        classifier = IssueClassifier()
        issue = Issue(
            id="issue-6",
            issue_type=IssueType.MISSING_METADATA,
            severity=IssueSeverity.MEDIUM,
            page_id="page-6",
            description="Missing tags metadata",
            detected_at=datetime.now()
        )

        classified = classifier.classify_issue(issue)

        assert classified.category == IssueCategory.METADATA
        assert classified.complexity == RepairComplexity.SIMPLE
        assert classified.approach == RepairApproach.AUTOMATIC
        assert 0.4 <= classified.priority_score <= 0.7  # MEDIUM severity
        assert classified.estimated_repair_time_minutes == 15  # SIMPLE base time
        assert classified.can_repair_automatically is True

    def test_classify_issue_low_quality(self):
        """Test classification of low quality issues."""
        classifier = IssueClassifier()
        issue = Issue(
            id="issue-7",
            issue_type=IssueType.LOW_QUALITY,
            severity=IssueSeverity.HIGH,
            page_id="page-7",
            description="Content quality score below threshold",
            detected_at=datetime.now()
        )

        classified = classifier.classify_issue(issue)

        assert classified.category == IssueCategory.CONTENT_QUALITY
        assert classified.complexity == RepairComplexity.MEDIUM
        assert classified.approach == RepairApproach.MANUAL
        assert 0.6 <= classified.priority_score <= 0.9  # HIGH severity but lower type weight
        assert classified.estimated_repair_time_minutes == 45  # 30 base × 1.5 HIGH multiplier
        assert classified.can_repair_automatically is False


class TestClassifyBatch:
    """Test batch classification of multiple issues."""

    def test_classify_batch_multiple_issues(self):
        """Test classification of multiple issues in batch."""
        classifier = IssueClassifier()
        issues = [
            Issue(
                id=f"issue-{i}",
                issue_type=IssueType.ORPHAN_PAGE,
                severity=IssueSeverity.MEDIUM,
                page_id=f"page-{i}",
                description=f"Description {i}",
                detected_at=datetime.now()
            )
            for i in range(1, 6)
        ]

        classified_issues = classifier.classify_batch(issues)

        assert len(classified_issues) == 5
        for classified in classified_issues:
            assert isinstance(classified, ClassifiedIssue)
            assert classified.category == IssueCategory.STRUCTURAL
            assert classified.complexity == RepairComplexity.MEDIUM


class TestPrioritizeIssues:
    """Test issue prioritization logic."""

    def test_prioritize_issues_sorts_by_priority(self):
        """Test that issues are sorted by priority score descending."""
        classifier = IssueClassifier()
        classified_issues = [
            ClassifiedIssue(
                original_issue=Issue(
                    id="issue-1",
                    issue_type=IssueType.STALE_CONTENT,
                    severity=IssueSeverity.LOW,
                    page_id="page-1",
                    description="Low priority",
                    detected_at=datetime.now()
                ),
                category=IssueCategory.CONTENT_QUALITY,
                complexity=RepairComplexity.SIMPLE,
                approach=RepairApproach.AUTOMATIC,
                priority_score=0.2,
                estimated_repair_time_minutes=15,
                suggested_actions=["Update content"],
                dependencies=[],
                can_repair_automatically=True
            ),
            ClassifiedIssue(
                original_issue=Issue(
                    id="issue-2",
                    issue_type=IssueType.CIRCULAR_REF,
                    severity=IssueSeverity.CRITICAL,
                    page_id="page-2",
                    description="High priority",
                    detected_at=datetime.now()
                ),
                category=IssueCategory.STRUCTURAL,
                complexity=RepairComplexity.COMPLEX,
                approach=RepairApproach.MANUAL,
                priority_score=0.95,
                estimated_repair_time_minutes=120,
                suggested_actions=["Break circular reference"],
                dependencies=[],
                can_repair_automatically=False
            )
        ]

        prioritized = classifier.prioritize_issues(classified_issues)

        assert len(prioritized) == 2
        assert prioritized[0].priority_score > prioritized[1].priority_score
        assert prioritized[0].original_issue.id == "issue-2"

    def test_prioritize_issues_sorts_by_severity(self):
        """Test that issues with same priority are sorted by severity."""
        classifier = IssueClassifier()
        classified_issues = [
            ClassifiedIssue(
                original_issue=Issue(
                    id="issue-1",
                    issue_type=IssueType.STALE_CONTENT,
                    severity=IssueSeverity.LOW,
                    page_id="page-1",
                    description="Low severity",
                    detected_at=datetime.now()
                ),
                category=IssueCategory.CONTENT_QUALITY,
                complexity=RepairComplexity.SIMPLE,
                approach=RepairApproach.AUTOMATIC,
                priority_score=0.5,
                estimated_repair_time_minutes=15,
                suggested_actions=["Update"],
                dependencies=[],
                can_repair_automatically=True
            ),
            ClassifiedIssue(
                original_issue=Issue(
                    id="issue-2",
                    issue_type=IssueType.BROKEN_LINK,
                    severity=IssueSeverity.HIGH,
                    page_id="page-2",
                    description="High severity",
                    detected_at=datetime.now()
                ),
                category=IssueCategory.DATA_INTEGRITY,
                complexity=RepairComplexity.SIMPLE,
                approach=RepairApproach.AUTOMATIC,
                priority_score=0.5,
                estimated_repair_time_minutes=15,
                suggested_actions=["Fix link"],
                dependencies=[],
                can_repair_automatically=True
            )
        ]

        prioritized = classifier.prioritize_issues(classified_issues)

        # Same priority, but HIGH severity should come first
        assert prioritized[0].original_issue.severity == IssueSeverity.HIGH
        assert prioritized[1].original_issue.severity == IssueSeverity.LOW


class TestSuggestRepairPlan:
    """Test repair plan generation."""

    def test_suggest_repair_plan_groups_by_approach(self):
        """Test that repair plan groups issues by repair approach."""
        classifier = IssueClassifier()
        classified_issues = [
            ClassifiedIssue(
                original_issue=Issue(
                    id="issue-1",
                    issue_type=IssueType.BROKEN_LINK,
                    severity=IssueSeverity.HIGH,
                    page_id="page-1",
                    description="Broken link",
                    detected_at=datetime.now()
                ),
                category=IssueCategory.DATA_INTEGRITY,
                complexity=RepairComplexity.SIMPLE,
                approach=RepairApproach.AUTOMATIC,
                priority_score=0.8,
                estimated_repair_time_minutes=15,
                suggested_actions=["Fix link"],
                dependencies=[],
                can_repair_automatically=True
            ),
            ClassifiedIssue(
                original_issue=Issue(
                    id="issue-2",
                    issue_type=IssueType.ORPHAN_PAGE,
                    severity=IssueSeverity.MEDIUM,
                    page_id="page-2",
                    description="Orphan page",
                    detected_at=datetime.now()
                ),
                category=IssueCategory.STRUCTURAL,
                complexity=RepairComplexity.MEDIUM,
                approach=RepairApproach.SEMI_AUTOMATIC,
                priority_score=0.5,
                estimated_repair_time_minutes=30,
                suggested_actions=["Review orphan"],
                dependencies=[],
                can_repair_automatically=False
            )
        ]

        plan = classifier.suggest_repair_plan(classified_issues)

        assert plan.total_issues == 2
        assert plan.automatic_repairs == 1
        assert plan.semi_automatic_repairs == 1
        assert plan.manual_repairs == 0
        assert "automatic" in plan.issue_groups
        assert "semi_auto" in plan.issue_groups
        assert len(plan.issue_groups["automatic"]) == 1
        assert len(plan.issue_groups["semi_auto"]) == 1

    def test_suggest_repair_plan_estimates_time(self):
        """Test that repair plan accurately estimates total time."""
        classifier = IssueClassifier()
        classified_issues = [
            ClassifiedIssue(
                original_issue=Issue(
                    id=f"issue-{i}",
                    issue_type=IssueType.BROKEN_LINK,
                    severity=IssueSeverity.HIGH,
                    page_id=f"page-{i}",
                    description=f"Issue {i}",
                    detected_at=datetime.now()
                ),
                category=IssueCategory.DATA_INTEGRITY,
                complexity=RepairComplexity.SIMPLE,
                approach=RepairApproach.AUTOMATIC,
                priority_score=0.8,
                estimated_repair_time_minutes=15,
                suggested_actions=["Fix"],
                dependencies=[],
                can_repair_automatically=True
            )
            for i in range(1, 4)
        ]

        plan = classifier.suggest_repair_plan(classified_issues)

        assert plan.total_estimated_time_minutes == 45  # 3 issues × 15 minutes

    def test_suggest_repair_plan_identifies_dependencies(self):
        """Test that repair plan groups issues by repair approach correctly."""
        classifier = IssueClassifier()
        classified_issues = [
            ClassifiedIssue(
                original_issue=Issue(
                    id="issue-1",
                    issue_type=IssueType.BROKEN_LINK,
                    severity=IssueSeverity.HIGH,
                    page_id="page-1",
                    description="Broken link",
                    detected_at=datetime.now()
                ),
                category=IssueCategory.DATA_INTEGRITY,
                complexity=RepairComplexity.SIMPLE,
                approach=RepairApproach.AUTOMATIC,
                priority_score=0.8,
                estimated_repair_time_minutes=15,
                suggested_actions=["Fix link"],
                dependencies=[],
                can_repair_automatically=True
            ),
            ClassifiedIssue(
                original_issue=Issue(
                    id="issue-2",
                    issue_type=IssueType.ORPHAN_PAGE,
                    severity=IssueSeverity.MEDIUM,
                    page_id="page-2",
                    description="Orphan page",
                    detected_at=datetime.now()
                ),
                category=IssueCategory.STRUCTURAL,
                complexity=RepairComplexity.MEDIUM,
                approach=RepairApproach.SEMI_AUTOMATIC,
                priority_score=0.5,
                estimated_repair_time_minutes=30,
                suggested_actions=["Review"],
                dependencies=[],
                can_repair_automatically=False
            )
        ]

        plan = classifier.suggest_repair_plan(classified_issues)

        # Automatic repairs should come before semi-automatic
        assert plan.recommended_order.index("issue-1") < plan.recommended_order.index("issue-2")


class TestPriorityScoring:
    """Test priority score calculation."""

    def test_priority_score_calculation(self):
        """Test that priority score uses weighted formula correctly."""
        classifier = IssueClassifier()
        issue = Issue(
            id="issue-1",
            issue_type=IssueType.CIRCULAR_REF,
            severity=IssueSeverity.CRITICAL,
            page_id="page-1",
            description="Critical issue",
            detected_at=datetime.now()
        )

        classified = classifier.classify_issue(issue)

        # CRITICAL severity should result in high priority score
        # Formula: severity_weight × 0.5 + complexity_weight × 0.3 + type_weight × 0.2
        assert classified.priority_score >= 0.9
        assert classified.priority_score <= 1.0


class TestRepairTimeEstimation:
    """Test repair time estimation."""

    def test_estimated_repair_time_by_complexity_and_severity(self):
        """Test that repair time is estimated based on complexity and severity."""
        classifier = IssueClassifier()

        # SIMPLE complexity, LOW severity
        issue1 = Issue(
            id="issue-1",
            issue_type=IssueType.STALE_CONTENT,
            severity=IssueSeverity.LOW,
            page_id="page-1",
            description="Simple low severity",
            detected_at=datetime.now()
        )
        classified1 = classifier.classify_issue(issue1)

        # COMPLEX complexity, CRITICAL severity
        issue2 = Issue(
            id="issue-2",
            issue_type=IssueType.CIRCULAR_REF,
            severity=IssueSeverity.CRITICAL,
            page_id="page-2",
            description="Complex critical",
            detected_at=datetime.now()
        )
        classified2 = classifier.classify_issue(issue2)

        # Complex critical should take much longer than simple low
        assert classified2.estimated_repair_time_minutes > classified1.estimated_repair_time_minutes


class TestSuggestedActions:
    """Test suggested action generation."""

    def test_suggested_actions_by_issue_type(self):
        """Test that appropriate actions are suggested for each issue type."""
        classifier = IssueClassifier()

        # Test BROKEN_LINK actions
        broken_link_issue = Issue(
            id="issue-1",
            issue_type=IssueType.BROKEN_LINK,
            severity=IssueSeverity.HIGH,
            page_id="page-1",
            description="Broken link",
            detected_at=datetime.now()
        )
        classified = classifier.classify_issue(broken_link_issue)
        assert len(classified.suggested_actions) > 0
        assert any("link" in action.lower() for action in classified.suggested_actions)

        # Test CIRCULAR_REF actions
        circular_ref_issue = Issue(
            id="issue-2",
            issue_type=IssueType.CIRCULAR_REF,
            severity=IssueSeverity.CRITICAL,
            page_id="page-2",
            description="Circular ref",
            detected_at=datetime.now()
        )
        classified = classifier.classify_issue(circular_ref_issue)
        assert len(classified.suggested_actions) > 0
        assert any("circular" in action.lower() for action in classified.suggested_actions)


class TestCustomConfiguration:
    """Test classifier with custom configuration."""

    def test_classify_issue_with_custom_config(self):
        """Test that custom configuration affects classification."""
        custom_config = {
            "auto_classify": True,
            "suggest_repair": True,
            "priority_weights": {
                "severity": 0.7,  # Higher weight for severity
                "complexity": 0.2,
                "type": 0.1
            }
        }
        classifier = IssueClassifier(config=custom_config)

        issue = Issue(
            id="issue-1",
            issue_type=IssueType.BROKEN_LINK,
            severity=IssueSeverity.CRITICAL,
            page_id="page-1",
            description="Critical broken link",
            detected_at=datetime.now()
        )

        classified = classifier.classify_issue(issue)

        # With higher severity weight, CRITICAL should result in very high priority
        # CRITICAL severity weight 1.0 × 0.7 = 0.7
        # SIMPLE complexity weight 0.3 × 0.2 = 0.06
        # BROKEN_LINK type weight 0.9 × 0.1 = 0.09
        # Total = 0.85
        assert classified.priority_score >= 0.85
        assert classified.category == IssueCategory.DATA_INTEGRITY
