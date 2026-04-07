import pytest
import numpy as np
from datetime import datetime
from src.enhanced.models import EnhancedConcept, ConceptType

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
