import pytest
import numpy as np
from datetime import datetime
from src.enhanced.models import EnhancedConcept, ConceptType, TemporalInfo

def test_enhanced_concept_creation():
    """Test creating an EnhancedConcept"""
    concept = EnhancedConcept(
        name="Test Concept",
        type=ConceptType.ENTITY,
        definition="A test concept for testing",
        confidence=0.8
    )

    assert concept.name == "Test Concept"
    assert concept.type == ConceptType.ENTITY
    assert concept.definition == "A test concept for testing"
    assert concept.confidence == 0.8
    assert concept.embeddings is None
    assert concept.properties == {}
    assert concept.relations == []
    assert concept.evidence == []

def test_enhanced_concept_with_embeddings():
    """Test EnhancedConcept with embeddings"""
    embeddings = np.array([0.1, 0.2, 0.3])
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test",
        embeddings=embeddings
    )

    assert concept.embeddings is not None
    assert np.array_equal(concept.embeddings, embeddings)

def test_enhanced_concept_add_evidence():
    """Test adding evidence to concept"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    concept.add_evidence("source1.md", "Quote here", 0.9)

    assert len(concept.evidence) == 1
    assert concept.evidence[0]["source"] == "source1.md"
    assert concept.evidence[0]["confidence"] == 0.9

def test_enhanced_concept_add_relation():
    """Test adding relation to concept"""
    concept = EnhancedConcept(
        name="Concept1",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    concept.add_relation("Concept2")

    assert "Concept2" in concept.relations

def test_enhanced_concept_update_confidence():
    """Test updating confidence"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test",
        confidence=0.5
    )

    concept.update_confidence(0.9)

    assert concept.confidence == 0.9

def test_enhanced_concept_confidence_validation_too_high():
    """Test confidence validation rejects values > 1.0"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test",
        confidence=0.5
    )

    with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
        concept.update_confidence(1.5)

def test_enhanced_concept_confidence_validation_too_low():
    """Test confidence validation rejects values < 0.0"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test",
        confidence=0.5
    )

    with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
        concept.update_confidence(-0.1)

def test_enhanced_concept_evidence_timestamp():
    """Test evidence includes added_at timestamp"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    concept.add_evidence("source1.md", "Quote", 0.9)

    assert "added_at" in concept.evidence[0]
    assert isinstance(concept.evidence[0]["added_at"], str)

def test_enhanced_concept_temporal_info():
    """Test TemporalInfo fields"""
    from datetime import datetime

    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test",
        temporal_info=TemporalInfo(
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    )

    assert concept.temporal_info is not None
    assert concept.temporal_info.created_at is not None
    assert concept.temporal_info.updated_at is not None

def test_enhanced_concept_source_documents():
    """Test source_documents attribute"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test",
        source_documents=["doc1.md", "doc2.md"]
    )

    assert len(concept.source_documents) == 2
    assert "doc1.md" in concept.source_documents

def test_enhanced_concept_properties():
    """Test properties dictionary"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    concept.properties["key1"] = "value1"

    assert concept.properties["key1"] == "value1"

def test_enhanced_concept_duplicate_relation_prevention():
    """Test adding duplicate relation doesn't create duplicate"""
    concept = EnhancedConcept(
        name="Concept1",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    concept.add_relation("Concept2")
    concept.add_relation("Concept2")

    assert concept.relations.count("Concept2") == 1

def test_enhanced_concept_add_evidence_validation_empty_source():
    """Test add_evidence rejects empty source"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    with pytest.raises(ValueError, match="Source cannot be empty"):
        concept.add_evidence("", "Quote", 0.9)

def test_enhanced_concept_add_evidence_validation_empty_quote():
    """Test add_evidence rejects empty quote"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    with pytest.raises(ValueError, match="Quote cannot be empty"):
        concept.add_evidence("source.md", "", 0.9)

def test_enhanced_concept_add_evidence_validation_invalid_confidence():
    """Test add_evidence rejects invalid confidence"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
        concept.add_evidence("source.md", "Quote", 1.5)

def test_enhanced_concept_add_relation_validation_empty():
    """Test add_relation rejects empty concept name"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    with pytest.raises(ValueError, match="Concept name cannot be empty"):
        concept.add_relation("")
