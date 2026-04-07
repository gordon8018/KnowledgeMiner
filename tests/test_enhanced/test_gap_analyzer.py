"""
Tests for GapAnalyzer functionality
"""

import pytest
from src.enhanced.discovery.gap_analyzer import GapAnalyzer
from src.enhanced.models import EnhancedConcept, ConceptType, DiscoveryType


def test_analyze_knowledge_gaps():
    """Test analyzing knowledge gaps"""
    concepts = [
        EnhancedConcept(
            name="Concept1",
            type=ConceptType.ABSTRACT,
            definition="Well-defined concept",
            confidence=0.9
        ),
        EnhancedConcept(
            name="Concept2",
            type=ConceptType.ABSTRACT,
            definition="Poorly defined concept",
            confidence=0.3
        )
    ]

    analyzer = GapAnalyzer()
    gaps = analyzer.analyze(concepts)

    assert len(gaps) > 0
    # Should detect that Concept2 has low confidence (knowledge gap)
    gap_concepts = [gap.affected_concepts[0] for gap in gaps]
    assert "Concept2" in gap_concepts


def test_analyze_missing_evidence():
    """Test detecting concepts with no evidence"""
    concepts = [
        EnhancedConcept(
            name="ConceptWithEvidence",
            type=ConceptType.ABSTRACT,
            definition="Concept with evidence",
            confidence=0.8
        ),
        EnhancedConcept(
            name="ConceptWithoutEvidence",
            type=ConceptType.ABSTRACT,
            definition="Concept without evidence",
            confidence=0.7
        )
    ]

    # Add evidence to first concept
    concepts[0].add_evidence("source1", "quote1", 0.9)

    analyzer = GapAnalyzer()
    gaps = analyzer.analyze(concepts)

    # Should detect that ConceptWithoutEvidence has no supporting evidence
    gap_summaries = [gap.summary for gap in gaps]
    assert any("ConceptWithoutEvidence" in summary and "no supporting evidence" in summary.lower()
               for summary in gap_summaries)


def test_analyze_multiple_gaps():
    """Test detecting multiple types of gaps"""
    concepts = [
        EnhancedConcept(
            name="HighConfidenceWithEvidence",
            type=ConceptType.ABSTRACT,
            definition="Good concept",
            confidence=0.9
        ),
        EnhancedConcept(
            name="LowConfidenceNoEvidence",
            type=ConceptType.ABSTRACT,
            definition="Bad concept",
            confidence=0.2
        )
    ]

    # Add evidence only to first concept
    concepts[0].add_evidence("source1", "quote1", 0.9)

    analyzer = GapAnalyzer()
    gaps = analyzer.analyze(concepts)

    # Should detect both low confidence and missing evidence for second concept
    low_confidence_gaps = [g for g in gaps if "low confidence" in g.summary.lower()]
    missing_evidence_gaps = [g for g in gaps if "no supporting evidence" in g.summary.lower()]

    assert len(low_confidence_gaps) > 0
    assert len(missing_evidence_gaps) > 0


def test_analyze_empty_concepts():
    """Test analyzing empty concept list"""
    concepts = []

    analyzer = GapAnalyzer()
    gaps = analyzer.analyze(concepts)

    assert len(gaps) == 0


def test_gap_significance_scoring():
    """Test that gaps are scored appropriately"""
    concepts = [
        EnhancedConcept(
            name="VeryLowConfidence",
            type=ConceptType.ABSTRACT,
            definition="Very uncertain",
            confidence=0.1
        ),
        EnhancedConcept(
            name="ModeratelyLowConfidence",
            type=ConceptType.ABSTRACT,
            definition="Somewhat uncertain",
            confidence=0.4
        )
    ]

    analyzer = GapAnalyzer()
    gaps = analyzer.analyze(concepts)

    # Very low confidence should have higher significance score
    very_low_gap = next((g for g in gaps if "VeryLowConfidence" in g.affected_concepts), None)
    moderately_low_gap = next((g for g in gaps if "ModeratelyLowConfidence" in g.affected_concepts), None)

    assert very_low_gap is not None
    assert moderately_low_gap is not None
    assert very_low_gap.significance_score > moderately_low_gap.significance_score


def test_all_gaps_have_correct_type():
    """Test that all returned results have type GAP"""
    concepts = [
        EnhancedConcept(
            name="TestConcept",
            type=ConceptType.ABSTRACT,
            definition="Test",
            confidence=0.3
        )
    ]

    analyzer = GapAnalyzer()
    gaps = analyzer.analyze(concepts)

    for gap in gaps:
        assert gap.result_type == DiscoveryType.GAP


def test_gap_confidence_scores():
    """Test that gaps have reasonable confidence scores"""
    concepts = [
        EnhancedConcept(
            name="LowConfidenceConcept",
            type=ConceptType.ABSTRACT,
            definition="Test",
            confidence=0.2
        )
    ]

    analyzer = GapAnalyzer()
    gaps = analyzer.analyze(concepts)

    for gap in gaps:
        assert 0.0 <= gap.confidence <= 1.0
        assert gap.confidence > 0.5  # Gap detection should be confident
