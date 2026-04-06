import pytest
from datetime import datetime
from src.generators.article_generator import ArticleGenerator
from src.models.concept import Concept, ConceptType


class TestArticleGenerator:
    """Test cases for ArticleGenerator class."""

    def test_init_generator(self):
        """Test that ArticleGenerator initializes correctly."""
        generator = ArticleGenerator()
        assert generator.template_path is not None
        assert generator.articles == []

    def test_generate_article_basic(self):
        """Test generating a basic article."""
        generator = ArticleGenerator()

        concept = Concept(
            name="Machine Learning",
            type=ConceptType.TERM,
            definition="A subset of artificial intelligence that enables systems to learn from data.",
            criteria="Technology",
            applications=[{"name": "Email spam filtering", "description": "Used to filter spam emails"}],
            cases=[],
            formulas=[],
            related_concepts=["Artificial Intelligence", "Data Science"],
            backlinks=[]
        )

        article = generator.generate_article(concept)

        # Check basic structure
        assert article.startswith("# Machine Learning")
        assert "## Overview" in article
        assert "## Definition" in article
        assert "## Category" in article
        assert "## Related Concepts" in article
        assert "## Applications" in article
        assert "## Key Points" in article
        assert "## Formulas" in article
        assert "## Examples" in article
        assert "## Related Topics" in article

        # Check content
        assert "Machine Learning" in article
        assert "A subset of artificial intelligence that enables systems to learn from data." in article
        assert "**Category**: Technology" in article
        assert "- Artificial Intelligence" in article
        assert "- Data Science" in article
        assert "### Email spam filtering" in article
        assert "Used to filter spam emails" in article

    def test_generate_article_empty_concept(self):
        """Test generating article with empty concept."""
        generator = ArticleGenerator()

        concept = Concept(
            name="Empty Concept",
            type=ConceptType.TERM,
            definition="",
            criteria="",
            applications=[],
            cases=[],
            formulas=[],
            related_concepts=[],
            backlinks=[]
        )

        article = generator.generate_article(concept)

        # Should still have basic structure
        assert article.startswith("# Empty Concept")
        assert "## Overview" in article
        assert "## Definition" in article
        assert "## Category" in article
        assert "## Related Concepts" in article
        assert "## Applications" in article
        assert "## Key Points" in article
        assert "## Formulas" in article
        assert "## Examples" in article
        assert "## Related Topics" in article

        # Should handle empty content gracefully
        assert "No overview available" in article or "Empty Concept" in article
        assert "No definition available" in article or "Empty Concept" in article
        assert "**Category**: " in article

    def test_generate_article_with_formulas(self):
        """Test generating article with formulas."""
        generator = ArticleGenerator()

        concept = Concept(
            name="Linear Regression",
            type=ConceptType.TERM,
            definition="A statistical method for modeling the relationship between variables.",
            criteria="Mathematics",
            applications=[],
            cases=[],
            formulas=["y = mx + b", "R² = 1 - (SS_res / SS_tot)"],
            related_concepts=["Statistics", "Machine Learning"],
            backlinks=[]
        )

        article = generator.generate_article(concept)

        # Check formulas section
        assert "## Formulas" in article
        assert "### Linear Regression" in article
        assert "y = mx + b" in article
        assert "R² = 1 - (SS_res / SS_tot)" in article

    def test_generate_article_with_cases(self):
        """Test generating article with case studies."""
        generator = ArticleGenerator()

        concept = Concept(
            name="Case Study Concept",
            type=ConceptType.TERM,
            definition="A concept with case studies.",
            criteria="Technology",
            applications=[],
            cases=["Case 1: Implementation in healthcare", "Case 2: Use in finance"],
            formulas=[],
            related_concepts=[],
            backlinks=[]
        )

        article = generator.generate_article(concept)

        # Should include cases in key points section
        assert "## Key Points" in article
        assert "### Case Study Concept" in article
        assert "Case 1: Implementation in healthcare" in article
        assert "Case 2: Use in finance" in article

    def test_generate_articles_multiple(self):
        """Test generating multiple articles."""
        generator = ArticleGenerator()

        concepts = [
            Concept(
                name="Concept 1",
                type=ConceptType.TERM,
                definition="Definition 1",
                criteria="Category 1",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=[],
                backlinks=[]
            ),
            Concept(
                name="Concept 2",
                type=ConceptType.TERM,
                definition="Definition 2",
                criteria="Category 2",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=[],
                backlinks=[]
            )
        ]

        articles = generator.generate_articles(concepts)

        # Should generate two articles
        assert len(articles) == 2
        assert articles[0].startswith("# Concept 1")
        assert articles[1].startswith("# Concept 2")

    def test_generate_articles_empty_list(self):
        """Test generating articles with empty list."""
        generator = ArticleGenerator()

        articles = generator.generate_articles([])

        # Should return empty list
        assert len(articles) == 0

    def test_template_loading(self):
        """Test that template loads correctly."""
        generator = ArticleGenerator()

        # Check that template path is set
        assert generator.template_path is not None
        assert generator.template_path.exists()

    def test_article_formatting(self):
        """Test that article is properly formatted."""
        generator = ArticleGenerator()

        concept = Concept(
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

        article = generator.generate_article(concept)

        # Check proper markdown formatting
        assert article.startswith("# Test Concept")
        assert "## Overview" in article
        assert "## Definition" in article
        assert "## Category" in article
        assert "## Related Concepts" in article
        assert "## Applications" in article
        assert "## Key Points" in article
        assert "## Formulas" in article
        assert "## Examples" in article
        assert "## Related Topics" in article
        assert "*Generated on" in article
        assert "using Knowledge Compiler*" in article

    def test_article_with_complex_content(self):
        """Test generating article with complex content."""
        generator = ArticleGenerator()

        concept = Concept(
            name="Complex Concept",
            type=ConceptType.TERM,
            definition="A complex concept with multiple properties.",
            criteria="Complex Category",
            applications=[
                {"name": "Application 1", "description": "First application description"},
                {"name": "Application 2", "description": "Second application description"}
            ],
            cases=["Case 1: Complex case study", "Case 2: Another complex case"],
            formulas=["Formula 1: F = ma", "Formula 2: E = mc²"],
            related_concepts=["Related Concept 1", "Related Concept 2"],
            backlinks=[]
        )

        article = generator.generate_article(concept)

        # Check all complex content is included
        assert "### Complex Concept" in article
        assert "Application 1" in article
        assert "First application description" in article
        assert "Application 2" in article
        assert "Second application description" in article
        assert "Case 1: Complex case study" in article
        assert "Case 2: Another complex case" in article
        assert "Formula 1: F = ma" in article
        assert "Formula 2: E = mc²" in article
        assert "- Related Concept 1" in article
        assert "- Related Concept 2" in article

    def test_article_date_inclusion(self):
        """Test that article includes generation date."""
        generator = ArticleGenerator()

        concept = Concept(
            name="Dated Concept",
            type=ConceptType.TERM,
            definition="A concept with a date.",
            criteria="Category",
            applications=[],
            cases=[],
            formulas=[],
            related_concepts=[],
            backlinks=[]
        )

        article = generator.generate_article(concept)

        # Check date is included
        assert "*Generated on" in article
        assert datetime.now().strftime("%Y-%m-%d") in article