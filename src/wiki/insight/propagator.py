"""
Insight propagator for spreading insights through knowledge graph.
"""

import logging
from collections import deque
from typing import List, Dict, Any, Set

from src.discovery.models.insight import Insight

logger = logging.getLogger(__name__)


class InsightPropagator:
    """
    Propagate insights through knowledge graph using BFS traversal.

    Implements direct propagation with cycle detection and max hops limit.
    """

    def __init__(self, wiki_core):
        """
        Initialize InsightPropagator.

        Args:
            wiki_core: WikiCore instance for accessing knowledge graph
        """
        self.wiki_core = wiki_core

    def propagate(self, insight: Insight, max_hops: int = 2) -> List[Dict[str, Any]]:
        """
        Propagate insight through knowledge graph.

        Uses BFS traversal to find all concepts reachable from the insight's
        related_concepts within max_hops distance. Implements cycle detection
        to avoid infinite loops and redundant processing.

        Args:
            insight: Insight to propagate
            max_hops: Maximum number of hops to propagate (default: 2)

        Returns:
            List of propagation targets with:
                - concept: str (target concept name)
                - path: List[str] (path taken from source to target)
                - hops: int (number of hops from source)
                - insight_id: str (original insight ID)
        """
        if not insight.related_concepts:
            logger.debug(f"Insight {insight.id} has no related concepts to propagate")
            return []

        # Initialize BFS queue
        # Each queue item: (current_concept, path_from_source, hop_count)
        queue = deque()

        # Initialize with all related concepts as starting points
        for source_concept in insight.related_concepts:
            queue.append((source_concept, [source_concept], 0))

        # Track visited concepts for cycle detection
        visited: Set[str] = set(insight.related_concepts)

        results = []

        # BFS traversal
        while queue:
            current_concept, path, hops = queue.popleft()

            # Skip if we've exceeded max hops (don't expand further)
            if hops >= max_hops:
                continue

            # Get related concepts from knowledge graph
            related_concepts = self.wiki_core.get_related_concepts(current_concept)

            for related_concept in related_concepts:
                # Skip if already visited (cycle detection)
                if related_concept in visited:
                    continue

                # Mark as visited
                visited.add(related_concept)

                # Create new path
                new_path = path + [related_concept]

                # Add to results
                results.append({
                    "concept": related_concept,
                    "path": new_path,
                    "hops": hops + 1,
                    "insight_id": insight.id
                })

                # Enqueue for further expansion
                queue.append((related_concept, new_path, hops + 1))

        logger.debug(
            f"Propagated insight {insight.id} to {len(results)} concepts "
            f"within {max_hops} hops"
        )

        return results
