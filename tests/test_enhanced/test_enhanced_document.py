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

def test_enhanced_document_add_concept_type_validation():
    """Test add_concept rejects non-EnhancedConcept"""
    from src.enhanced.models import EnhancedConcept, ConceptType

    doc = EnhancedDocument(
        source_type=SourceType.TEXT,
        content="Test content",
        metadata=DocumentMetadata(title="Test")
    )

    with pytest.raises(TypeError, match="concept must be an EnhancedConcept instance"):
        doc.add_concept("not a concept")

def test_enhanced_document_empty_title_validation():
    """Test DocumentMetadata rejects empty title"""
    with pytest.raises(ValueError, match="title must not be empty"):
        DocumentMetadata(
            title="",
            tags=["test"]
        )

def test_enhanced_document_empty_content_validation():
    """Test EnhancedDocument rejects empty content"""
    with pytest.raises(ValueError, match="content must not be empty"):
        EnhancedDocument(
            source_type=SourceType.TEXT,
            content="",
            metadata=DocumentMetadata(title="Test")
        )

def test_enhanced_document_whitespace_only_validation():
    """Test EnhancedDocument rejects whitespace-only content"""
    with pytest.raises(ValueError, match="content must not be empty"):
        EnhancedDocument(
            source_type=SourceType.TEXT,
            content="   ",
            metadata=DocumentMetadata(title="Test")
        )

def test_enhanced_document_find_concepts_by_type():
    """Test finding concepts by type"""
    from src.enhanced.models import EnhancedConcept, ConceptType

    doc = EnhancedDocument(
        source_type=SourceType.TEXT,
        content="Test content",
        metadata=DocumentMetadata(title="Test")
    )

    concept1 = EnhancedConcept(name="C1", type=ConceptType.ENTITY, definition="Entity")
    concept2 = EnhancedConcept(name="C2", type=ConceptType.ABSTRACT, definition="Abstract")
    concept3 = EnhancedConcept(name="C3", type=ConceptType.ENTITY, definition="Another entity")

    doc.add_concept(concept1)
    doc.add_concept(concept2)
    doc.add_concept(concept3)

    entities = doc.find_concepts_by_type(ConceptType.ENTITY)
    assert len(entities) == 2
    assert entities[0].name == "C1"
    assert entities[1].name == "C3"
