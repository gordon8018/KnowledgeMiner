import pytest
from src.enhanced.models import EnhancedDocument, SourceType, DocumentMetadata

def test_enhanced_document_creation():
    """Test creating an EnhancedDocument"""
    metadata = DocumentMetadata(
        title="Test Document",
        tags=["test", "example"],
        file_path="/path/to/doc.md"
    )

    doc = EnhancedDocument(
        source_type=SourceType.FILE,
        content="# Test Content\nThis is a test document.",
        metadata=metadata
    )

    assert doc.source_type == SourceType.FILE
    assert doc.content == "# Test Content\nThis is a test document."
    assert doc.metadata.title == "Test Document"
    assert doc.quality_score == 0.5
    assert doc.concepts == []

def test_enhanced_document_add_concept():
    """Test adding a concept to document"""
    from src.enhanced.models import EnhancedConcept, ConceptType

    doc = EnhancedDocument(
        source_type=SourceType.TEXT,
        content="Test content",
        metadata=DocumentMetadata(title="Test")
    )

    concept = EnhancedConcept(
        name="TestConcept",
        type=ConceptType.ABSTRACT,
        definition="A test concept"
    )

    doc.add_concept(concept)

    assert len(doc.concepts) == 1
    assert doc.concepts[0].name == "TestConcept"
