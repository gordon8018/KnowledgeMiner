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
