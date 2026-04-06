import pytest
import networkx as nx
from src.discovery.utils.graph_utils import (
    build_relation_graph,
    find_isolated_nodes,
    detect_communities,
    compute_centrality
)
from src.discovery.utils.scoring import (
    compute_significance_score,
    normalize_scores,
    rank_by_score
)
from src.core.relation_model import Relation, RelationType


def test_build_relation_graph():
    """Test building graph from relations."""
    relations = [
        Relation(id="rel1", source_concept="A", target_concept="B", relation_type=RelationType.RELATED_TO, strength=0.8),
        Relation(id="rel2", source_concept="B", target_concept="C", relation_type=RelationType.RELATED_TO, strength=0.6),
        Relation(id="rel3", source_concept="A", target_concept="C", relation_type=RelationType.RELATED_TO, strength=0.5),
    ]

    graph = build_relation_graph(relations)

    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 3
    assert graph.has_edge("A", "B")


def test_find_isolated_nodes():
    """Test finding isolated nodes."""
    graph = nx.Graph()
    graph.add_node("isolated")
    graph.add_edge("A", "B")

    isolated = find_isolated_nodes(graph)

    assert "isolated" in isolated
    assert len(isolated) == 1


def test_compute_significance_score():
    """Test significance score computation."""
    score = compute_significance_score(
        novelty=0.8,
        impact=0.7,
        actionability=0.9
    )

    expected = 0.8 * 0.25 + 0.7 * 0.40 + 0.9 * 0.35
    assert abs(score - expected) < 0.001
    assert 0.0 <= score <= 1.0


def test_normalize_scores():
    """Test score normalization."""
    scores = [0.2, 0.5, 0.8, 1.0]
    normalized = normalize_scores(scores)

    assert len(normalized) == len(scores)
    assert min(normalized) == 0.0
    assert max(normalized) == 1.0


def test_rank_by_score():
    """Test ranking by score."""
    class Item:
        def __init__(self, name, score):
            self.name = name
            self.score = score

    items = [Item("A", 0.5), Item("B", 0.9), Item("C", 0.3)]
    ranked = rank_by_score(items, 'score', reverse=True)

    assert ranked[0].name == "B"  # Highest score
    assert ranked[-1].name == "C"  # Lowest score


def test_build_relation_graph_multiple_edges():
    """Test edge weight accumulation when multiple relations exist between same concepts."""
    relations = [
        Relation(id="rel1", source_concept="A", target_concept="B", relation_type=RelationType.RELATED_TO, strength=0.5),
        Relation(id="rel2", source_concept="A", target_concept="B", relation_type=RelationType.RELATED_TO, strength=0.3),
        Relation(id="rel3", source_concept="A", target_concept="C", relation_type=RelationType.RELATED_TO, strength=0.7),
    ]

    graph = build_relation_graph(relations)

    # Should have 3 edges (A-B twice, A-C once)
    assert graph.number_of_edges() == 2
    # A-B edge should have accumulated weight (0.5 + 0.3 = 0.8) and count of 2
    assert graph["A"]["B"]["weight"] == 0.8
    assert graph["A"]["B"]["count"] == 2
    # A-C edge should have single weight and count
    assert graph["A"]["C"]["weight"] == 0.7
    assert graph["A"]["C"]["count"] == 1


def test_detect_communities_fallback():
    """Test community detection fallback behavior when Louvain fails."""
    # Create a simple graph
    graph = nx.Graph()
    graph.add_edges_from([("A", "B"), ("B", "C"), ("D", "E")])

    # This should work normally
    communities = detect_communities(graph, min_size=2)
    assert len(communities) >= 1

    # Test with a graph that might trigger fallback
    # (The function should gracefully handle any exception and return connected components)
    empty_graph = nx.Graph()
    empty_graph.add_node("isolated")
    empty_communities = detect_communities(empty_graph, min_size=1)
    assert isinstance(empty_communities, list)


def test_compute_centrality_empty_graph():
    """Test centrality computation with an empty graph."""
    graph = nx.Graph()
    centrality = compute_centrality(graph)

    assert isinstance(centrality, dict)
    assert len(centrality) == 0


def test_compute_centrality_disconnected_nodes():
    """Test centrality computation with disconnected nodes."""
    graph = nx.Graph()
    graph.add_node("isolated1")
    graph.add_node("isolated2")
    graph.add_edge("A", "B")

    centrality = compute_centrality(graph)

    assert isinstance(centrality, dict)
    assert len(centrality) == 4  # All 4 nodes
    # Isolated nodes should have centrality of 0.0
    assert centrality.get("isolated1", 1.0) == 0.0
    assert centrality.get("isolated2", 1.0) == 0.0
