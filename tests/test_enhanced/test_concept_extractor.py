import pytest
from src.enhanced.extractors.concept_extractor import ConceptExtractor
from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType


def test_extract_concepts_from_simple_text():
    """Test extracting concepts from simple text"""
    content = """
    Machine Learning is a subset of Artificial Intelligence.
    Deep Learning is a type of Machine Learning.
    """

    doc = EnhancedDocument(
        source_type=SourceType.TEXT,
        content=content,
        metadata=DocumentMetadata(title="ML Test")
    )

    extractor = ConceptExtractor()
    concepts = extractor.extract(doc)

    assert len(concepts) > 0
    # Should find key concepts like "Machine Learning", "Artificial Intelligence"
    concept_names = [c.name for c in concepts]
    assert any("Machine Learning" in name for name in concept_names)
