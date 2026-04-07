"""
Pattern detection functionality
"""

from collections import Counter
from typing import List
from src.enhanced.models import EnhancedConcept, DiscoveryResult, DiscoveryType


class PatternDetector:
    """
    Detects recurring patterns across concepts
    """

    def detect(self, concepts: List[EnhancedConcept]) -> List[DiscoveryResult]:
        """
        Detect patterns in a list of concepts

        Args:
            concepts: List of EnhancedConcept instances

        Returns:
            List of DiscoveryResult instances with type PATTERN
        """
        results = []

        # Look for recurring patterns in properties
        pattern_counter = Counter()

        for concept in concepts:
            if "pattern" in concept.properties:
                pattern = concept.properties["pattern"]
                pattern_counter[pattern] += 1

        # Find patterns that appear multiple times
        for pattern, count in pattern_counter.items():
            if count >= 2:  # Pattern appears at least twice
                result = DiscoveryResult(
                    result_type=DiscoveryType.PATTERN,
                    summary=f"Recurring pattern '{pattern}' found in {count} concepts",
                    significance_score=min(0.9, count * 0.3),
                    confidence=0.7,
                    affected_concepts=[c.name for c in concepts if "pattern" in c.properties and c.properties["pattern"] == pattern]
                )

                results.append(result)

        return results
