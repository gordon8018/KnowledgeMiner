"""
Insight generation functionality
"""

from typing import List
from src.enhanced.models import EnhancedConcept, DiscoveryResult, DiscoveryType


class InsightGenerator:
    """
    Generates insights from concept relationships
    """

    def generate(self, concepts: List[EnhancedConcept]) -> List[DiscoveryResult]:
        """
        Generate insights from concepts

        Args:
            concepts: List of EnhancedConcept instances

        Returns:
            List of DiscoveryResult instances with type INSIGHT
        """
        results = []

        # Find highly connected concepts (hubs)
        for concept in concepts:
            if len(concept.relations) >= 3:
                result = DiscoveryResult(
                    result_type=DiscoveryType.INSIGHT,
                    summary=f"Insight: '{concept.name}' is a central concept connected to {len(concept.relations)} other concepts",
                    significance_score=min(0.9, len(concept.relations) * 0.2),
                    confidence=0.7,
                    affected_concepts=[concept.name] + concept.relations
                )

                results.append(result)

        return results
