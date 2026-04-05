"""
Explicit relation patterns for text-based extraction.
"""

import re
from typing import Dict, List, Tuple
from src.core.relation_model import RelationType


# Default explicit relation patterns
EXPLICIT_PATTERNS: Dict[str, RelationType] = {
    # Chinese patterns
    r'(\S+)导致(\S+)': RelationType.CAUSES,
    r'(\S+)影响(\S+)': RelationType.RELATED_TO,
    r'(\S+)包含(\S+)': RelationType.CONTAINS,
    r'(\S+)支持(\S+)': RelationType.SUPPORTS,
    r'(\S+)反对(\S+)': RelationType.OPPOSES,
    r'(\S+)依赖于(\S+)': RelationType.DEPENDS_ON,
    r'(\S+)类似于(\S+)': RelationType.SIMILAR_TO,
    r'(\S+)先于(\S+)': RelationType.PRECEDES,

    # English patterns (fallback)
    r'(\S+)\s+causes?\s+(\S+)': RelationType.CAUSES,
    r'(\S+)\s+influences?\s+(\S+)': RelationType.RELATED_TO,
    r'(\S+)\s+contains?\s+(\S+)': RelationType.CONTAINS,
    r'(\S+)\s+supports?\s+(\S+)': RelationType.SUPPORTS,
    r'(\S+)\s+opposes?\s+(\S+)': RelationType.OPPOSES,
    r'(\S+)\s+depends?\s+on\s+(\S+)': RelationType.DEPENDS_ON,
    r'(\S+)\s+similar\s+to\s+(\S+)': RelationType.SIMILAR_TO,
    r'(\S+)\s+precedes?\s+(\S+)': RelationType.PRECEDES,
}


class RelationPatternLoader:
    """
    Loader for explicit relation patterns.

    Patterns are compiled regex expressions that match text
    indicating relationships between concepts.
    """

    def __init__(self, custom_patterns: Dict[str, RelationType] = None):
        """
        Initialize pattern loader.

        Args:
            custom_patterns: Optional custom patterns to add/override defaults
        """
        self.patterns = EXPLICIT_PATTERNS.copy()

        if custom_patterns:
            self.patterns.update(custom_patterns)

        # Compile patterns for performance
        self._compiled_patterns = [
            (re.compile(pattern), relation_type)
            for pattern, relation_type in self.patterns.items()
        ]

    def extract_relations(self, text: str) -> List[Tuple[str, str, RelationType]]:
        """
        Extract explicit relations from text.

        Args:
            text: Text to search for relations

        Returns:
            List of (source_concept, target_concept, relation_type) tuples
        """
        relations = []

        for pattern, relation_type in self._compiled_patterns:
            matches = pattern.finditer(text)

            for match in matches:
                if len(match.groups()) >= 2:
                    source = match.group(1).strip()
                    target = match.group(2).strip()

                    # Filter out non-concept matches
                    if self._is_valid_concept(source) and self._is_valid_concept(target):
                        relations.append((source, target, relation_type))

        return relations

    def _is_valid_concept(self, text: str) -> bool:
        """
        Check if text looks like a valid concept.

        Args:
            text: Text to validate

        Returns:
            True if text looks like a concept name
        """
        # Basic validation: should be 1-50 chars, not all punctuation
        if len(text) < 1 or len(text) > 50:
            return False

        # Should contain at least one letter or Chinese character
        has_alpha = any(c.isalpha() or '\u4e00' <= c <= '\u9fff' for c in text)
        return has_alpha

    def get_pattern_count(self) -> int:
        """Get number of loaded patterns."""
        return len(self.patterns)
