"""KnowledgeGraph using NetworkX for graph operations."""

import networkx as nx
from typing import List, Optional, Dict, Any

from src.core.relation_model import Relation


class KnowledgeGraph:
    """
    Knowledge graph using NetworkX.

    Reuses NetworkX from Phase 2 for graph operations.
    Simplified to core functionality: concept graph and basic queries.
    """

    def __init__(self):
        """Initialize an empty knowledge graph."""
        self.graph = nx.DiGraph()

    def add_relations(self, relations: List[Relation]):
        """
        Add relations to the graph.

        Args:
            relations: List of Relation objects to add
        """
        for relation in relations:
            self.graph.add_edge(
                relation.source_concept,
                relation.target_concept,
                relation_type=relation.relation_type,
                strength=relation.strength,
                confidence=relation.confidence
            )

    def get_related_concepts(self, concept: str) -> List[str]:
        """
        Get concepts directly related to the given concept.

        Args:
            concept: Concept name

        Returns:
            List of related concept names
        """
        if concept not in self.graph:
            return []

        return list(self.graph.neighbors(concept))

    def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Find shortest path between two concepts.

        Args:
            source: Source concept
            target: Target concept

        Returns:
            List of concept names in path, or None if no path exists
        """
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return None

    def get_concept_connections(self, concept: str) -> Dict[str, Any]:
        """
        Get connection statistics for a concept.

        Args:
            concept: Concept name

        Returns:
            Dictionary with connection statistics
        """
        if concept not in self.graph:
            return {"in_degree": 0, "out_degree": 0, "total_degree": 0}

        return {
            "in_degree": self.graph.in_degree(concept),
            "out_degree": self.graph.out_degree(concept),
            "total_degree": self.graph.degree(concept)
        }
