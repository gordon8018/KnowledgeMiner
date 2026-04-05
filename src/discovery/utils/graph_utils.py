"""
Graph processing utilities using NetworkX.
"""

from typing import List, Dict, Tuple, Any
import networkx as nx
import logging
from src.core.relation_model import Relation

logger = logging.getLogger(__name__)


def build_relation_graph(relations: List[Relation]) -> nx.Graph:
    """
    Build a NetworkX graph from relations.

    Args:
        relations: List of relations between concepts

    Returns:
        NetworkX Graph object
    """
    G = nx.Graph()

    for relation in relations:
        source = relation.source_concept
        target = relation.target_concept

        # Add nodes
        if not G.has_node(source):
            G.add_node(source)
        if not G.has_node(target):
            G.add_node(target)

        # Add edge with weight based on relation strength
        weight = relation.strength if hasattr(relation, 'strength') else 1.0
        if G.has_edge(source, target):
            # Edge exists, update weight
            G[source][target]['weight'] += weight
            G[source][target]['count'] += 1
        else:
            G.add_edge(source, target, weight=weight, count=1)

    return G


def find_isolated_nodes(graph: nx.Graph) -> List[str]:
    """
    Find isolated nodes (nodes with no connections).

    Args:
        graph: NetworkX Graph

    Returns:
        List of isolated node names
    """
    return list(nx.isolates(graph))


def detect_communities(graph: nx.Graph, min_size: int = 3) -> List[List[str]]:
    """
    Detect communities in the graph using Louvain algorithm.

    Args:
        graph: NetworkX Graph
        min_size: Minimum community size to include

    Returns:
        List of communities, where each community is a list of node names
    """
    try:
        import networkx.algorithms.community as nx_community

        # Use Louvain algorithm for community detection
        communities = nx_community.louvain_communities(graph)

        # Filter by minimum size
        filtered_communities = [
            list(comm) for comm in communities
            if len(comm) >= min_size
        ]

        return filtered_communities
    except (ImportError, AttributeError) as e:
        # NetworkX version doesn't support community detection
        logger.warning(f"Community detection not available: {e}. Using connected components fallback.")
        return [list(comp) for comp in nx.connected_components(graph)]
    except Exception as e:
        # Other unexpected errors (e.g., graph structure issues)
        logger.warning(f"Community detection failed: {e}. Using connected components fallback.")
        return [list(comp) for comp in nx.connected_components(graph)]


def compute_centrality(graph: nx.Graph) -> Dict[str, float]:
    """
    Compute centrality measures for all nodes.

    Args:
        graph: NetworkX Graph

    Returns:
        Dictionary mapping node names to centrality scores
    """
    # Use betweenness centrality
    centrality = nx.betweenness_centrality(graph)
    return centrality
