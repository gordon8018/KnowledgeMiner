import pytest
from src.enhanced.discovery.pattern_detector import PatternDetector
from src.enhanced.models import EnhancedConcept, ConceptType

def test_detect_recurring_patterns():
    """Test detecting recurring patterns in concepts"""
    concepts = [
        EnhancedConcept(
            name="Concept1",
            type=ConceptType.ABSTRACT,
            definition="Pattern A appears in context X",
            properties={"pattern": "A"}
        ),
        EnhancedConcept(
            name="Concept2",
            type=ConceptType.ABSTRACT,
            definition="Pattern A appears in context Y",
            properties={"pattern": "A"}
        )
    ]

    detector = PatternDetector()
    patterns = detector.detect(concepts)

    assert len(patterns) > 0
    # Should detect that pattern "A" appears in both concepts
