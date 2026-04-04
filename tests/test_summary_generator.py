import pytest
from datetime import datetime
from src.generators.summary_generator import SummaryGenerator
from src.models.concept import Concept, ConceptType


class TestSummaryGenerator:
    """Test cases for SummaryGenerator class."""

    def test_init_generator(self):
        """Test that SummaryGenerator initializes correctly."""
        generator = SummaryGenerator()
        assert generator.template_path is not None
        assert generator.concepts == []
        assert generator.summary_content == ""

    def test_generate_summary_empty_concepts(self):
        """Test generating summary with no concepts."""
        generator = SummaryGenerator()
        summary = generator.generate_summary([])

        # Should contain header with 0 concepts
        assert "# Knowledge Summary" in summary
        assert "**Total Concepts**: 0" in summary
        assert "- **Categories**: 0" in summary
        assert "- **Definitions**: 0" in summary
        assert "## Categories" in summary
        assert "## Key Concepts" in summary
        assert "## Definitions" in summary
        assert "## Relations" in summary

    def test_generate_summary_with_concepts(self):
        """Test generating summary with sample concepts."""
        generator = SummaryGenerator()

        # Create sample concepts
        concepts = [
            Concept(
                name="Machine Learning",
                type=ConceptType.TERM,
                definition="A subset of artificial intelligence that enables systems to learn from data.",
                criteria="Technology",
                applications=[{"name": "Email spam filtering", "description": ""}],
                cases=[],
                formulas=[],
                related_concepts=["Artificial Intelligence", "Data Science"],
                backlinks=[]
            ),
            Concept(
                name="Deep Learning",
                type=ConceptType.TERM,
                definition="A subfield of machine learning that uses neural networks.",
                criteria="Technology",
                applications=[{"name": "Image recognition", "description": ""}],
                cases=[],
                formulas=[],
                related_concepts=["Machine Learning", "Neural Networks"],
                backlinks=[]
            )
        ]

        summary = generator.generate_summary(concepts)

        # Check that summary contains all expected sections
        assert "# Knowledge Summary" in summary
        assert "**Total Concepts**: 2" in summary
        assert "- **Categories**: 1" in summary
        assert "- **Definitions**: 2" in summary

        # Check categories section
        assert "### Technology" in summary
        assert "- Machine Learning" in summary
        assert "- Deep Learning" in summary

        # Check key concepts section
        assert "### Machine Learning" in summary
        assert "A subset of artificial intelligence that enables systems to learn from data." in summary
        assert "### Deep Learning" in summary
        assert "A subfield of machine learning that uses neural networks." in summary

        # Check definitions section
        assert "### Machine Learning" in summary
        assert "A subset of artificial intelligence that enables systems to learn from data." in summary
        assert "### Deep Learning" in summary
        assert "A subfield of machine learning that uses neural networks." in summary

        # Check relations section
        assert "### Machine Learning" in summary
        assert "- Related to: Artificial Intelligence, Data Science" in summary
        assert "### Deep Learning" in summary
        assert "- Related to: Machine Learning, Neural Networks" in summary

        # Check that date is present
        assert "Generated on" in summary
        assert datetime.now().strftime("%Y-%m-%d") in summary

    def test_generate_summary_multiple_categories(self):
        """Test generating summary with multiple categories."""
        generator = SummaryGenerator()

        concepts = [
            Concept(
                name="Machine Learning",
                type=ConceptType.TERM,
                definition="A subset of artificial intelligence.",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=[],
                backlinks=[]
            ),
            Concept(
                name="Investment Strategy",
                type=ConceptType.STRATEGY,
                definition="A plan for investing.",
                criteria="Finance",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=[],
                backlinks=[]
            )
        ]

        summary = generator.generate_summary(concepts)

        # Should have multiple categories
        assert "### Technology" in summary
        assert "### Finance" in summary
        assert "- Machine Learning" in summary
        assert "- Investment Strategy" in summary

    def test_generate_summary_concepts_without_definitions(self):
        """Test generating summary with concepts that have no definitions."""
        generator = SummaryGenerator()

        concepts = [
            Concept(
                name="Undefined Concept",
                type=ConceptType.TERM,
                definition="",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=[],
                backlinks=[]
            )
        ]

        summary = generator.generate_summary(concepts)

        # Should handle empty definitions gracefully
        assert "### Undefined Concept" in summary
        assert "No definition available" in summary or "Undefined Concept" in summary

    def test_generate_summary_concepts_without_relations(self):
        """Test generating summary with concepts that have no relations."""
        generator = SummaryGenerator()

        concepts = [
            Concept(
                name="Isolated Concept",
                type=ConceptType.TERM,
                definition="A concept with no relations.",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=[],
                backlinks=[]
            )
        ]

        summary = generator.generate_summary(concepts)

        # Should handle empty relations gracefully
        assert "### Isolated Concept" in summary
        assert "No relations found" not in summary  # Should not have "no relations" message

    def test_generate_summary_large_dataset(self):
        """Test generating summary with a large number of concepts."""
        generator = SummaryGenerator()

        # Create 50 concepts
        concepts = []
        for i in range(50):
            concept = Concept(
                name=f"Concept {i+1}",
                type=ConceptType.TERM,
                definition=f"Definition for concept {i+1}.",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=[],
                backlinks=[]
            )
            concepts.append(concept)

        summary = generator.generate_summary(concepts)

        # Should handle large dataset without issues
        assert "**Total Concepts**: 50" in summary
        assert "### Technology" in summary
        assert len(summary) > 1000  # Should be substantial

    def test_template_loading(self):
        """Test that template loads correctly."""
        generator = SummaryGenerator()

        # Check that template path is set
        assert generator.template_path is not None
        assert generator.template_path.exists()

    def test_summary_formatting(self):
        """Test that summary is properly formatted."""
        generator = SummaryGenerator()

        concepts = [
            Concept(
                name="Test Concept",
                type=ConceptType.TERM,
                definition="A test definition.",
                criteria="Test Category",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=[],
                backlinks=[]
            )
        ]

        summary = generator.generate_summary(concepts)

        # Check proper markdown formatting
        assert summary.startswith("# Knowledge Summary")
        assert "## Overview" in summary
        assert "## Statistics" in summary
        assert "## Categories" in summary
        assert "## Key Concepts" in summary
        assert "## Definitions" in summary
        assert "## Relations" in summary
        assert "*Generated on" in summary
        assert "using Knowledge Compiler*" in summary