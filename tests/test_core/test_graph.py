"""Tests for KnowledgeGraph using NetworkX."""

import pytest
from src.wiki.core.graph import KnowledgeGraph
from src.core.relation_model import Relation, RelationType


@pytest.fixture
def sample_relations():
    """Create sample relations for testing."""
    return [
        Relation(
            id="rel_1",
            source_concept="A",
            target_concept="B",
            relation_type=RelationType.CAUSES,
            strength=0.8,
            confidence=0.9
        ),
        Relation(
            id="rel_2",
            source_concept="B",
            target_concept="C",
            relation_type=RelationType.ENABLES,
            strength=0.7,
            confidence=0.8
        ),
        Relation(
            id="rel_3",
            source_concept="A",
            target_concept="C",
            relation_type=RelationType.RELATED_TO,
            strength=0.5,
            confidence=0.7
        )
    ]


def test_graph_initialization():
    """Test graph initialization."""
    graph = KnowledgeGraph()
    assert graph.graph is not None
    assert graph.graph.number_of_nodes() == 0
    assert graph.graph.number_of_edges() == 0


def test_add_relations(sample_relations):
    """Test adding relations to graph."""
    graph = KnowledgeGraph()
    graph.add_relations(sample_relations)

    assert graph.graph.number_of_nodes() == 3
    assert graph.graph.number_of_edges() == 3


def test_get_related_concepts(sample_relations):
    """Test getting related concepts."""
    graph = KnowledgeGraph()
    graph.add_relations(sample_relations)

    related = graph.get_related_concepts("A")
    assert "B" in related
    assert "C" in related


def test_find_shortest_path(sample_relations):
    """Test finding shortest path between concepts."""
    graph = KnowledgeGraph()
    graph.add_relations(sample_relations)

    path = graph.find_shortest_path("A", "C")
    assert path is not None
    assert "A" in path
    assert "C" in path


def test_get_concept_connections(sample_relations):
    """Test getting concept connection statistics."""
    graph = KnowledgeGraph()
    graph.add_relations(sample_relations)

    # Node A has 2 outgoing edges (to B and C)
    stats_a = graph.get_concept_connections("A")
    assert stats_a["out_degree"] == 2
    assert stats_a["in_degree"] == 0
    assert stats_a["total_degree"] == 2

    # Node B has 1 incoming (from A) and 1 outgoing (to C)
    stats_b = graph.get_concept_connections("B")
    assert stats_b["out_degree"] == 1
    assert stats_b["in_degree"] == 1
    assert stats_b["total_degree"] == 2

    # Node C has 2 incoming edges (from A and B)
    stats_c = graph.get_concept_connections("C")
    assert stats_c["out_degree"] == 0
    assert stats_c["in_degree"] == 2
    assert stats_c["total_degree"] == 2
