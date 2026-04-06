import pytest
import re
from src.extractors.patterns import ExtractionPatterns
from src.extractors.concept_extractor import ConceptExtractor
from src.models.concept import Concept


class TestExtractionPatterns:
    """Test cases for ExtractionPatterns class."""

    def test_init_patterns(self):
        """Test that patterns are initialized correctly."""
        patterns = ExtractionPatterns()

        # Check that all required patterns are present
        assert hasattr(patterns, 'concept_pattern')
        assert hasattr(patterns, 'definition_pattern')
        assert hasattr(patterns, 'category_pattern')
        assert hasattr(patterns, 'relation_pattern')
        assert hasattr(patterns, 'example_pattern')

        # Check that patterns are compiled regex objects
        assert isinstance(patterns.concept_pattern, re.Pattern)
        assert isinstance(patterns.definition_pattern, re.Pattern)
        assert isinstance(patterns.category_pattern, re.Pattern)
        assert isinstance(patterns.relation_pattern, re.Pattern)
        assert isinstance(patterns.example_pattern, re.Pattern)

    def test_concept_pattern_matches(self):
        """Test concept pattern matching."""
        patterns = ExtractionPatterns()

        # Test matching concepts
        text1 = "# Machine Learning\nMachine learning is a subset of AI."
        match1 = patterns.concept_pattern.search(text1)
        assert match1 is not None
        assert match1.group(2) == "Machine Learning"

        # Test with different heading formats
        text2 = "## Deep Learning\nDeep learning uses neural networks."
        match2 = patterns.concept_pattern.search(text2)
        assert match2 is not None
        assert match2.group(2) == "Deep Learning"

        # Test non-concept text
        text3 = "This is just regular text."
        match3 = patterns.concept_pattern.search(text3)
        assert match3 is None

    def test_definition_pattern_matches(self):
        """Test definition pattern matching."""
        patterns = ExtractionPatterns()

        # Test simple definition
        text1 = "**Definition:** Machine learning is the study of computer algorithms."
        match1 = patterns.definition_pattern.search(text1)
        assert match1 is not None
        assert "machine learning is the study of computer algorithms" in match1.group(1).lower()

        # Test definition with different keywords
        text2 = "**Definition:** Deep learning is a subfield of machine learning."
        match2 = patterns.definition_pattern.search(text2)
        assert match2 is not None
        assert "deep learning" in match2.group(1).lower()

        # Test without definition marker
        text3 = "This is just a statement."
        match3 = patterns.definition_pattern.search(text3)
        assert match3 is None

    def test_category_pattern_matches(self):
        """Test category pattern matching."""
        patterns = ExtractionPatterns()

        # Test category with label
        text1 = "**Category:** Technology"
        match1 = patterns.category_pattern.search(text1)
        assert match1 is not None
        assert match1.group(1) == "Technology"

        # Test category with different formats
        text2 = "**Category:** Computer Science"
        match2 = patterns.category_pattern.search(text2)
        assert match2 is not None
        assert match2.group(1) == "Computer Science"

        # Test without category marker
        text3 = "This has no category."
        match3 = patterns.category_pattern.search(text3)
        assert match3 is None

    def test_relation_pattern_matches(self):
        """Test relation pattern matching."""
        patterns = ExtractionPatterns()

        # Test related to relation
        text1 = "**Related to:** Artificial Intelligence, Data Science"
        match1 = patterns.relation_pattern.search(text1)
        assert match1 is not None
        assert "artificial intelligence, data science" in match1.group(1).lower()

        # Test different relation keywords
        text2 = "**Also known as:** ML, ML algorithms"
        match2 = patterns.relation_pattern.search(text2)
        assert match2 is not None
        assert "ml, ml algorithms" in match2.group(1).lower()

        # Test without relation marker
        text3 = "This has no relations."
        match3 = patterns.relation_pattern.search(text3)
        assert match3 is None

    def test_example_pattern_matches(self):
        """Test example pattern matching."""
        patterns = ExtractionPatterns()

        # Test example with label
        text1 = "**Example:** Image classification is a common use case."
        match1 = patterns.example_pattern.search(text1)
        assert match1 is not None
        assert "image classification is a common use case" in match1.group(1).lower()

        # Test different example keywords
        text2 = "**Examples:** Netflix recommendation system, Amazon product suggestions"
        match2 = patterns.example_pattern.search(text2)
        assert match2 is not None
        assert "netflix recommendation system, amazon product suggestions" in match2.group(1).lower()

        # Test without example marker
        text3 = "This has no examples."
        match3 = patterns.example_pattern.search(text3)
        assert match3 is None


class TestConceptExtractor:
    """Test cases for ConceptExtractor class."""

    def test_init_extractor(self):
        """Test that ConceptExtractor initializes correctly."""
        extractor = ConceptExtractor()
        assert extractor.patterns is not None
        assert extractor.concepts == []
        assert extractor.current_concept is None

    def test_extract_concepts_from_markdown(self):
        """Test extracting concepts from markdown content."""
        extractor = ConceptExtractor()

        content = """
# Machine Learning
**Definition:** Machine learning is a subset of artificial intelligence that enables systems to learn from data.
**Category:** Technology
**Related to:** Artificial Intelligence, Data Science
**Example:** Email spam filters use machine learning algorithms.

## Deep Learning
**Definition:** Deep learning is a subfield of machine learning that uses neural networks.
**Category:** Technology
**Related to:** Machine Learning, Neural Networks
**Examples:** Image recognition, Natural language processing
        """

        concepts = extractor.extract_concepts(content)

        # Should extract two concepts
        assert len(concepts) == 2

        # Check first concept (Machine Learning)
        ml_concept = concepts[0]
        assert ml_concept.name == "Machine Learning"
        assert "machine learning is a subset of artificial intelligence that enables systems to learn from data" in ml_concept.definition.lower()
        assert ml_concept.criteria == "Technology"
        assert "artificial intelligence" in ml_concept.related_concepts
        assert "data science" in ml_concept.related_concepts
        # Check that the example is in applications
        ml_applications = [app['name'] for app in ml_concept.applications]
        assert "email spam filters use machine learning algorithms" in ml_applications[0]

        # Check second concept (Deep Learning)
        dl_concept = concepts[1]
        assert dl_concept.name == "Deep Learning"
        assert "deep learning is a subfield of machine learning that uses neural networks" in dl_concept.definition.lower()
        assert dl_concept.criteria == "Technology"
        assert "machine learning" in dl_concept.related_concepts
        assert "neural networks" in dl_concept.related_concepts

    def test_extract_concepts_no_content(self):
        """Test extracting concepts from empty content."""
        extractor = ConceptExtractor()
        concepts = extractor.extract_concepts("")
        assert len(concepts) == 0

    def test_extract_concepts_no_concepts(self):
        """Test extracting concepts when no concepts are present."""
        extractor = ConceptExtractor()

        content = """
This is just regular text with no concept headings.
It has some definitions but no proper concept structure.
**Definition:** This is a definition but not for a concept.
        """

        concepts = extractor.extract_concepts(content)
        assert len(concepts) == 0

    def test_concept_with_multiple_definitions(self):
        """Test concept with multiple definition patterns."""
        extractor = ConceptExtractor()

        content = """
# Supervised Learning
**Definition:** A type of machine learning where the algorithm learns from labeled data.
**Definition:** Also known as supervised machine learning.
**Category:** Machine Learning
**Related to:** Unsupervised Learning, Reinforcement Learning
        """

        concepts = extractor.extract_concepts(content)

        assert len(concepts) == 1
        concept = concepts[0]
        assert concept.name == "Supervised Learning"
        # Should contain both definitions
        assert "type of machine learning where the algorithm learns from labeled data" in concept.definition.lower()
        assert "also known as supervised machine learning" in concept.definition.lower()
        assert concept.criteria == "Machine Learning"
        assert "unsupervised learning" in concept.related_concepts
        assert "reinforcement learning" in concept.related_concepts

    def test_concept_with_multiple_relations(self):
        """Test concept with multiple relation patterns."""
        extractor = ConceptExtractor()

        content = """
# Neural Network
**Definition:** A computational model inspired by biological neural networks.
**Related to:** Machine Learning, Deep Learning
**Also known as:** Artificial Neural Network (ANN)
**Applications:** Image recognition, Natural language processing
        """

        concepts = extractor.extract_concepts(content)

        assert len(concepts) == 1
        concept = concepts[0]
        assert concept.name == "Neural Network"
        expected_relations = ["machine learning", "deep learning", "artificial neural network (ann)", "image recognition", "natural language processing"]
        for relation in expected_relations:
            assert relation in concept.related_concepts