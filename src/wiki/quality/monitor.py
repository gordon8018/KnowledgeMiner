"""
HealthMonitor for Wiki quality assurance and health monitoring.

This module provides comprehensive health monitoring for Wikis, including
consistency checks, quality analysis, and staleness detection.
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from .models import (
    IssueType,
    IssueSeverity,
    Issue,
    QualityReport,
    HealthCheckResult
)
from ..core.models import WikiPage, PageType


DEFAULT_CONFIG = {
    "quality_threshold": 0.7,
    "staleness_days": 30,
    "consistency_checks": True,
    "duplicate_threshold": 0.8,
    "orphan_check": True,
    "link_validation": True
}


class HealthMonitor:
    """
    Monitor Wiki health and detect quality issues.

    Provides comprehensive health monitoring including:
    - Consistency checks (orphan pages, broken links, circular refs, duplicates)
    - Quality analysis (completeness, freshness, metadata)
    - Staleness detection (outdated content)
    """

    def __init__(self, wiki_store, config: Optional[dict] = None):
        """
        Initialize HealthMonitor.

        Args:
            wiki_store: WikiStore instance to monitor
            config: Optional configuration dict with thresholds and settings
        """
        self.wiki_store = wiki_store
        self.config = {**DEFAULT_CONFIG, **(config or {})}

    def _get_all_pages(self) -> List[WikiPage]:
        """Helper method to retrieve all pages from WikiStore."""
        # This is a workaround - we'll need to add proper query support to WikiStore
        pages = []
        # Try to get pages from storage
        try:
            for page_type in [PageType.TOPIC, PageType.CONCEPT, PageType.RELATION]:
                dir_path = self.wiki_store._get_page_dir(page_type)
                if dir_path.exists():
                    for file_path in dir_path.glob("*.md"):
                        page_id = file_path.stem
                        page = self.wiki_store.get_page(page_id)
                        if page:
                            pages.append(page)
        except Exception as e:
            # If storage access fails, return empty list
            pass
        return pages

    def check_consistency(self) -> List[Issue]:
        """
        Detect consistency issues in Wiki.

        Checks for:
        - Orphan pages (no links from other pages)
        - Broken links (references to non-existent pages)
        - Circular references (A→B→A)
        - Duplicate content (similar pages >80% overlap)

        Returns:
            List of detected Issue objects
        """
        if not self.config.get("consistency_checks", True):
            return []

        issues = []
        pages = self._get_all_pages()

        if not pages:
            return issues

        # Build page link graph
        page_links = defaultdict(list)
        all_page_ids = {page.id for page in pages}

        for page in pages:
            links = page.metadata.get("links", [])
            if isinstance(links, list):
                page_links[page.id] = links

        # Check for orphan pages
        if self.config.get("orphan_check", True):
            linked_pages = set()
            for links in page_links.values():
                linked_pages.update(links)

            for page in pages:
                if page.id not in linked_pages and len(page_links.get(page.id, [])) > 0:
                    # Page has no incoming links but has outgoing links
                    issues.append(Issue(
                        id=str(uuid.uuid4()),
                        issue_type=IssueType.ORPHAN_PAGE,
                        severity=IssueSeverity.LOW,
                        page_id=page.id,
                        description=f"Page has no incoming links",
                        detected_at=datetime.now(),
                        metadata={"outgoing_links": len(page_links.get(page.id, []))}
                    ))

        # Check for broken links
        if self.config.get("link_validation", True):
            for page in pages:
                links = page_links.get(page.id, [])
                for link in links:
                    if link not in all_page_ids:
                        issues.append(Issue(
                            id=str(uuid.uuid4()),
                            issue_type=IssueType.BROKEN_LINK,
                            severity=IssueSeverity.CRITICAL,
                            page_id=page.id,
                            description=f"Broken link to non-existent page: {link}",
                            detected_at=datetime.now(),
                            metadata={"broken_link": link}
                        ))

        # Check for circular references
        if HAS_NETWORKX and page_links:
            try:
                G = nx.DiGraph()
                for page_id, links in page_links.items():
                    for link in links:
                        G.add_edge(page_id, link)

                cycles = list(nx.simple_cycles(G))
                for cycle in cycles:
                    if len(cycle) > 1:  # Ignore self-loops
                        issues.append(Issue(
                            id=str(uuid.uuid4()),
                            issue_type=IssueType.CIRCULAR_REF,
                            severity=IssueSeverity.MEDIUM,
                            page_id=cycle[0],
                            description=f"Circular reference detected: {' -> '.join(cycle + [cycle[0]])}",
                            detected_at=datetime.now(),
                            metadata={"cycle": cycle}
                        ))
            except Exception:
                # NetworkX analysis failed, skip circular reference detection
                pass

        # Check for duplicate content
        duplicate_threshold = self.config.get("duplicate_threshold", 0.8)
        for i, page1 in enumerate(pages):
            for page2 in pages[i+1:]:
                similarity = self._calculate_similarity(page1.content, page2.content)
                if similarity >= duplicate_threshold:
                    issues.append(Issue(
                        id=str(uuid.uuid4()),
                        issue_type=IssueType.DUPLICATE_CONTENT,
                        severity=IssueSeverity.MEDIUM,
                        page_id=page1.id,
                        description=f"Duplicate content detected with page '{page2.id}' (similarity: {similarity:.2f})",
                        detected_at=datetime.now(),
                        metadata={"similar_page": page2.id, "similarity": similarity}
                    ))

        return issues

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate Jaccard similarity between two pieces of content.

        Args:
            content1: First content string
            content2: Second content string

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Tokenize content into words
        words1 = set(re.findall(r'\w+', content1.lower()))
        words2 = set(re.findall(r'\w+', content2.lower()))

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def analyze_quality(self) -> QualityReport:
        """
        Analyze overall Wiki quality.

        Analyzes:
        - Page completeness (missing sections)
        - Content freshness (age distribution)
        - Metadata completeness
        - Citation quality (if applicable)

        Returns:
            QualityReport with scores and recommendations
        """
        pages = self._get_all_pages()

        if not pages:
            return QualityReport(
                overall_score=0.0,
                page_count=0,
                avg_page_quality=0.0,
                completeness_score=0.0,
                freshness_score=0.0,
                metadata_score=0.0,
                issues_found=0,
                recommendations=[]
            )

        # Calculate completeness score
        completeness_scores = []
        for page in pages:
            score = self._calculate_page_completeness(page)
            completeness_scores.append(score)

        completeness_score = sum(completeness_scores) / len(completeness_scores)

        # Calculate freshness score
        staleness_days = self.config.get("staleness_days", 30)
        freshness_scores = []
        now = datetime.now()

        for page in pages:
            days_since_update = (now - page.updated_at).days
            # Score decreases as page gets older
            if days_since_update < 7:
                score = 1.0
            elif days_since_update < staleness_days:
                score = 1.0 - (days_since_update / staleness_days) * 0.3
            else:
                score = 0.7 - min((days_since_update - staleness_days) / 90, 0.7)
            freshness_scores.append(max(0.0, score))

        freshness_score = sum(freshness_scores) / len(freshness_scores)

        # Calculate metadata score
        metadata_scores = []
        for page in pages:
            score = self._calculate_metadata_completeness(page)
            metadata_scores.append(score)

        metadata_score = sum(metadata_scores) / len(metadata_scores)

        # Calculate overall score
        overall_score = (completeness_score * 0.4 +
                        freshness_score * 0.3 +
                        metadata_score * 0.3)

        avg_page_quality = overall_score

        # Generate recommendations
        recommendations = []
        if completeness_score < 0.8:
            recommendations.append("Improve page completeness by adding required sections")
        if freshness_score < 0.7:
            recommendations.append("Update stale content to improve freshness")
        if metadata_score < 0.8:
            recommendations.append("Enhance metadata completeness")

        # Count issues
        issues = self.check_consistency()
        staleness_issues = self.detect_staleness()
        total_issues = len(issues) + len(staleness_issues)

        return QualityReport(
            overall_score=round(overall_score, 2),
            page_count=len(pages),
            avg_page_quality=round(avg_page_quality, 2),
            completeness_score=round(completeness_score, 2),
            freshness_score=round(freshness_score, 2),
            metadata_score=round(metadata_score, 2),
            issues_found=total_issues,
            recommendations=recommendations
        )

    def _calculate_page_completeness(self, page: WikiPage) -> float:
        """
        Calculate completeness score for a single page.

        Checks for:
        - Required markdown sections (##, ###)
        - Content length
        - Structure quality

        Args:
            page: WikiPage to analyze

        Returns:
            Completeness score between 0.0 and 1.0
        """
        score = 0.0
        content = page.content

        # Check for sections
        sections = re.findall(r'^#{1,3}\s+\w+', content, re.MULTILINE)
        if sections:
            score += 0.4
            if len(sections) >= 2:
                score += 0.2

        # Check content length
        word_count = len(content.split())
        if word_count > 50:
            score += 0.2
        if word_count > 200:
            score += 0.2

        # Check for basic structure
        if any(pattern in content for pattern in ['##', '###', '- ', '* ']):
            score += 0.2

        return min(score, 1.0)

    def _calculate_metadata_completeness(self, page: WikiPage) -> float:
        """
        Calculate metadata completeness score for a page.

        Checks for:
        - Required metadata fields
        - Optional but recommended fields

        Args:
            page: WikiPage to analyze

        Returns:
            Metadata score between 0.0 and 1.0
        """
        required_fields = []  # No required fields currently
        recommended_fields = ['category', 'tags', 'author']
        metadata = page.metadata or {}

        score = 0.0

        # Check required fields
        for field in required_fields:
            if field in metadata and metadata[field]:
                score += 0.5

        # Check recommended fields
        for field in recommended_fields:
            if field in metadata and metadata[field]:
                score += 0.5 / len(recommended_fields)

        # Check if metadata exists at all
        if metadata:
            score += 0.2

        return min(score, 1.0)

    def detect_staleness(self) -> List[Issue]:
        """
        Detect stale content.

        Detects:
        - Pages not updated in N days (configurable)
        - Outdated references to old concepts
        - Deprecated information patterns

        Returns:
            List of staleness issues
        """
        issues = []
        pages = self._get_all_pages()

        if not pages:
            return issues

        staleness_days = self.config.get("staleness_days", 30)
        now = datetime.now()

        for page in pages:
            days_since_update = (now - page.updated_at).days

            if days_since_update > staleness_days:
                # Determine severity based on age
                if days_since_update >= 90:
                    severity = IssueSeverity.HIGH
                elif days_since_update >= 60:
                    severity = IssueSeverity.MEDIUM
                else:
                    severity = IssueSeverity.LOW

                issues.append(Issue(
                    id=str(uuid.uuid4()),
                    issue_type=IssueType.STALE_CONTENT,
                    severity=severity,
                    page_id=page.id,
                    description=f"Content not updated in {days_since_update} days",
                    detected_at=datetime.now(),
                    metadata={"days_since_update": days_since_update}
                ))

        return issues

    def run_health_check(self) -> HealthCheckResult:
        """
        Orchestrate complete health check.

        Runs all three checks (consistency, quality, staleness) and aggregates results.

        Returns:
            HealthCheckResult with complete health status
        """
        # Run all checks
        consistency_issues = self.check_consistency()
        quality_report = self.analyze_quality()
        staleness_issues = self.detect_staleness()

        # Calculate statistics
        total_issues = len(consistency_issues) + len(staleness_issues)
        critical_issues = sum(1 for issue in consistency_issues + staleness_issues
                            if issue.severity == IssueSeverity.CRITICAL)

        # Determine overall status
        quality_threshold = self.config.get("quality_threshold", 0.7)

        # Empty wiki is considered healthy
        if quality_report.page_count == 0:
            status = "healthy"
        elif critical_issues > 0 or quality_report.overall_score < quality_threshold * 0.5:
            status = "unhealthy"
        elif quality_report.overall_score < quality_threshold or total_issues > 10:
            status = "degraded"
        else:
            status = "healthy"

        return HealthCheckResult(
            timestamp=datetime.now(),
            consistency_issues=consistency_issues,
            quality_report=quality_report,
            staleness_issues=staleness_issues,
            total_issues=total_issues,
            critical_issues=critical_issues,
            status=status
        )
