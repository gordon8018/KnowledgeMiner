"""
Pattern data models.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class PatternType(str, Enum):
    """Types of patterns that can be detected."""
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    EVOLUTIONARY = "evolutionary"
    CONFLICT = "conflict"


@dataclass
class Evidence:
    """Evidence supporting a pattern."""
    source_id: str
    content: str
    confidence: float
    timestamp: Optional[datetime] = None


@dataclass
class Pattern:
    """A detected pattern in the knowledge base."""
    id: str
    pattern_type: PatternType
    title: str
    description: str
    confidence: float  # 0.0-1.0
    evidence: List[Evidence]
    related_concepts: List[str]
    related_patterns: List[str]
    metadata: Dict[str, Any]
    significance_score: float  # 0.0-1.0
    detected_at: datetime

    def __post_init__(self):
        """Validate pattern data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if not 0.0 <= self.significance_score <= 1.0:
            raise ValueError("significance_score must be between 0.0 and 1.0")
