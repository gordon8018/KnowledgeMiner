"""
Knowledge gap data models.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any


class GapType(str, Enum):
    """Types of knowledge gaps."""
    MISSING_CONCEPT = "missing_concept"
    MISSING_RELATION = "missing_relation"
    WEAK_EVIDENCE = "weak_evidence"
    COVERAGE_GAP = "coverage_gap"


@dataclass
class KnowledgeGap:
    """A gap in the knowledge base."""
    id: str
    gap_type: GapType
    description: str
    severity: float  # 0.0-1.0
    affected_concepts: List[str]
    affected_relations: List[str]
    suggested_actions: List[str]
    priority: int  # 1-10
    estimated_effort: str  # "low", "medium", "high"
    metadata: Dict[str, Any]
    detected_at: datetime

    def __post_init__(self):
        """Validate gap data."""
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("severity must be between 0.0 and 1.0")
        if not 1 <= self.priority <= 10:
            raise ValueError("priority must be between 1 and 10")
        if self.estimated_effort not in ["low", "medium", "high"]:
            raise ValueError("estimated_effort must be 'low', 'medium', or 'high'")
