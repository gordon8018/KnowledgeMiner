"""
Concept extraction functionality
"""

import re
from typing import List
from src.enhanced.models import EnhancedDocument, EnhancedConcept, ConceptType


class ConceptExtractor:
    """
    Extracts concepts from documents

    This is a basic implementation that extracts capitalized phrases
    that appear to be concepts
    """

    def extract(self, document: EnhancedDocument) -> List[EnhancedConcept]:
        """
        Extract concepts from a document

        Args:
            document: EnhancedDocument instance

        Returns:
            List of EnhancedConcept instances
        """
        concepts = []
        content = document.content

        # Simple pattern: Capitalized words/phrases (2-4 words)
        # This is a basic implementation - will be enhanced with LLM
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        matches = re.findall(pattern, content)

        # Filter unique concepts
        unique_matches = list(set(matches))

        for match in unique_matches:
            # Skip common words
            if self._is_common_word(match):
                continue

            concept = EnhancedConcept(
                name=match,
                type=ConceptType.ABSTRACT,
                definition=f"Concept: {match}",  # Will be enhanced with LLM
                confidence=0.5,
                source_documents=[document.metadata.file_path or "unknown"]
            )

            concepts.append(concept)

        return concepts

    def _is_common_word(self, phrase: str) -> bool:
        """Check if phrase is a common word to skip"""
        common_words = {
            "The", "This", "That", "These", "Those",
            "And", "But", "Or", "For", "Nor", "So", "Yet",
            "Is", "Are", "Was", "Were", "Be", "Been", "Being",
            "Have", "Has", "Had", "Do", "Does", "Did"
        }

        return phrase in common_words
