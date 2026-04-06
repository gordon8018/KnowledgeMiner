"""
Tests for InsightPropagator.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from src.discovery.models.insight import Insight, InsightType
from src.discovery.models.pattern import Evidence
from src.wiki.insight.propagator import InsightPropagator


@pytest.fixture
def mock_wiki_core():
    """Create a mock WikiCore."""
    wiki_core = Mock()
    return wiki_core


@pytest.fixture
def sample_insight():
    """Create a sample insight for testing."""
    return Insight(
        id="test-insight",
        insight_type=InsightType.PATTERN,
        title="Test Pattern",
        description="A test pattern",
        significance=0.8,
        related_concepts=["SourceConcept"],
        related_patterns=["pattern-1"],
        related_gaps=[],
        evidence=[
            Evidence(
                source_id="doc-1",
                content="Test evidence",
                confidence=0.8
            )
        ],
        actionable_suggestions=["Test action"],
        generated_at=datetime.now(),
        metadata={}
    )


def test_direct_propagation(mock_wiki_core, sample_insight):
    """Test direct propagation (1 hop)."""
    # Setup: SourceConcept has one direct relation
    def get_related(concept):
        relations = {
            "SourceConcept": ["RelatedConcept1"],
            "RelatedConcept1": []
        }
        return relations.get(concept, [])

    mock_wiki_core.get_related_concepts.side_effect = get_related

    propagator = InsightPropagator(mock_wiki_core)
    results = propagator.propagate(sample_insight, max_hops=1)

    assert len(results) == 1
    assert results[0]["concept"] == "RelatedConcept1"
    assert results[0]["path"] == ["SourceConcept", "RelatedConcept1"]
    assert results[0]["hops"] == 1
    assert results[0]["insight_id"] == "test-insight"


def test_two_hop_propagation(mock_wiki_core, sample_insight):
    """Test two-hop propagation (2 hops)."""
    # Setup: SourceConcept -> RelatedConcept1 -> RelatedConcept2
    def get_related(concept):
        relations = {
            "SourceConcept": ["RelatedConcept1"],
            "RelatedConcept1": ["RelatedConcept2"],
            "RelatedConcept2": []
        }
        return relations.get(concept, [])

    mock_wiki_core.get_related_concepts.side_effect = get_related

    propagator = InsightPropagator(mock_wiki_core)
    results = propagator.propagate(sample_insight, max_hops=2)

    assert len(results) == 2

    # Check first hop
    result1 = next(r for r in results if r["concept"] == "RelatedConcept1")
    assert result1["path"] == ["SourceConcept", "RelatedConcept1"]
    assert result1["hops"] == 1

    # Check second hop
    result2 = next(r for r in results if r["concept"] == "RelatedConcept2")
    assert result2["path"] == ["SourceConcept", "RelatedConcept1", "RelatedConcept2"]
    assert result2["hops"] == 2


def test_cycle_detection(mock_wiki_core, sample_insight):
    """Test that cycles are detected and avoided."""
    # Setup: SourceConcept -> A -> B -> A (cycle back)
    def get_related(concept):
        relations = {
            "SourceConcept": ["ConceptA"],
            "ConceptA": ["ConceptB"],
            "ConceptB": ["ConceptA"],  # Creates cycle: A -> B -> A
            "ConceptC": []
        }
        return relations.get(concept, [])

    mock_wiki_core.get_related_concepts.side_effect = get_related

    propagator = InsightPropagator(mock_wiki_core)
    results = propagator.propagate(sample_insight, max_hops=5)

    # Should find ConceptA (hop 1) and ConceptB (hop 2)
    # But should NOT revisit ConceptA from ConceptB (cycle detection)
    assert len(results) == 2

    concepts_found = [r["concept"] for r in results]
    assert "ConceptA" in concepts_found
    assert "ConceptB" in concepts_found

    # Verify no duplicates
    assert len(concepts_found) == len(set(concepts_found))


def test_max_hops_limit(mock_wiki_core, sample_insight):
    """Test that max_hops limit is enforced."""
    # Setup: Chain longer than max_hops
    def get_related(concept):
        relations = {
            "SourceConcept": ["Concept1"],
            "Concept1": ["Concept2"],
            "Concept2": ["Concept3"],
            "Concept3": ["Concept4"],
            "Concept4": []
        }
        return relations.get(concept, [])

    mock_wiki_core.get_related_concepts.side_effect = get_related

    propagator = InsightPropagator(mock_wiki_core)
    results = propagator.propagate(sample_insight, max_hops=2)

    # Should only reach Concept2 (2 hops), not Concept3 or Concept4
    assert len(results) == 2
    assert results[0]["hops"] <= 2
    assert results[1]["hops"] <= 2

    concepts_found = [r["concept"] for r in results]
    assert "Concept1" in concepts_found
    assert "Concept2" in concepts_found
    assert "Concept3" not in concepts_found
    assert "Concept4" not in concepts_found


def test_empty_related_concepts(mock_wiki_core):
    """Test propagation with insight that has no related concepts."""
    # Create insight with empty related_concepts
    insight = Insight(
        id="empty-insight",
        insight_type=InsightType.PATTERN,
        title="Empty Insight",
        description="Insight with no related concepts",
        significance=0.5,
        related_concepts=[],  # Empty!
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    mock_wiki_core.get_related_concepts.return_value = []

    propagator = InsightPropagator(mock_wiki_core)
    results = propagator.propagate(insight, max_hops=2)

    # Should return empty list
    assert len(results) == 0


def test_multiple_starting_concepts(mock_wiki_core):
    """Test propagation from multiple starting concepts."""
    # Create insight with multiple related_concepts
    insight = Insight(
        id="multi-source-insight",
        insight_type=InsightType.PATTERN,
        title="Multi-Source Insight",
        description="Insight with multiple source concepts",
        significance=0.7,
        related_concepts=["Source1", "Source2"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Setup: Each source has its own related concepts
    def get_related(concept):
        relations = {
            "Source1": ["Related1A", "Related1B"],
            "Source2": ["Related2A"],
            "Related1A": [],
            "Related1B": [],
            "Related2A": []
        }
        return relations.get(concept, [])

    mock_wiki_core.get_related_concepts.side_effect = get_related

    propagator = InsightPropagator(mock_wiki_core)
    results = propagator.propagate(insight, max_hops=1)

    # Should find all 3 direct relations
    assert len(results) == 3

    concepts_found = [r["concept"] for r in results]
    assert "Related1A" in concepts_found
    assert "Related1B" in concepts_found
    assert "Related2A" in concepts_found

    # Verify paths start from correct sources
    for result in results:
        if result["concept"] in ["Related1A", "Related1B"]:
            assert result["path"][0] == "Source1"
        elif result["concept"] == "Related2A":
            assert result["path"][0] == "Source2"


def test_complex_graph_with_branching(mock_wiki_core, sample_insight):
    """Test propagation in a complex graph with branching paths."""
    # Setup: SourceConcept -> A, B
    #        A -> C, D
    #        B -> E
    def get_related(concept):
        relations = {
            "SourceConcept": ["ConceptA", "ConceptB"],
            "ConceptA": ["ConceptC", "ConceptD"],
            "ConceptB": ["ConceptE"],
            "ConceptC": [],
            "ConceptD": [],
            "ConceptE": []
        }
        return relations.get(concept, [])

    mock_wiki_core.get_related_concepts.side_effect = get_related

    propagator = InsightPropagator(mock_wiki_core)
    results = propagator.propagate(sample_insight, max_hops=2)

    # Should find: A, B (hop 1), C, D, E (hop 2)
    assert len(results) == 5

    # Check hop counts
    hop_1_concepts = [r["concept"] for r in results if r["hops"] == 1]
    hop_2_concepts = [r["concept"] for r in results if r["hops"] == 2]

    assert "ConceptA" in hop_1_concepts
    assert "ConceptB" in hop_1_concepts
    assert "ConceptC" in hop_2_concepts
    assert "ConceptD" in hop_2_concepts
    assert "ConceptE" in hop_2_concepts
