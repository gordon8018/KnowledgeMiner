"""
Article generator for creating detailed concept articles.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from src.models.concept import Concept


class ArticleGenerator:
    """
    Generates detailed articles for individual concepts.
    """

    def __init__(self, template_path: str = None):
        """
        Initialize the article generator.

        Args:
            template_path: Path to the article template file
        """
        if template_path is None:
            # Use default path relative to this file
            current_dir = Path(__file__).parent.parent.parent
            self.template_path = current_dir / "templates" / "concept_article.md"
        else:
            self.template_path = Path(template_path)

        self.articles: List[str] = []

    def generate_article(self, concept: Concept) -> str:
        """
        Generate an article for a single concept.

        Args:
            concept: The concept to generate an article for

        Returns:
            Formatted article content
        """
        # Generate article content
        article_content = self._build_article(concept)

        # Store article
        self.articles.append(article_content)

        return article_content

    def generate_articles(self, concepts: List[Concept]) -> List[str]:
        """
        Generate articles for multiple concepts.

        Args:
            concepts: List of concepts to generate articles for

        Returns:
            List of article contents
        """
        articles = []
        for concept in concepts:
            article = self.generate_article(concept)
            articles.append(article)
        return articles

    def _build_article(self, concept: Concept) -> str:
        """
        Build the article content using the template.

        Args:
            concept: The concept to build article for

        Returns:
            Formatted article string
        """
        # Get template content
        template_content = self._get_template_content()

        # Prepare placeholders
        placeholders = {
            'concept_name': concept.name,
            'overview': self._generate_overview(concept),
            'definition': concept.definition if concept.definition else "No definition available.",
            'category': concept.criteria if concept.criteria else "Uncategorized",
            'related_concepts': self._generate_related_concepts(concept),
            'applications': self._generate_applications(concept),
            'key_points': self._generate_key_points(concept),
            'formulas': self._generate_formulas(concept),
            'examples': self._generate_examples(concept),
            'related_topics': self._generate_related_topics(concept),
            'date': datetime.now().strftime("%Y-%m-%d")
        }

        # Replace placeholders
        article = template_content.format(**placeholders)

        return article

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
        return """# {concept_name}

## Overview
{overview}

## Definition
{definition}

## Category
**Category**: {category}

## Related Concepts
{related_concepts}

## Applications
{applications}

## Key Points
{key_points}

## Formulas
{formulas}

## Examples
{examples}

## Related Topics
{related_topics}

---
*Generated on {date} using Knowledge Compiler*
"""

    def _generate_overview(self, concept: Concept) -> str:
        """
        Generate an overview section for the concept.

        Args:
            concept: The concept to generate overview for

        Returns:
            Formatted overview section
        """
        if concept.definition:
            return concept.definition
        else:
            return f"No overview available for {concept.name}."

    def _generate_related_concepts(self, concept: Concept) -> str:
        """
        Generate related concepts section.

        Args:
            concept: The concept to generate related concepts for

        Returns:
            Formatted related concepts section
        """
        if not concept.related_concepts or len(concept.related_concepts) == 0:
            return "No related concepts available."

        section = ""
        for related_concept in sorted(concept.related_concepts):
            section += f"- {related_concept}\n"
        return section

    def _generate_applications(self, concept: Concept) -> str:
        """
        Generate applications section.

        Args:
            concept: The concept to generate applications for

        Returns:
            Formatted applications section
        """
        if not concept.applications or len(concept.applications) == 0:
            return "No applications available."

        section = ""
        for app in concept.applications:
            name = app.get('name', '')
            description = app.get('description', '')
            if name:
                section += f"### {name}\n"
                if description:
                    section += f"{description}\n"
        return section

    def _generate_key_points(self, concept: Concept) -> str:
        """
        Generate key points section.

        Args:
            concept: The concept to generate key points for

        Returns:
            Formatted key points section
        """
        section = f"### {concept.name}\n"

        # Add cases if available
        if concept.cases and len(concept.cases) > 0:
            section += "**Case Studies:**\n"
            for case in concept.cases:
                section += f"- {case}\n"

        # Add additional insights based on concept properties
        if concept.definition:
            section += f"\n**Definition**: {concept.definition}\n"

        if concept.criteria:
            section += f"\n**Category**: {concept.criteria}\n"

        # Add related concepts as key points
        if concept.related_concepts and len(concept.related_concepts) > 0:
            section += "\n**Related Concepts:** "
            section += ", ".join(concept.related_concepts)

        return section

    def _generate_formulas(self, concept: Concept) -> str:
        """
        Generate formulas section.

        Args:
            concept: The concept to generate formulas for

        Returns:
            Formatted formulas section
        """
        if not concept.formulas or len(concept.formulas) == 0:
            return "No formulas available."

        section = f"### {concept.name}\n"
        for formula in concept.formulas:
            section += f"- {formula}\n"
        return section

    def _generate_examples(self, concept: Concept) -> str:
        """
        Generate examples section.

        Args:
            concept: The concept to generate examples for

        Returns:
            Formatted examples section
        """
        if not concept.applications or len(concept.applications) == 0:
            return "No examples available."

        section = ""
        for app in concept.applications:
            name = app.get('name', '')
            description = app.get('description', '')
            if name and "example" in name.lower():
                section += f"### {name}\n"
                if description:
                    section += f"{description}\n"

        if not section:
            return "No examples available."
        return section

    def _generate_related_topics(self, concept: Concept) -> str:
        """
        Generate related topics section.

        Args:
            concept: The concept to generate related topics for

        Returns:
            Formatted related topics section
        """
        if not concept.related_concepts or len(concept.related_concepts) == 0:
            return "No related topics available."

        section = ""
        for topic in sorted(concept.related_concepts):
            section += f"- {topic}\n"
        return section

    def save_articles(self, directory_path: str) -> bool:
        """
        Save all generated articles to a directory.

        Args:
            directory_path: Directory path to save articles

        Returns:
            True if successful, False otherwise
        """
        try:
            directory = Path(directory_path)
            directory.mkdir(parents=True, exist_ok=True)

            for i, article in enumerate(self.articles):
                # Create filename from concept name or index
                filename = f"article_{i+1}.md"
                file_path = directory / filename

                with file_path.open('w', encoding='utf-8') as file:
                    file.write(article)

            return True
        except Exception:
            return False

    def get_article(self, concept_name: str) -> str:
        """
        Get an article by concept name.

        Args:
            concept_name: Name of the concept to retrieve

        Returns:
            Article content or empty string if not found
        """
        for article in self.articles:
            if article.startswith(f"# {concept_name}"):
                return article
        return ""

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the generated articles.

        Returns:
            Dictionary containing various statistics
        """
        return {
            "total_articles": len(self.articles),
            "concepts_with_applications": sum(1 for article in self.articles if "###" in article),
            "concepts_with_formulas": sum(1 for article in self.articles if "## Formulas" in article and "No formulas" not in article),
            "concepts_with_cases": sum(1 for article in self.articles if "Case Studies:" in article)
        }

    def clear_articles(self):
        """
        Clear all generated articles and reset the generator.
        """
        self.articles = []