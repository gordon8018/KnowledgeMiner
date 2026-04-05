"""
Discovery result data model.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any

from src.discovery.models.pattern import Pattern
from src.discovery.models.gap import KnowledgeGap
from src.discovery.models.insight import Insight
from src.core.relation_model import Relation


@dataclass
class DiscoveryResult:
    """Result of knowledge discovery process."""
    relations: List[Relation]
    patterns: List[Pattern]
    gaps: List[KnowledgeGap]
    insights: List[Insight]
    statistics: Dict[str, Any]
    generated_at: datetime

    def __post_init__(self):
        """Compute statistics if not provided."""
        if not self.statistics:
            self.statistics = {
                'total_relations': len(self.relations),
                'total_patterns': len(self.patterns),
                'total_gaps': len(self.gaps),
                'total_insights': len(self.insights),
                'avg_insight_significance': sum(
                    i.significance for i in self.insights
                ) / len(self.insights) if self.insights else 0.0
            }
