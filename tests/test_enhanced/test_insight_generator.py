"""
Tests for InsightGenerator
"""

import pytest
from src.enhanced.discovery.insight_generator import InsightGenerator
from src.enhanced.models import EnhancedConcept, ConceptType


def test_generate_insights():
    """Test generating insights from concepts"""
    concepts = [
        EnhancedConcept(
            name="Concept1",
            type=ConceptType.ABSTRACT,
            definition="Definition 1",
            relations=["Concept2", "Concept3", "Concept4"]  # 3+ relations to trigger insight
        ),
        EnhancedConcept(
            name="Concept2",
            type=ConceptType.ABSTRACT,
            definition="Definition 2",
            relations=["Concept1"]
        )
    ]

    generator = InsightGenerator()
    insights = generator.generate(concepts)

    assert len(insights) > 0
    # Should generate insight about interconnected concepts
    assert insights[0].result_type.value == "insight"
    assert "Concept1" in insights[0].summary


def test_no_insights_for_few_relations():
    """Test that concepts with fewer than 3 relations don't generate insights"""
    concepts = [
        EnhancedConcept(
            name="Concept1",
            type=ConceptType.ABSTRACT,
            definition="Definition 1",
            relations=["Concept2", "Concept3"]  # Only 2 relations
        ),
        EnhancedConcept(
            name="Concept2",
            type=ConceptType.ABSTRACT,
            definition="Definition 2",
            relations=["Concept1"]
        )
    ]

    generator = InsightGenerator()
    insights = generator.generate(concepts)

    assert len(insights) == 0


def test_multiple_hubs():
    """Test generating insights for multiple hub concepts"""
    concepts = [
        EnhancedConcept(
            name="Hub1",
            type=ConceptType.ABSTRACT,
            definition="Hub 1",
            relations=["A", "B", "C"]  # 3 relations
        ),
        EnhancedConcept(
            name="Hub2",
            type=ConceptType.ABSTRACT,
            definition="Hub 2",
            relations=["D", "E", "F", "G"]  # 4 relations
        ),
        EnhancedConcept(
            name="Leaf",
            type=ConceptType.ABSTRACT,
            definition="Leaf",
            relations=["Hub1"]  # 1 relation
        )
    ]

    generator = InsightGenerator()
    insights = generator.generate(concepts)

    assert len(insights) == 2
    # Check that both hubs are detected
    hub_names = {insight.affected_concepts[0] for insight in insights}
    assert "Hub1" in hub_names
    assert "Hub2" in hub_names


def test_significance_score_calculation():
    """Test that significance score is calculated correctly"""
    concepts = [
        EnhancedConcept(
            name="Hub",
            type=ConceptType.ABSTRACT,
            definition="Hub",
            relations=["A", "B", "C", "D", "E"]  # 5 relations
        )
    ]

    generator = InsightGenerator()
    insights = generator.generate(concepts)

    assert len(insights) == 1
    # Significance should be min(0.9, 5 * 0.2) = min(0.9, 1.0) = 0.9
    assert insights[0].significance_score == 0.9


def test_empty_concepts():
    """Test handling empty concept list"""
    generator = InsightGenerator()
    insights = generator.generate([])

    assert len(insights) == 0
