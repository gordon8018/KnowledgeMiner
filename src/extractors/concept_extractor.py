"""
Concept extractor for extracting knowledge concepts from markdown content.
"""

import re
from typing import List, Dict, Optional
from src.models.concept import Concept, ConceptType
from src.extractors.patterns import ExtractionPatterns


class ConceptExtractor:
    """
    Extracts concepts and their properties from markdown content.
    """

    def __init__(self):
        """
        Initialize the concept extractor.
        """
        self.patterns = ExtractionPatterns()
        self.concepts: List[Concept] = []
        self.current_concept: Optional[Concept] = None

    def extract_concepts(self, content: str) -> List[Concept]:
        """
        Extract concepts from markdown content.

        Args:
            content: The markdown content to extract concepts from

        Returns:
            List of extracted concepts
        """
        self.concepts = []

        # Split content by concept headings
        pattern = re.compile(r'^\s*(#{1,6})\s*(.+?)\s*$', re.MULTILINE)
        matches = list(pattern.finditer(content))

        if not matches:
            return []

        # Process each concept
        for i, match in enumerate(matches):
            concept_name = match.group(2).strip()

            # Create concept
            concept = Concept(
                name=concept_name,
                type=ConceptType.TERM,
                definition="",
                criteria="",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=[],
                backlinks=[]
            )

            # Extract content for this concept
            start_pos = match.start()
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            concept_content = content[start_pos:end_pos]

            # Extract properties from concept content
            self._extract_properties_for_concept(concept, concept_content)

            self.concepts.append(concept)

        return self.concepts

    def _process_line(self, line: str, full_content: str):
        """
        Process a single line of content.

        Args:
            line: The line to process
            full_content: The full content for pattern matching
        """
        # Check for concept heading
        match = self.patterns.concept_pattern.match(line.strip())
        if match:
            # Save current concept if it exists
            if self.current_concept:
                self.concepts.append(self.current_concept)

            # Create new concept with default values
            concept_name = match.group(2).strip()
            self.current_concept = Concept(
                name=concept_name,
                type=ConceptType.TERM,  # Default type
                definition="",  # Will be filled later
                criteria="",  # Will be filled later
                applications=[],  # Will be filled later
                cases=[],  # Will be filled later
                formulas=[],  # Will be filled later
                related_concepts=[],  # Will be filled later
                backlinks=[]  # Will be filled later
            )
            return

        # If we have a current concept, extract additional properties
        if self.current_concept:
            self._extract_concept_properties(full_content)

    def _extract_properties_for_concept(self, concept: Concept, content: str):
        """
        Extract properties for a concept from its content.

        Args:
            concept: The concept to extract properties for
            content: The content for this concept only
        """
        # Extract definition - collect all definitions
        definition_matches = self.patterns.definition_pattern.finditer(content)
        definitions = []
        for match in definition_matches:
            definitions.append(match.group(1).strip())

        if definitions:
            concept.definition = " ".join(definitions)

        # Extract category (store as a simple string in criteria for now)
        category_match = self.patterns.category_pattern.search(content)
        if category_match and not concept.criteria:
            concept.criteria = category_match.group(1).strip()

        # Extract relations
        relation_matches = self.patterns.relation_pattern.finditer(content)
        relations = []
        for match in relation_matches:
            # Split relations by comma and clean up
            raw_relations = match.group(1).split(',')
            for relation in raw_relations:
                relation = relation.strip()
                if relation and relation.lower() not in relations:
                    relations.append(relation.lower())

        # Add relations to existing ones, avoiding duplicates
        if relations:
            if not concept.related_concepts:
                concept.related_concepts = []

            for relation in relations:
                if relation not in concept.related_concepts:
                    concept.related_concepts.append(relation)

        # Extract examples
        example_matches = self.patterns.example_pattern.finditer(content)
        examples = []
        for match in example_matches:
            # Split examples by comma and clean up
            raw_examples = match.group(1).split(',')
            for example in raw_examples:
                example = example.strip()
                if example and example.lower() not in examples:
                    examples.append(example.lower())

        # Add examples to applications for now
        if examples:
            if not concept.applications:
                concept.applications = []

            for example in examples:
                example_dict = {"name": example, "description": ""}
                if example_dict not in concept.applications:
                    concept.applications.append(example_dict)

    def _process_line(self, line: str, full_content: str):
        """
        Process a single line of content.

        Args:
            line: The line to process
            full_content: The full content for pattern matching
        """
        # Keep this for backward compatibility if needed
        pass

    def get_concepts_by_category(self, category: str) -> List[Concept]:
        """
        Get all concepts belonging to a specific category.

        Args:
            category: The category name to filter by

        Returns:
            List of concepts in the specified category
        """
        return [concept for concept in self.concepts if concept.category == category]

    def get_concepts_by_relation(self, relation: str) -> List[Concept]:
        """
        Get all concepts that have a specific relation.

        Args:
            relation: The relation to filter by

        Returns:
            List of concepts with the specified relation
        """
        return [concept for concept in self.concepts
                if concept.related and relation.lower() in concept.related]

    def clear_concepts(self):
        """
        Clear all extracted concepts and reset the extractor.
        """
        self.concepts = []
        self.current_concept = None