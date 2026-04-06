"""
Data models for Wiki quality assurance and health monitoring.

This module defines the core data structures used for monitoring Wiki health,
tracking issues, and reporting on quality metrics.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class IssueType(str, Enum):
    """Types of quality issues that can be detected in the Wiki."""
    ORPHAN_PAGE = "orphan_page"
    BROKEN_LINK = "broken_link"
    CIRCULAR_REF = "circular_ref"
    DUPLICATE_CONTENT = "duplicate_content"
    STALE_CONTENT = "stale_content"
    MISSING_METADATA = "missing_metadata"
    LOW_QUALITY = "low_quality"


class IssueSeverity(str, Enum):
    """Severity levels for quality issues."""
    CRITICAL = "critical"  # Data integrity issue
    HIGH = "high"        # Significant quality problem
    MEDIUM = "medium"    # Moderate concern
    LOW = "low"          # Minor issue


class Issue(BaseModel):
    """Represents a quality issue detected in the Wiki."""
    model_config = ConfigDict(use_enum_values=True)

    id: str
    issue_type: IssueType
    severity: IssueSeverity
    page_id: str
    description: str
    detected_at: datetime
    metadata: Dict[str, Any] = {}


class QualityReport(BaseModel):
    """Comprehensive report on Wiki quality metrics."""
    overall_score: float  # 0.0 to 1.0
    page_count: int
    avg_page_quality: float
    completeness_score: float
    freshness_score: float
    metadata_score: float
    issues_found: int
    recommendations: List[str]


class HealthCheckResult(BaseModel):
    """Complete result of a Wiki health check."""
    timestamp: datetime
    consistency_issues: List[Issue]
    quality_report: QualityReport
    staleness_issues: List[Issue]
    total_issues: int
    critical_issues: int
    status: str  # "healthy", "degraded", "unhealthy"
