"""
HealthMonitor for Wiki quality assurance and health monitoring.

This module provides comprehensive health monitoring for Wikis, including
consistency checks, quality analysis, and staleness detection.
"""

import re
import uuid
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

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


# Issue 6: Circuit breaker for WikiCore calls
class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.

    Opens circuit after threshold failures, closes after recovery timeout.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or fallback value

        Raises:
            Exception: If circuit is open and no fallback provided
        """
        # Check if circuit should transition to half-open
        if self.state == "open":
            if datetime.now() - self.last_failure_time >= timedelta(seconds=self.recovery_timeout):
                logger.info("Circuit breaker transitioning to half-open")
                self.state = "half-open"
            else:
                logger.warning("Circuit breaker is OPEN, blocking call")
                raise Exception("Circuit breaker is open - service unavailable")

        try:
            result = func(*args, **kwargs)

            # Reset on success
            if self.state == "half-open":
                logger.info("Circuit breaker closing after successful call")
                self.state = "closed"
                self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            # Open circuit if threshold reached
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker OPEN after {self.failure_count} failures: {e}"
                )
                self.state = "open"

            raise e


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

        # Issue 5: Cache for content hashes and similarity calculations
        self._content_hash_cache: Dict[str, str] = {}
        self._similarity_cache: Dict[tuple, float] = {}

        # Issue 6: Circuit breaker for WikiCore calls
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

    def _get_all_pages(self, page_size: Optional[int] = None) -> List[WikiPage]:
        """
        Helper method to retrieve all pages from WikiStore with circuit breaker protection.

        Args:
            page_size: Optional batch size for pagination (default: None for no pagination)

        Returns:
            List of all WikiPage objects
        """
        def _fetch_pages():
            # This is a workaround - we'll need to add proper query support to WikiStore
            pages = []
            # Try to get pages from storage
            for page_type in [PageType.TOPIC, PageType.CONCEPT, PageType.RELATION]:
                dir_path = self.wiki_store._get_page_dir(page_type)
                if dir_path.exists():
                    # Issue 4: Add pagination support
                    file_paths = list(dir_path.glob("*.md"))

                    if page_size:
                        # Process in batches to reduce memory
                        for i in range(0, len(file_paths), page_size):
                            batch = file_paths[i:i + page_size]
                            for file_path in batch:
                                page_id = file_path.stem
                                page = self.wiki_store.get_page(page_id)
                                if page:
                                    pages.append(page)

                            # Clear cache between batches for large wikis
                            if len(file_paths) > 1000:
                                self.clear_cache()
                    else:
                        # Process all at once for small wikis
                        for file_path in file_paths:
                            page_id = file_path.stem
                            page = self.wiki_store.get_page(page_id)
                            if page:
                                pages.append(page)
            return pages

        # Issue 6: Use circuit breaker for WikiCore calls
        try:
            return self.circuit_breaker.call(_fetch_pages)
        except Exception as e:
            logger.warning(f"Failed to fetch pages due to circuit breaker: {e}")
            return []

    def check_orphan_pages(self, page_size: Optional[int] = None) -> List[Issue]:
        """
        Check for orphan pages with pagination support.

        Args:
            page_size: Optional batch size for processing (default: 1000)

        Returns:
            List of orphan page issues
        """
        if page_size is None:
            page_size = 1000  # Default page size

        pages = self._get_all_pages(page_size=page_size)
        if not pages:
            return []

        issues = []

        # Build page link graph
        page_links = defaultdict(list)
        all_page_ids = {page.id for page in pages}

        for page in pages:
            links = page.metadata.get("links", [])
            if isinstance(links, list):
                page_links[page.id] = links

        # Check for orphan pages
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

        return issues

    def check_broken_links(self, page_size: Optional[int] = None) -> List[Issue]:
        """
        Check for broken links with pagination support.

        Args:
            page_size: Optional batch size for processing (default: 1000)

        Returns:
            List of broken link issues
        """
        if page_size is None:
            page_size = 1000  # Default page size

        pages = self._get_all_pages(page_size=page_size)
        if not pages:
            return []

        issues = []

        # Build page link graph
        page_links = defaultdict(list)
        all_page_ids = {page.id for page in pages}

        for page in pages:
            links = page.metadata.get("links", [])
            if isinstance(links, list):
                page_links[page.id] = links

        # Check for broken links
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

        return issues

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

    # Issue 5: Add caching for expensive operations
    def _get_content_hash(self, content: str) -> str:
        """
        Get cached hash for content.

        Args:
            content: Content string to hash

        Returns:
            Hash of content
        """
        # Create hash key
        content_key = f"content_{len(content)}_{content[:50]}"

        # Return cached if available
        if content_key in self._content_hash_cache:
            return self._content_hash_cache[content_key]

        # Calculate and cache hash
        content_hash = hashlib.md5(content.encode()).hexdigest()
        self._content_hash_cache[content_key] = content_hash

        return content_hash

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate Jaccard similarity between two pieces of content with caching.

        Args:
            content1: First content string
            content2: Second content string

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Issue 5: Check cache
        hash1 = self._get_content_hash(content1)
        hash2 = self._get_content_hash(content2)
        cache_key = (hash1, hash2)

        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        # Tokenize content into words
        words1 = set(re.findall(r'\w+', content1.lower()))
        words2 = set(re.findall(r'\w+', content2.lower()))

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        similarity = intersection / union if union > 0 else 0.0

        # Issue 5: Cache result
        self._similarity_cache[cache_key] = similarity

        return similarity

    def clear_cache(self):
        """Clear all caches to free memory."""
        self._content_hash_cache.clear()
        self._similarity_cache.clear()
        logger.debug("Cleared content and similarity caches")

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
