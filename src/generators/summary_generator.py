"""
Summary generator for creating knowledge summaries from extracted concepts.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from src.models.concept import Concept


class SummaryGenerator:
    """
    Generates comprehensive summaries from extracted concepts.
    """

    def __init__(self, template_path: str = None):
        """
        Initialize the summary generator.

        Args:
            template_path: Path to the summary template file
        """
        if template_path is None:
            # Use default path relative to this file
            current_dir = Path(__file__).parent.parent.parent
            self.template_path = current_dir / "templates" / "summary.md"
        else:
            self.template_path = Path(template_path)

        self.concepts: List[Concept] = []
        self.summary_content = ""

    def generate_summary(self, concepts: List[Concept]) -> str:
        """
        Generate a comprehensive summary from a list of concepts.

        Args:
            concepts: List of concepts to include in the summary

        Returns:
            Formatted markdown summary
        """
        self.concepts = concepts
        self.summary_content = self._build_summary()
        return self.summary_content

    def _build_summary(self) -> str:
        """
        Build the summary content using the template.

        Returns:
            Formatted summary string
        """
        # Generate statistics
        total_concepts = len(self.concepts)
        total_categories = len(self._get_categories())
        total_definitions = sum(1 for concept in self.concepts if concept.definition.strip())

        # Generate category section
        categories_section = self._generate_categories_section()

        # Generate key concepts section
        key_concepts_section = self._generate_key_concepts_section()

        # Generate definitions section
        definitions_section = self._generate_definitions_section()

        # Generate relations section
        relations_section = self._generate_relations_section()

        # Generate relations overview
        relations_overview = self._generate_relations_overview()

        # Get template content
        template_content = self._get_template_content()

        # Replace placeholders
        summary = template_content.format(
            total_concepts=total_concepts,
            total_categories=total_categories,
            total_definitions=total_definitions,
            categories=categories_section,
            key_concepts=key_concepts_section,
            definitions=definitions_section,
            relations=relations_section,
            relations_overview=relations_overview,
            date=datetime.now().strftime("%Y-%m-%d")
        )

        return summary

    def _get_template_content(self) -> str:
        """
        Load and return the template content.

        Returns:
            Template content as string
        """
        try:
            with self.template_path.open('r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            # Return default template if file not found
            return self._get_default_template()

    def _get_default_template(self) -> str:
        """
        Return a default template.

        Returns:
            Default template content
        """
        return """# Knowledge Summary

## Overview
This document provides a comprehensive summary of the compiled knowledge concepts extracted from the source materials.

## Statistics
- **Total Concepts**: {total_concepts}
- **Total Categories**: {total_categories}
- **Total Definitions**: {total_definitions}

## Categories
{categories}

## Key Concepts
{key_concepts}

## Definitions
{definitions}

## Relations
{relations}

## Relations Overview
{relations_overview}

---
*Generated on {date} using Knowledge Compiler*
"""

    def _get_categories(self) -> Dict[str, List[Concept]]:
        """
        Get concepts grouped by category.

        Returns:
            Dictionary mapping categories to lists of concepts
        """
        categories = {}
        for concept in self.concepts:
            category = concept.criteria if concept.criteria else "Uncategorized"
            if category not in categories:
                categories[category] = []
            categories[category].append(concept)
        return categories

    def _generate_categories_section(self) -> str:
        """
        Generate the categories section.

        Returns:
            Formatted categories section
        """
        categories = self._get_categories()
        sections = []

        for category, concepts in categories.items():
            section = f"### {category}\n"
            for concept in sorted(concepts, key=lambda c: c.name):
                section += f"- {concept.name}\n"
            sections.append(section)

        return "\n".join(sections)

    def _generate_key_concepts_section(self) -> str:
        """
        Generate the key concepts section.

        Returns:
            Formatted key concepts section
        """
        if not self.concepts:
            return "No concepts available."

        sections = []

        for concept in sorted(self.concepts, key=lambda c: c.name):
            section = f"### {concept.name}\n"
            if concept.definition:
                section += f"{concept.definition}\n"
            else:
                section += "No definition available.\n"
            sections.append(section)

        return "\n".join(sections)

    def _generate_definitions_section(self) -> str:
        """
        Generate the definitions section.

        Returns:
            Formatted definitions section
        """
        if not self.concepts:
            return "No definitions available."

        sections = []

        for concept in sorted(self.concepts, key=lambda c: c.name):
            section = f"### {concept.name}\n"
            if concept.definition:
                section += f"{concept.definition}\n"
            else:
                section += "No definition available.\n"
            sections.append(section)

        return "\n".join(sections)

    def _generate_relations_section(self) -> str:
        """
        Generate the relations section.

        Returns:
            Formatted relations section
        """
        if not self.concepts:
            return "No relations available."

        sections = []

        for concept in sorted(self.concepts, key=lambda c: c.name):
            section = f"### {concept.name}\n"
            if concept.related_concepts and len(concept.related_concepts) > 0:
                relations = ", ".join(concept.related_concepts)
                section += f"- Related to: {relations}\n"
            sections.append(section)

        return "\n".join(sections)

    def _generate_relations_overview(self) -> str:
        """
        Generate a high-level overview of relations.

        Returns:
            Formatted relations overview
        """
        if not self.concepts:
            return "No relations overview available."

        # Count relations
        relation_count = sum(len(concept.related_concepts) for concept in self.concepts)
        concepts_with_relations = sum(1 for concept in self.concepts if concept.related_concepts)

        overview = f"- **Total Relations**: {relation_count}\n"
        overview += f"- **Concepts with Relations**: {concepts_with_relations}\n"
        overview += f"- **Average Relations per Concept**: {relation_count / len(self.concepts):.2f}\n"

        return overview

    def save_summary(self, file_path: str) -> bool:
        """
        Save the generated summary to a file.

        Args:
            file_path: Path to save the summary file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.summary_content)
            return True
        except Exception:
            return False

    def get_concepts_by_category(self, category: str) -> List[Concept]:
        """
        Get all concepts belonging to a specific category.

        Args:
            category: The category name to filter by

        Returns:
            List of concepts in the specified category
        """
        return [concept for concept in self.concepts if concept.criteria == category]

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the concepts.

        Returns:
            Dictionary containing various statistics
        """
        total_concepts = len(self.concepts)
        total_categories = len(self._get_categories())
        total_definitions = sum(1 for concept in self.concepts if concept.definition.strip())
        total_relations = sum(len(concept.related_concepts) for concept in self.concepts)
        concepts_with_relations = sum(1 for concept in self.concepts if concept.related_concepts)

        return {
            "total_concepts": total_concepts,
            "total_categories": total_categories,
            "total_definitions": total_definitions,
            "total_relations": total_relations,
            "concepts_with_relations": concepts_with_relations,
            "average_relations_per_concept": total_relations / total_concepts if total_concepts > 0 else 0
        }