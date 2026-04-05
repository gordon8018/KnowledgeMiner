"""
Insight data models.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from src.discovery.models.pattern import Evidence


class InsightType(str, Enum):
    """Types of insights."""
    PATTERN = "pattern"
    RELATION = "relation"
    GAP = "gap"
    INTEGRATED = "integrated"


@dataclass
class Insight:
    """An actionable insight derived from knowledge analysis."""
    id: str
    insight_type: InsightType
    title: str
    description: str
    significance: float  # 0.0-1.0
    related_concepts: List[str]
    related_patterns: List[str]
    related_gaps: List[str]
    evidence: List[Evidence]  # Evidence objects
    actionable_suggestions: List[str]
    generated_at: datetime
    metadata: Dict[str, Any]

    def __post_init__(self):
        """Validate insight data."""
        if not 0.0 <= self.significance <= 1.0:
            raise ValueError("significance must be between 0.0 and 1.0")
