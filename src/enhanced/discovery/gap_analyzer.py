"""
Knowledge gap analysis functionality
"""

from typing import List
from src.enhanced.models import EnhancedConcept, DiscoveryResult, DiscoveryType


class GapAnalyzer:
    """
    Analyzes concepts to identify knowledge gaps

    This analyzer examines concepts to detect potential knowledge gaps including:
    - Low confidence concepts (uncertain knowledge)
    - Concepts without supporting evidence
    """

    def analyze(self, concepts: List[EnhancedConcept]) -> List[DiscoveryResult]:
        """
        Analyze concepts for knowledge gaps

        Args:
            concepts: List of EnhancedConcept instances

        Returns:
            List of DiscoveryResult instances with type GAP
        """
        results = []

        for concept in concepts:
            # Low confidence indicates potential knowledge gap
            if concept.confidence < 0.5:
                result = DiscoveryResult(
                    result_type=DiscoveryType.GAP,
                    summary=f"Knowledge gap: '{concept.name}' has low confidence ({concept.confidence})",
                    significance_score=1.0 - concept.confidence,
                    confidence=0.8,
                    affected_concepts=[concept.name]
                )

                results.append(result)

            # Missing evidence
            if len(concept.evidence) == 0:
                result = DiscoveryResult(
                    result_type=DiscoveryType.GAP,
                    summary=f"Knowledge gap: '{concept.name}' has no supporting evidence",
                    significance_score=0.7,
                    confidence=0.9,
                    affected_concepts=[concept.name]
                )

                results.append(result)

        return results
