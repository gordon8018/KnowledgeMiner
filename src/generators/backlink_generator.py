"""
Backlink generator for creating concept relationships.
"""

import logging
from typing import List, Dict, Set
from src.models.concept import Concept

logger = logging.getLogger(__name__)


class BacklinkGenerator:
    """
    Generates backlinks and relationship maps between concepts.
    """

    def __init__(self):
        """
        Initialize the backlink generator.
        """
        pass

    def generate_backlinks(self, concepts: List[Concept]) -> Dict[str, List[str]]:
        """
        Generate backlinks between concepts.

        Args:
            concepts: List of concepts to generate backlinks for

        Returns:
            Dictionary mapping concept names to their backlinks
        """
        backlinks = {}
        for concept in concepts:
            # Remove duplicates from related concepts
            unique_relations = self._remove_duplicates(concept.related_concepts)
            backlinks[concept.name] = unique_relations
        return backlinks

    def generate_relationship_map(self, concepts: List[Concept]) -> Dict[str, List[str]]:
        """
        Generate a relationship map between concepts.

        Args:
            concepts: List of concepts to generate relationship map for

        Returns:
            Dictionary mapping concept names to their related concepts
        """
        return self.generate_backlinks(concepts)

    def generate(self, concepts: List[Concept], output_path: str = None) -> Dict[str, List[str]]:
        """
        Generate backlinks and optionally save to file.

        Args:
            concepts: List of concepts to generate backlinks for
            output_path: Optional path to save the backlinks

        Returns:
            Dictionary mapping concept names to their backlinks
        """
        backlinks = self.generate_backlinks(concepts)

        if output_path:
            self._save_backlinks(backlinks, output_path)

        return backlinks

    def generate_all(self, concepts: List[Concept], output_dir: str = None) -> Dict[str, Dict]:
        """
        Generate all types of relationship maps and optionally save to files.

        Args:
            concepts: List of concepts to generate relationship maps for
            output_dir: Optional directory to save the relationship maps

        Returns:
            Dictionary containing all relationship maps
        """
        backlinks = self.generate_backlinks(concepts)
        relationship_map = self.generate_relationship_map(concepts)

        # Generate comprehensive relationship data
        all_relationships = {
            'backlinks': backlinks,
            'relationship_map': relationship_map,
            'summary': self._generate_summary(concepts, backlinks)
        }

        if output_dir:
            self._save_all_relationships(all_relationships, output_dir)

        return all_relationships

    def _remove_duplicates(self, items: List[str]) -> List[str]:
        """
        Remove duplicates from a list while preserving order.

        Args:
            items: List of items to remove duplicates from

        Returns:
            List with duplicates removed
        """
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def _generate_summary(self, concepts: List[Concept], backlinks: Dict[str, List[str]]) -> Dict:
        """
        Generate summary statistics for the relationship data.

        Args:
            concepts: List of concepts
            backlinks: Generated backlinks

        Returns:
            Dictionary containing summary statistics
        """
        total_concepts = len(concepts)
        total_relationships = sum(len(relations) for relations in backlinks.values())
        avg_relationships_per_concept = total_relationships / total_concepts if total_concepts > 0 else 0

        # Find concepts with most relationships
        most_connected = []
        if backlinks:
            max_relations = max(len(relations) for relations in backlinks.values())
            most_connected = [
                concept_name for concept_name, relations in backlinks.items()
                if len(relations) == max_relations
            ]

        return {
            'total_concepts': total_concepts,
            'total_relationships': total_relationships,
            'avg_relationships_per_concept': avg_relationships_per_concept,
            'most_connected_concepts': most_connected,
            'max_relationships': max_relations if backlinks else 0
        }

    def _save_backlinks(self, backlinks: Dict[str, List[str]], output_path: str):
        """
        Save backlinks to a file.

        Args:
            backlinks: Dictionary of backlinks to save
            output_path: Path to save the file
        """
        import json

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(backlinks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not save backlinks to {output_path}: {e}")

    def _save_all_relationships(self, all_relationships: Dict[str, Dict], output_dir: str):
        """
        Save all relationship data to files.

        Args:
            all_relationships: Dictionary containing all relationship data
            output_dir: Directory to save the files
        """
        import json
        import os

        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save individual files
        try:
            # Save backlinks
            with open(os.path.join(output_dir, 'backlinks.json'), 'w', encoding='utf-8') as f:
                json.dump(all_relationships['backlinks'], f, indent=2, ensure_ascii=False)

            # Save relationship map
            with open(os.path.join(output_dir, 'relationship_map.json'), 'w', encoding='utf-8') as f:
                json.dump(all_relationships['relationship_map'], f, indent=2, ensure_ascii=False)

            # Save summary
            with open(os.path.join(output_dir, 'summary.json'), 'w', encoding='utf-8') as f:
                json.dump(all_relationships['summary'], f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"Could not save relationship data to {output_dir}: {e}")
