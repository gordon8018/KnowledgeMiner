"""
Extraction patterns for concept extraction from markdown content.
"""

import re
from typing import Pattern


class ExtractionPatterns:
    """
    Compiled regex patterns for extracting concepts and related information from markdown content.
    """

    def __init__(self):
        """
        Initialize all extraction patterns.
        """
        # Pattern for concept headings (## Concept Name)
        self.concept_pattern = re.compile(
            r'^\s*(#{1,6})\s*(.+?)\s*$',
            re.MULTILINE
        )

        # Pattern for definitions (**Definition:** definition text) - multiple matches
        self.definition_pattern = re.compile(
            r'\*\*Definition:\*\*\s*(.+?)(?=\n\*\*|\n\*\*|$)',
            re.IGNORECASE | re.DOTALL
        )

        # Pattern for categories (**Category:** category name)
        self.category_pattern = re.compile(
            r'\*\*Category:\*\*\s*(.+?)(?=\n\*\*|$)',
            re.IGNORECASE | re.DOTALL
        )

        # Pattern for relations (**Related to:** related concepts)
        self.relation_pattern = re.compile(
            r'\*\*(?:Related to|Also known as|Applications|Uses|Includes):\*\*\s*(.+?)(?=\n\*\*|$)',
            re.IGNORECASE | re.DOTALL
        )

        # Pattern for examples (**Example:** example text)
        self.example_pattern = re.compile(
            r'\*\*(?:Example|Examples):\*\*\s*(.+?)(?=\n\*\*|$)',
            re.IGNORECASE | re.DOTALL
        )