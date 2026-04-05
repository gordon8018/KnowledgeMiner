"""Unit tests for EnhancedDocument model."""

import pytest
import numpy as np
from datetime import datetime
from pydantic import ValidationError

from src.core.base_models import SourceType, ProcessingStatus


def test_document_metadata_creation():
    """Test creating DocumentMetadata with all fields"""
    from src.core.document_model import DocumentMetadata

    metadata = DocumentMetadata(
        title="Test Document",
        author="Test Author",
        date=datetime.now(),
        tags=["test", "document"],
        source_url="https://example.com",
        file_path="/path/to/file.pdf"
    )

    assert metadata.title == "Test Document"
    assert metadata.author == "Test Author"
    assert len(metadata.tags) == 2
    assert metadata.source_url == "https://example.com"
    assert metadata.file_path == "/path/to/file.pdf"


def test_document_metadata_defaults():
    """Test DocumentMetadata with optional fields as None"""
    from src.core.document_model import DocumentMetadata

    metadata = DocumentMetadata()

    assert metadata.title is None
    assert metadata.author is None
    assert metadata.date is None
    assert metadata.tags == []
    assert metadata.source_url is None
    assert metadata.file_path is None


def test_document_metadata_with_partial_data():
    """Test DocumentMetadata with only some fields"""
    from src.core.document_model import DocumentMetadata

    metadata = DocumentMetadata(
        title="Partial Document",
        tags=["partial"]
    )

    assert metadata.title == "Partial Document"
    assert metadata.author is None
    assert metadata.tags == ["partial"]


def test_enhanced_document_creation():
    """Test creating EnhancedDocument with all required fields"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Test Doc")
    doc = EnhancedDocument(
        id="doc-123",
        source_type=SourceType.PDF,
        content="This is test content",
        metadata=metadata,
        quality_score=0.8,
        processing_status=ProcessingStatus.PROCESSED
    )

    assert doc.id == "doc-123"
    assert doc.source_type == SourceType.PDF
    assert doc.content == "This is test content"
    assert doc.quality_score == 0.8
    assert doc.processing_status == ProcessingStatus.PROCESSED
    assert doc.concepts == []
    assert doc.relations == []
    assert doc.embeddings is None


def test_enhanced_document_with_embeddings():
    """Test EnhancedDocument with numpy array embeddings"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Test Doc")
    embeddings = np.array([0.1, 0.2, 0.3, 0.4])

    doc = EnhancedDocument(
        id="doc-456",
        source_type=SourceType.TEXT,
        content="Content with embeddings",
        metadata=metadata,
        embeddings=embeddings
    )

    assert doc.embeddings is not None
    assert isinstance(doc.embeddings, np.ndarray)
    assert len(doc.embeddings) == 4
    assert np.allclose(doc.embeddings, embeddings)


def test_enhanced_document_quality_score_validation():
    """Test that quality_score must be between 0.0 and 1.0"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Test Doc")

    # Valid scores
    doc1 = EnhancedDocument(
        id="doc-valid-1",
        source_type=SourceType.PDF,
        content="Valid content",
        metadata=metadata,
        quality_score=0.0
    )
    assert doc1.quality_score == 0.0

    doc2 = EnhancedDocument(
        id="doc-valid-2",
        source_type=SourceType.PDF,
        content="Valid content",
        metadata=metadata,
        quality_score=1.0
    )
    assert doc2.quality_score == 1.0

    doc3 = EnhancedDocument(
        id="doc-valid-3",
        source_type=SourceType.PDF,
        content="Valid content",
        metadata=metadata,
        quality_score=0.5
    )
    assert doc3.quality_score == 0.5

    # Invalid scores
    with pytest.raises(ValidationError) as exc_info:
        EnhancedDocument(
            id="doc-invalid-1",
            source_type=SourceType.PDF,
            content="Invalid content",
            metadata=metadata,
            quality_score=-0.1
        )
    assert "quality_score" in str(exc_info.value).lower()

    with pytest.raises(ValidationError) as exc_info:
        EnhancedDocument(
            id="doc-invalid-2",
            source_type=SourceType.PDF,
            content="Invalid content",
            metadata=metadata,
            quality_score=1.1
        )
    assert "quality_score" in str(exc_info.value).lower()


def test_enhanced_document_source_types():
    """Test EnhancedDocument with different source types"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Source Type Test")

    source_types = [
        SourceType.WEB_CLIPPER,
        SourceType.PDF,
        SourceType.MARKDOWN,
        SourceType.TEXT,
        SourceType.IMAGE
    ]

    for i, source_type in enumerate(source_types):
        doc = EnhancedDocument(
            id=f"doc-source-{i}",
            source_type=source_type,
            content=f"Content for {source_type.value}",
            metadata=metadata
        )
        assert doc.source_type == source_type


def test_enhanced_document_processing_statuses():
    """Test EnhancedDocument with different processing statuses"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Status Test")

    statuses = [
        ProcessingStatus.PENDING,
        ProcessingStatus.PROCESSING,
        ProcessingStatus.PROCESSED,
        ProcessingStatus.FAILED,
        ProcessingStatus.SKIPPED
    ]

    for i, status in enumerate(statuses):
        doc = EnhancedDocument(
            id=f"doc-status-{i}",
            source_type=SourceType.TEXT,
            content=f"Content with status {status.value}",
            metadata=metadata,
            processing_status=status
        )
        assert doc.processing_status == status


def test_enhanced_document_add_concept():
    """Test adding concepts to EnhancedDocument"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Concept Test")
    doc = EnhancedDocument(
        id="doc-concepts",
        source_type=SourceType.TEXT,
        content="Content about concepts",
        metadata=metadata
    )

    assert doc.concepts == []

    # Add single concept
    doc.add_concept("concept-1")
    assert len(doc.concepts) == 1
    assert "concept-1" in doc.concepts

    # Add multiple concepts
    doc.add_concept("concept-2")
    doc.add_concept("concept-3")
    assert len(doc.concepts) == 3
    assert "concept-2" in doc.concepts
    assert "concept-3" in doc.concepts

    # Add duplicate concept (should not add again)
    doc.add_concept("concept-1")
    assert len(doc.concepts) == 3


def test_enhanced_document_add_relation():
    """Test adding relations to EnhancedDocument"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Relation Test")
    doc = EnhancedDocument(
        id="doc-relations",
        source_type=SourceType.TEXT,
        content="Content with relations",
        metadata=metadata
    )

    assert doc.relations == []

    # Add single relation
    doc.add_relation("relation-1")
    assert len(doc.relations) == 1
    assert "relation-1" in doc.relations

    # Add multiple relations
    doc.add_relation("relation-2")
    doc.add_relation("relation-3")
    assert len(doc.relations) == 3
    assert "relation-2" in doc.relations
    assert "relation-3" in doc.relations

    # Add duplicate relation (should not add again)
    doc.add_relation("relation-1")
    assert len(doc.relations) == 3


def test_enhanced_document_update_quality_score():
    """Test updating quality score with validation"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Quality Update Test")
    doc = EnhancedDocument(
        id="doc-quality",
        source_type=SourceType.TEXT,
        content="Content for quality test",
        metadata=metadata,
        quality_score=0.5
    )

    assert doc.quality_score == 0.5

    # Update to valid score
    doc.update_quality_score(0.8)
    assert doc.quality_score == 0.8

    # Update to boundary values
    doc.update_quality_score(0.0)
    assert doc.quality_score == 0.0

    doc.update_quality_score(1.0)
    assert doc.quality_score == 1.0

    # Try to update to invalid score (should raise ValueError)
    with pytest.raises(ValueError) as exc_info:
        doc.update_quality_score(-0.1)
    assert "quality_score" in str(exc_info.value).lower()

    with pytest.raises(ValueError) as exc_info:
        doc.update_quality_score(1.5)
    assert "quality_score" in str(exc_info.value).lower()

    # Verify score hasn't changed after failed update
    assert doc.quality_score == 1.0


def test_enhanced_document_inheritance():
    """Test that EnhancedDocument properly inherits from BaseModel"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Inheritance Test")
    doc = EnhancedDocument(
        id="doc-inherit",
        source_type=SourceType.TEXT,
        content="Content",
        metadata=metadata
    )

    # Check inherited fields exist
    assert hasattr(doc, 'id')
    assert hasattr(doc, 'created_at')
    assert hasattr(doc, 'updated_at')

    # Check inherited methods work
    assert isinstance(doc.created_at, datetime)
    assert isinstance(doc.updated_at, datetime)

    original_updated = doc.updated_at

    # Test inherited update_timestamp method
    import time
    time.sleep(0.01)
    doc.update_timestamp()

    assert doc.updated_at > original_updated

    # Test inherited to_dict method
    doc_dict = doc.to_dict()
    assert isinstance(doc_dict, dict)
    assert doc_dict["id"] == "doc-inherit"
    assert "created_at" in doc_dict
    assert "updated_at" in doc_dict


def test_enhanced_document_serialization():
    """Test EnhancedDocument serialization to dictionary"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(
        title="Serialization Test",
        author="Test Author",
        tags=["test", "serialization"]
    )

    doc = EnhancedDocument(
        id="doc-serial",
        source_type=SourceType.PDF,
        content="Content for serialization",
        metadata=metadata,
        quality_score=0.85,
        processing_status=ProcessingStatus.PROCESSED
    )

    doc.add_concept("concept-1")
    doc.add_relation("relation-1")

    doc_dict = doc.to_dict()

    # Verify all fields are serialized
    assert doc_dict["id"] == "doc-serial"
    assert doc_dict["source_type"] == "pdf"
    assert doc_dict["content"] == "Content for serialization"
    assert doc_dict["metadata"]["title"] == "Serialization Test"
    assert doc_dict["quality_score"] == 0.85
    assert doc_dict["processing_status"] == "processed"
    assert "concept-1" in doc_dict["concepts"]
    assert "relation-1" in doc_dict["relations"]
    assert "created_at" in doc_dict
    assert "updated_at" in doc_dict


def test_enhanced_document_model_dump():
    """Test EnhancedDocument model_dump with exclusions"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Model Dump Test")
    embeddings = np.array([0.1, 0.2, 0.3])

    doc = EnhancedDocument(
        id="doc-dump",
        source_type=SourceType.TEXT,
        content="Content",
        metadata=metadata,
        embeddings=embeddings
    )

    # Test model_dump with exclude
    dump_without_embeddings = doc.model_dump(exclude={'embeddings'})
    assert 'embeddings' not in dump_without_embeddings
    assert dump_without_embeddings['content'] == "Content"


def test_enhanced_document_copy():
    """Test creating a copy of EnhancedDocument"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Copy Test")
    doc = EnhancedDocument(
        id="doc-copy",
        source_type=SourceType.TEXT,
        content="Original content",
        metadata=metadata,
        quality_score=0.7
    )

    doc.add_concept("concept-1")

    # Create copy
    doc_copy = doc.model_copy()

    # Verify copy has same data
    assert doc_copy.id == doc.id
    assert doc_copy.content == doc.content
    assert doc_copy.quality_score == doc.quality_score
    assert "concept-1" in doc_copy.concepts

    # Modify copy shouldn't affect original
    doc_copy.add_concept("concept-2")
    assert "concept-2" in doc_copy.concepts
    assert "concept-2" not in doc.concepts


def test_enhanced_document_default_values():
    """Test EnhancedDocument with default values"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    metadata = DocumentMetadata(title="Defaults Test")
    doc = EnhancedDocument(
        id="doc-defaults",
        source_type=SourceType.TEXT,
        content="Content",
        metadata=metadata
    )

    # Check default values
    assert doc.embeddings is None
    assert doc.concepts == []
    assert doc.relations == []
    assert doc.quality_score == 0.5  # Default should be 0.5
    assert doc.processing_status == ProcessingStatus.PENDING  # Default should be PENDING


def test_enhanced_document_edge_cases():
    """Test edge cases for EnhancedDocument"""
    from src.core.document_model import EnhancedDocument, DocumentMetadata

    # Empty content
    metadata = DocumentMetadata(title="Edge Case")
    doc1 = EnhancedDocument(
        id="doc-empty",
        source_type=SourceType.TEXT,
        content="",
        metadata=metadata
    )
    assert doc1.content == ""

    # Very long content
    long_content = "A" * 10000
    doc2 = EnhancedDocument(
        id="doc-long",
        source_type=SourceType.TEXT,
        content=long_content,
        metadata=metadata
    )
    assert len(doc2.content) == 10000

    # Many concepts and relations
    doc3 = EnhancedDocument(
        id="doc-many",
        source_type=SourceType.TEXT,
        content="Content",
        metadata=metadata
    )
    for i in range(100):
        doc3.add_concept(f"concept-{i}")
        doc3.add_relation(f"relation-{i}")

    assert len(doc3.concepts) == 100
    assert len(doc3.relations) == 100
