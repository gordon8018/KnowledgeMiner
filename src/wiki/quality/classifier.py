"""
IssueClassifier for intelligent issue triage and repair planning.

This module provides classification and prioritization of quality issues detected
in the Wiki system, enabling efficient repair planning and execution.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import (
    Issue,
    IssueType,
    IssueSeverity,
    IssueCategory,
    RepairComplexity,
    RepairApproach,
    ClassifiedIssue,
    RepairPlan
)


class IssueClassifier:
    """
    Classifies and prioritizes detected Wiki quality issues.

    The IssueClassifier analyzes issues by type, severity, and complexity to determine
    the best repair approach and estimate required effort. It generates comprehensive
    repair plans with prioritized action items.
    """

    # Classification rules for each issue type
    CLASSIFICATION_RULES = {
        IssueType.ORPHAN_PAGE: {
            "category": IssueCategory.STRUCTURAL,
            "complexity": RepairComplexity.MEDIUM,
            "approach": RepairApproach.SEMI_AUTOMATIC,
            "base_time_minutes": 30,
            "suggested_actions": [
                "Review orphan page for valuable content",
                "Add inbound links from relevant pages",
                "Consider merging with related pages if appropriate",
                "Delete if content is obsolete or redundant"
            ]
        },
        IssueType.BROKEN_LINK: {
            "category": IssueCategory.DATA_INTEGRITY,
            "complexity": RepairComplexity.SIMPLE,
            "approach": RepairApproach.AUTOMATIC,
            "base_time_minutes": 15,
            "suggested_actions": [
                "Update link to point to correct page",
                "Remove link if target page no longer exists",
                "Create redirect if page was moved"
            ]
        },
        IssueType.CIRCULAR_REF: {
            "category": IssueCategory.STRUCTURAL,
            "complexity": RepairComplexity.COMPLEX,
            "approach": RepairApproach.MANUAL,
            "base_time_minutes": 120,
            "suggested_actions": [
                "Analyze circular reference chain",
                "Identify which link to break",
                "Reorganize content structure to eliminate cycle",
                "Update affected pages and verify fix"
            ]
        },
        IssueType.DUPLICATE_CONTENT: {
            "category": IssueCategory.DATA_INTEGRITY,
            "complexity": RepairComplexity.MEDIUM,
            "approach": RepairApproach.SEMI_AUTOMATIC,
            "base_time_minutes": 30,
            "suggested_actions": [
                "Compare duplicate pages for differences",
                "Merge unique content into single page",
                "Set up redirects from eliminated pages",
                "Update all inbound links"
            ]
        },
        IssueType.STALE_CONTENT: {
            "category": IssueCategory.CONTENT_QUALITY,
            "complexity": RepairComplexity.SIMPLE,
            "approach": RepairApproach.AUTOMATIC,
            "base_time_minutes": 15,
            "suggested_actions": [
                "Review content for outdated information",
                "Update with current information",
                "Add last-updated date if missing",
                "Consider archiving if no longer relevant"
            ]
        },
        IssueType.MISSING_METADATA: {
            "category": IssueCategory.METADATA,
            "complexity": RepairComplexity.SIMPLE,
            "approach": RepairApproach.AUTOMATIC,
            "base_time_minutes": 15,
            "suggested_actions": [
                "Add missing metadata fields",
                "Generate automatic tags from content",
                "Set appropriate categories",
                "Update page summary"
            ]
        },
        IssueType.LOW_QUALITY: {
            "category": IssueCategory.CONTENT_QUALITY,
            "complexity": RepairComplexity.MEDIUM,
            "approach": RepairApproach.MANUAL,
            "base_time_minutes": 30,
            "suggested_actions": [
                "Review content quality issues",
                "Improve writing and structure",
                "Add examples and clarification",
                "Enhance formatting and readability"
            ]
        }
    }

    # Severity multipliers for repair time estimation
    SEVERITY_MULTIPLIERS = {
        IssueSeverity.CRITICAL: 2.0,
        IssueSeverity.HIGH: 1.5,
        IssueSeverity.MEDIUM: 1.0,
        IssueSeverity.LOW: 0.5
    }

    # Severity weights for priority scoring (0.0 to 1.0)
    SEVERITY_WEIGHTS = {
        IssueSeverity.CRITICAL: 1.0,
        IssueSeverity.HIGH: 0.8,
        IssueSeverity.MEDIUM: 0.55,
        IssueSeverity.LOW: 0.2
    }

    # Complexity weights for priority scoring (0.0 to 1.0)
    COMPLEXITY_WEIGHTS = {
        RepairComplexity.SIMPLE: 0.3,
        RepairComplexity.MEDIUM: 0.5,
        RepairComplexity.COMPLEX: 0.7
    }

    # Type weights for priority scoring (0.0 to 1.0)
    TYPE_WEIGHTS = {
        IssueType.CIRCULAR_REF: 1.0,
        IssueType.BROKEN_LINK: 0.9,
        IssueType.DUPLICATE_CONTENT: 0.8,
        IssueType.ORPHAN_PAGE: 0.6,
        IssueType.LOW_QUALITY: 0.5,
        IssueType.MISSING_METADATA: 0.3,
        IssueType.STALE_CONTENT: 0.2
    }

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the IssueClassifier with configuration.

        Args:
            config: Optional configuration dictionary with keys:
                - auto_classify: Enable automatic classification (default: True)
                - suggest_repair: Enable repair suggestions (default: True)
                - priority_weights: Custom weights for priority calculation
                  with keys: severity, complexity, type (default: equal weights)
        """
        self.config = config or {}
        self.auto_classify = self.config.get("auto_classify", True)
        self.suggest_repair = self.config.get("suggest_repair", True)

        # Priority weights (default: severity 0.5, complexity 0.3, type 0.2)
        default_weights = {"severity": 0.5, "complexity": 0.3, "type": 0.2}
        self.priority_weights = self.config.get("priority_weights", default_weights)

        # Validate priority weights sum to 1.0
        weight_sum = sum(self.priority_weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            # Normalize weights
            self.priority_weights = {
                k: v / weight_sum
                for k, v in self.priority_weights.items()
            }

    def classify_issue(self, issue: Issue) -> ClassifiedIssue:
        """
        Classify a single issue by type, severity, and complexity.

        Args:
            issue: The Issue to classify

        Returns:
            ClassifiedIssue with category, complexity, approach, and repair suggestions
        """
        if not self.auto_classify:
            raise ValueError("Automatic classification is disabled")

        # Get classification rules for this issue type
        rules = self.CLASSIFICATION_RULES.get(issue.issue_type)
        if not rules:
            raise ValueError(f"No classification rules for issue type: {issue.issue_type}")

        # Calculate priority score
        priority_score = self._calculate_priority_score(issue)

        # Calculate repair time
        base_time = rules["base_time_minutes"]
        severity_multiplier = self.SEVERITY_MULTIPLIERS.get(issue.severity, 1.0)
        estimated_time = int(base_time * severity_multiplier)

        # Determine if can be repaired automatically
        can_repair_auto = rules["approach"] == RepairApproach.AUTOMATIC

        # Detect dependencies
        dependencies = self._detect_dependencies(issue)

        # Get suggested actions
        suggested_actions = rules["suggested_actions"] if self.suggest_repair else []

        return ClassifiedIssue(
            original_issue=issue,
            category=rules["category"],
            complexity=rules["complexity"],
            approach=rules["approach"],
            priority_score=priority_score,
            estimated_repair_time_minutes=estimated_time,
            suggested_actions=suggested_actions,
            dependencies=dependencies,
            can_repair_automatically=can_repair_auto
        )

    def classify_batch(self, issues: List[Issue]) -> List[ClassifiedIssue]:
        """
        Classify multiple issues efficiently.

        Args:
            issues: List of Issues to classify

        Returns:
            List of ClassifiedIssue objects
        """
        classified_issues = []
        for issue in issues:
            try:
                classified = self.classify_issue(issue)
                classified_issues.append(classified)
            except ValueError as e:
                # Skip issues that can't be classified
                continue

        return classified_issues

    def prioritize_issues(
        self,
        classified_issues: List[ClassifiedIssue]
    ) -> List[ClassifiedIssue]:
        """
        Sort issues by priority score and severity.

        Args:
            classified_issues: List of ClassifiedIssue objects

        Returns:
            Prioritized list sorted by:
            1. Priority score (descending)
            2. Severity (CRITICAL > HIGH > MEDIUM > LOW)
        """
        # Define severity order for sorting
        severity_order = {
            IssueSeverity.CRITICAL: 4,
            IssueSeverity.HIGH: 3,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 1
        }

        def sort_key(issue: ClassifiedIssue) -> tuple:
            """Sort by priority score (desc) then severity (desc)."""
            priority_desc = -issue.priority_score
            severity_desc = -severity_order.get(
                issue.original_issue.severity,
                0
            )
            return (priority_desc, severity_desc)

        return sorted(classified_issues, key=sort_key)

    def suggest_repair_plan(
        self,
        classified_issues: List[ClassifiedIssue]
    ) -> RepairPlan:
        """
        Generate comprehensive repair plan for classified issues.

        Args:
            classified_issues: List of ClassifiedIssue objects

        Returns:
            RepairPlan with grouped issues and recommended repair order
        """
        if not classified_issues:
            return RepairPlan(
                total_issues=0,
                automatic_repairs=0,
                semi_automatic_repairs=0,
                manual_repairs=0,
                total_estimated_time_minutes=0,
                issue_groups={},
                recommended_order=[],
                created_at=datetime.now()
            )

        # Count issues by approach
        automatic_count = sum(
            1 for issue in classified_issues
            if issue.approach == RepairApproach.AUTOMATIC
        )
        semi_auto_count = sum(
            1 for issue in classified_issues
            if issue.approach == RepairApproach.SEMI_AUTOMATIC
        )
        manual_count = sum(
            1 for issue in classified_issues
            if issue.approach == RepairApproach.MANUAL
        )

        # Group issues by repair approach
        issue_groups = {
            "automatic": [
                issue for issue in classified_issues
                if issue.approach == RepairApproach.AUTOMATIC
            ],
            "semi_auto": [
                issue for issue in classified_issues
                if issue.approach == RepairApproach.SEMI_AUTOMATIC
            ],
            "manual": [
                issue for issue in classified_issues
                if issue.approach == RepairApproach.MANUAL
            ]
        }

        # Calculate total estimated time
        total_time = sum(
            issue.estimated_repair_time_minutes
            for issue in classified_issues
        )

        # Determine recommended repair order
        recommended_order = self._determine_repair_order(classified_issues)

        return RepairPlan(
            total_issues=len(classified_issues),
            automatic_repairs=automatic_count,
            semi_automatic_repairs=semi_auto_count,
            manual_repairs=manual_count,
            total_estimated_time_minutes=total_time,
            issue_groups=issue_groups,
            recommended_order=recommended_order,
            created_at=datetime.now()
        )

    def _calculate_priority_score(self, issue: Issue) -> float:
        """
        Calculate priority score using weighted formula.

        Formula: severity_weight × 0.5 + complexity_weight × 0.3 + type_weight × 0.2

        Args:
            issue: The Issue to score

        Returns:
            Priority score from 0.0 to 1.0
        """
        severity_weight = self.SEVERITY_WEIGHTS.get(issue.severity, 0.5)
        complexity = self.CLASSIFICATION_RULES[issue.issue_type]["complexity"]
        complexity_weight = self.COMPLEXITY_WEIGHTS.get(complexity, 0.5)
        type_weight = self.TYPE_WEIGHTS.get(issue.issue_type, 0.5)

        # Apply custom weights if provided
        score = (
            severity_weight * self.priority_weights.get("severity", 0.5) +
            complexity_weight * self.priority_weights.get("complexity", 0.3) +
            type_weight * self.priority_weights.get("type", 0.2)
        )

        # Ensure score is in valid range
        return max(0.0, min(1.0, score))

    def _detect_dependencies(self, issue: Issue) -> List[str]:
        """
        Detect dependencies between issues.

        Rules:
        - ORPHAN_PAGE depends on BROKEN_LINK (fix links first)
        - DUPLICATE_CONTENT depends on CIRCULAR_REF (resolve structure first)
        - METADATA issues are independent

        Args:
            issue: The Issue to check for dependencies

        Returns:
            List of issue IDs this issue depends on
        """
        dependencies = []

        # ORPHAN_PAGE depends on BROKEN_LINK
        if issue.issue_type == IssueType.ORPHAN_PAGE:
            # Would need access to other issues to detect specific dependencies
            # For now, return empty list (would be populated in batch processing)
            pass

        # DUPLICATE_CONTENT depends on CIRCULAR_REF
        if issue.issue_type == IssueType.DUPLICATE_CONTENT:
            # Would need access to other issues to detect specific dependencies
            pass

        return dependencies

    def _determine_repair_order(
        self,
        classified_issues: List[ClassifiedIssue]
    ) -> List[str]:
        """
        Determine recommended repair order considering dependencies and approach.

        Strategy:
        1. Automatic repairs first (fastest, no human intervention)
        2. Semi-automatic repairs (require human review)
        3. Manual repairs (most complex)
        4. Within each group: highest priority first

        Args:
            classified_issues: List of ClassifiedIssue objects

        Returns:
            List of issue IDs in recommended repair order
        """
        # Group by approach
        automatic = [
            issue for issue in classified_issues
            if issue.approach == RepairApproach.AUTOMATIC
        ]
        semi_auto = [
            issue for issue in classified_issues
            if issue.approach == RepairApproach.SEMI_AUTOMATIC
        ]
        manual = [
            issue for issue in classified_issues
            if issue.approach == RepairApproach.MANUAL
        ]

        # Sort each group by priority (descending)
        automatic_sorted = self.prioritize_issues(automatic)
        semi_auto_sorted = self.prioritize_issues(semi_auto)
        manual_sorted = self.prioritize_issues(manual)

        # Combine in order: automatic -> semi_auto -> manual
        ordered_issues = automatic_sorted + semi_auto_sorted + manual_sorted

        # Extract issue IDs
        return [issue.original_issue.id for issue in ordered_issues]
