"""Unit tests for EnhancedConcept model."""

import pytest
import numpy as np
from datetime import datetime
from pydantic import ValidationError

from src.core.base_models import BaseModel


def test_concept_type_enum_values():
    """Test ConceptType enum has all required values"""
    from src.core.concept_model import ConceptType

    # Test all enum values exist
    assert hasattr(ConceptType, 'TERM')
    assert hasattr(ConceptType, 'INDICATOR')
    assert hasattr(ConceptType, 'STRATEGY')
    assert hasattr(ConceptType, 'THEORY')
    assert hasattr(ConceptType, 'PERSON')

    # Test enum values are correct
    assert ConceptType.TERM.value == "term"
    assert ConceptType.INDICATOR.value == "indicator"
    assert ConceptType.STRATEGY.value == "strategy"
    assert ConceptType.THEORY.value == "theory"
    assert ConceptType.PERSON.value == "person"

    # Test enum inherits from str and Enum
    assert issubclass(ConceptType, str)
    assert issubclass(ConceptType, type(ConceptType.TERM).__bases__[1].__mro__[1])  # Enum check


def test_temporal_info_creation():
    """Test creating TemporalInfo with all fields"""
    from src.core.concept_model import TemporalInfo

    now = datetime.now()
    valid_start = datetime(2024, 1, 1)
    valid_end = datetime(2024, 12, 31)

    temporal = TemporalInfo(
        created=now,
        modified=now,
        valid_period=(valid_start, valid_end)
    )

    assert temporal.created == now
    assert temporal.modified == now
    assert temporal.valid_period == (valid_start, valid_end)


def test_temporal_info_defaults():
    """Test TemporalInfo with optional fields as None"""
    from src.core.concept_model import TemporalInfo

    temporal = TemporalInfo()

    assert temporal.created is None
    assert temporal.modified is None
    assert temporal.valid_period is None


def test_temporal_info_with_partial_data():
    """Test TemporalInfo with only some fields"""
    from src.core.concept_model import TemporalInfo

    now = datetime.now()

    temporal = TemporalInfo(created=now)

    assert temporal.created == now
    assert temporal.modified is None
    assert temporal.valid_period is None


def test_enhanced_concept_creation():
    """Test creating EnhancedConcept with all required fields"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-123",
        name="Test Concept",
        type=ConceptType.TERM,
        definition="A test concept definition"
    )

    assert concept.id == "concept-123"
    assert concept.name == "Test Concept"
    assert concept.type == ConceptType.TERM
    assert concept.definition == "A test concept definition"
    assert concept.embeddings is None
    assert concept.properties == {}
    assert concept.relations == []
    assert concept.evidence == []
    assert concept.confidence == 0.5
    assert concept.temporal_info is None
    assert concept.source_documents == []


def test_enhanced_concept_with_all_fields():
    """Test creating EnhancedConcept with all optional fields"""
    from src.core.concept_model import EnhancedConcept, ConceptType, TemporalInfo

    embeddings = np.array([0.1, 0.2, 0.3, 0.4])
    temporal = TemporalInfo(created=datetime.now())

    concept = EnhancedConcept(
        id="concept-full",
        name="Full Concept",
        type=ConceptType.INDICATOR,
        definition="Full definition",
        embeddings=embeddings,
        properties={"key": "value", "number": 42},
        relations=["rel-1", "rel-2"],
        evidence=[
            {"source": "doc-1", "quote": "Test quote", "confidence": 0.9}
        ],
        confidence=0.85,
        temporal_info=temporal,
        source_documents=["doc-1", "doc-2"]
    )

    assert concept.id == "concept-full"
    assert concept.name == "Full Concept"
    assert concept.type == ConceptType.INDICATOR
    assert concept.embeddings is not None
    assert isinstance(concept.embeddings, np.ndarray)
    assert len(concept.embeddings) == 4
    assert concept.properties == {"key": "value", "number": 42}
    assert len(concept.relations) == 2
    assert len(concept.evidence) == 1
    assert concept.confidence == 0.85
    assert concept.temporal_info is not None
    assert len(concept.source_documents) == 2


def test_enhanced_concept_confidence_validation():
    """Test that confidence must be between 0.0 and 1.0"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    # Valid confidence scores
    concept1 = EnhancedConcept(
        id="concept-valid-1",
        name="Valid 1",
        type=ConceptType.TERM,
        definition="Test",
        confidence=0.0
    )
    assert concept1.confidence == 0.0

    concept2 = EnhancedConcept(
        id="concept-valid-2",
        name="Valid 2",
        type=ConceptType.TERM,
        definition="Test",
        confidence=1.0
    )
    assert concept2.confidence == 1.0

    concept3 = EnhancedConcept(
        id="concept-valid-3",
        name="Valid 3",
        type=ConceptType.TERM,
        definition="Test",
        confidence=0.5
    )
    assert concept3.confidence == 0.5

    # Invalid confidence scores
    with pytest.raises(ValidationError) as exc_info:
        EnhancedConcept(
            id="concept-invalid-1",
            name="Invalid 1",
            type=ConceptType.TERM,
            definition="Test",
            confidence=-0.1
        )
    assert "confidence" in str(exc_info.value).lower()

    with pytest.raises(ValidationError) as exc_info:
        EnhancedConcept(
            id="concept-invalid-2",
            name="Invalid 2",
            type=ConceptType.TERM,
            definition="Test",
            confidence=1.1
        )
    assert "confidence" in str(exc_info.value).lower()


def test_enhanced_concept_default_confidence():
    """Test that confidence defaults to 0.5"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-default",
        name="Default Confidence",
        type=ConceptType.TERM,
        definition="Test"
    )

    assert concept.confidence == 0.5


def test_enhanced_concept_with_embeddings():
    """Test EnhancedConcept with numpy array embeddings"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    embeddings = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

    concept = EnhancedConcept(
        id="concept-embeddings",
        name="Embeddings Concept",
        type=ConceptType.STRATEGY,
        definition="Test with embeddings",
        embeddings=embeddings
    )

    assert concept.embeddings is not None
    assert isinstance(concept.embeddings, np.ndarray)
    assert len(concept.embeddings) == 5
    assert np.allclose(concept.embeddings, embeddings)


def test_enhanced_concept_properties_handling():
    """Test EnhancedConcept properties dictionary"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-props",
        name="Properties Concept",
        type=ConceptType.THEORY,
        definition="Test properties",
        properties={"key1": "value1", "key2": 42}
    )

    assert concept.properties == {"key1": "value1", "key2": 42}

    # Update properties
    concept.properties["key3"] = [1, 2, 3]
    assert concept.properties["key3"] == [1, 2, 3]


def test_enhanced_concept_relations_handling():
    """Test EnhancedConcept relations list"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-relations",
        name="Relations Concept",
        type=ConceptType.PERSON,
        definition="Test relations",
        relations=["rel-1", "rel-2", "rel-3"]
    )

    assert len(concept.relations) == 3
    assert "rel-1" in concept.relations
    assert "rel-2" in concept.relations
    assert "rel-3" in concept.relations


def test_enhanced_concept_evidence_handling():
    """Test EnhancedConcept evidence list"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    evidence_list = [
        {"source": "doc-1", "quote": "Quote 1", "confidence": 0.9},
        {"source": "doc-2", "quote": "Quote 2", "confidence": 0.8},
        {"source": "doc-3", "quote": "Quote 3", "confidence": 0.95}
    ]

    concept = EnhancedConcept(
        id="concept-evidence",
        name="Evidence Concept",
        type=ConceptType.INDICATOR,
        definition="Test evidence",
        evidence=evidence_list
    )

    assert len(concept.evidence) == 3
    assert concept.evidence[0]["source"] == "doc-1"
    assert concept.evidence[1]["confidence"] == 0.8


def test_enhanced_concept_source_documents_handling():
    """Test EnhancedConcept source_documents list"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-sources",
        name="Sources Concept",
        type=ConceptType.TERM,
        definition="Test source documents",
        source_documents=["doc-1", "doc-2", "doc-3"]
    )

    assert len(concept.source_documents) == 3
    assert "doc-1" in concept.source_documents
    assert "doc-2" in concept.source_documents
    assert "doc-3" in concept.source_documents


def test_enhanced_concept_add_evidence():
    """Test adding evidence to EnhancedConcept"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-add-evidence",
        name="Add Evidence",
        type=ConceptType.TERM,
        definition="Test"
    )

    assert concept.evidence == []

    # Add first evidence
    concept.add_evidence("doc-1", "First quote", 0.9)
    assert len(concept.evidence) == 1
    assert concept.evidence[0]["source"] == "doc-1"
    assert concept.evidence[0]["quote"] == "First quote"
    assert concept.evidence[0]["confidence"] == 0.9

    # Add more evidence
    concept.add_evidence("doc-2", "Second quote", 0.8)
    concept.add_evidence("doc-3", "Third quote", 0.95)

    assert len(concept.evidence) == 3
    assert concept.evidence[1]["source"] == "doc-2"
    assert concept.evidence[2]["confidence"] == 0.95


def test_enhanced_concept_add_source_document():
    """Test adding source documents to EnhancedConcept"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-add-source",
        name="Add Source",
        type=ConceptType.TERM,
        definition="Test"
    )

    assert concept.source_documents == []

    # Add single source document
    concept.add_source_document("doc-1")
    assert len(concept.source_documents) == 1
    assert "doc-1" in concept.source_documents

    # Add more source documents
    concept.add_source_document("doc-2")
    concept.add_source_document("doc-3")

    assert len(concept.source_documents) == 3
    assert "doc-2" in concept.source_documents
    assert "doc-3" in concept.source_documents

    # Add duplicate (should not add again)
    concept.add_source_document("doc-1")
    assert len(concept.source_documents) == 3


def test_enhanced_concept_update_confidence():
    """Test updating confidence with validation"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-update-confidence",
        name="Update Confidence",
        type=ConceptType.TERM,
        definition="Test",
        confidence=0.5
    )

    assert concept.confidence == 0.5

    # Update to valid confidence
    concept.update_confidence(0.8)
    assert concept.confidence == 0.8

    # Update to boundary values
    concept.update_confidence(0.0)
    assert concept.confidence == 0.0

    concept.update_confidence(1.0)
    assert concept.confidence == 1.0

    # Try to update to invalid confidence (should raise ValueError)
    with pytest.raises(ValueError) as exc_info:
        concept.update_confidence(-0.1)
    assert "confidence" in str(exc_info.value).lower()

    with pytest.raises(ValueError) as exc_info:
        concept.update_confidence(1.5)
    assert "confidence" in str(exc_info.value).lower()

    # Verify confidence hasn't changed after failed update
    assert concept.confidence == 1.0


def test_enhanced_concept_inheritance():
    """Test that EnhancedConcept properly inherits from BaseModel"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-inherit",
        name="Inheritance Test",
        type=ConceptType.TERM,
        definition="Test inheritance"
    )

    # Check it's an instance of BaseModel
    assert isinstance(concept, BaseModel)

    # Check inherited fields exist
    assert hasattr(concept, 'id')
    assert hasattr(concept, 'created_at')
    assert hasattr(concept, 'updated_at')

    # Check inherited methods work
    assert isinstance(concept.created_at, datetime)
    assert isinstance(concept.updated_at, datetime)

    original_updated = concept.updated_at

    # Test inherited update_timestamp method
    import time
    time.sleep(0.01)
    concept.update_timestamp()

    assert concept.updated_at > original_updated

    # Test inherited to_dict method
    concept_dict = concept.to_dict()
    assert isinstance(concept_dict, dict)
    assert concept_dict["id"] == "concept-inherit"
    assert "created_at" in concept_dict
    assert "updated_at" in concept_dict


def test_enhanced_concept_all_concept_types():
    """Test EnhancedConcept with all concept types"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept_types = [
        ConceptType.TERM,
        ConceptType.INDICATOR,
        ConceptType.STRATEGY,
        ConceptType.THEORY,
        ConceptType.PERSON
    ]

    for i, concept_type in enumerate(concept_types):
        concept = EnhancedConcept(
            id=f"concept-type-{i}",
            name=f"{concept_type.value.title()} Concept",
            type=concept_type,
            definition=f"Test {concept_type.value} concept"
        )
        assert concept.type == concept_type


def test_enhanced_concept_serialization():
    """Test EnhancedConcept serialization to dictionary"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-serial",
        name="Serialization Test",
        type=ConceptType.INDICATOR,
        definition="Test serialization",
        properties={"key": "value"},
        confidence=0.75
    )

    concept.add_source_document("doc-1")
    concept.add_evidence("doc-1", "Test quote", 0.8)

    concept_dict = concept.to_dict()

    # Verify all fields are serialized
    assert concept_dict["id"] == "concept-serial"
    assert concept_dict["name"] == "Serialization Test"
    assert concept_dict["type"] == "indicator"
    assert concept_dict["definition"] == "Test serialization"
    assert concept_dict["properties"] == {"key": "value"}
    assert concept_dict["confidence"] == 0.75
    assert "doc-1" in concept_dict["source_documents"]
    assert len(concept_dict["evidence"]) == 1
    assert "created_at" in concept_dict
    assert "updated_at" in concept_dict


def test_enhanced_concept_model_dump():
    """Test EnhancedConcept model_dump with exclusions"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    embeddings = np.array([0.1, 0.2, 0.3])

    concept = EnhancedConcept(
        id="concept-dump",
        name="Model Dump Test",
        type=ConceptType.TERM,
        definition="Test",
        embeddings=embeddings
    )

    # Test model_dump with exclude
    dump_without_embeddings = concept.model_dump(exclude={'embeddings'})
    assert 'embeddings' not in dump_without_embeddings
    assert dump_without_embeddings['name'] == "Model Dump Test"


def test_enhanced_concept_copy():
    """Test creating a copy of EnhancedConcept"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-copy",
        name="Copy Test",
        type=ConceptType.THEORY,
        definition="Test copy",
        confidence=0.7
    )

    concept.add_source_document("doc-1")
    concept.add_evidence("doc-1", "Quote", 0.9)

    # Create copy
    concept_copy = concept.model_copy()

    # Verify copy has same data
    assert concept_copy.id == concept.id
    assert concept_copy.name == concept.name
    assert concept_copy.confidence == concept.confidence
    assert "doc-1" in concept_copy.source_documents
    assert len(concept_copy.evidence) == 1

    # Modify copy shouldn't affect original
    concept_copy.add_source_document("doc-2")
    assert "doc-2" in concept_copy.source_documents
    assert "doc-2" not in concept.source_documents


def test_enhanced_concept_edge_cases():
    """Test edge cases for EnhancedConcept"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    # Empty definition
    concept1 = EnhancedConcept(
        id="concept-empty-def",
        name="Empty Definition",
        type=ConceptType.TERM,
        definition=""
    )
    assert concept1.definition == ""

    # Very long definition
    long_definition = "A" * 10000
    concept2 = EnhancedConcept(
        id="concept-long-def",
        name="Long Definition",
        type=ConceptType.TERM,
        definition=long_definition
    )
    assert len(concept2.definition) == 10000

    # Empty properties dict
    concept3 = EnhancedConcept(
        id="concept-empty-props",
        name="Empty Props",
        type=ConceptType.TERM,
        definition="Test",
        properties={}
    )
    assert concept3.properties == {}

    # Many relations and source documents
    concept4 = EnhancedConcept(
        id="concept-many",
        name="Many Items",
        type=ConceptType.TERM,
        definition="Test"
    )
    for i in range(100):
        concept4.relations.append(f"rel-{i}")
        concept4.add_source_document(f"doc-{i}")

    assert len(concept4.relations) == 100
    assert len(concept4.source_documents) == 100

    # Complex properties
    complex_props = {
        "nested": {"key": "value"},
        "list": [1, 2, 3],
        "mixed": [{"a": 1}, {"b": 2}]
    }
    concept5 = EnhancedConcept(
        id="concept-complex-props",
        name="Complex Props",
        type=ConceptType.TERM,
        definition="Test",
        properties=complex_props
    )
    assert concept5.properties == complex_props


def test_enhanced_concept_temporal_info_integration():
    """Test EnhancedConcept with TemporalInfo"""
    from src.core.concept_model import EnhancedConcept, ConceptType, TemporalInfo

    now = datetime.now()
    temporal = TemporalInfo(
        created=now,
        modified=now,
        valid_period=(datetime(2024, 1, 1), datetime(2024, 12, 31))
    )

    concept = EnhancedConcept(
        id="concept-temporal",
        name="Temporal Test",
        type=ConceptType.THEORY,
        definition="Test temporal info",
        temporal_info=temporal
    )

    assert concept.temporal_info is not None
    assert concept.temporal_info.created == now
    assert concept.temporal_info.modified == now
    assert concept.temporal_info.valid_period is not None
    assert concept.temporal_info.valid_period[0] == datetime(2024, 1, 1)
    assert concept.temporal_info.valid_period[1] == datetime(2024, 12, 31)


def test_enhanced_concept_with_none_temporal_info():
    """Test EnhancedConcept with None temporal_info"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    concept = EnhancedConcept(
        id="concept-no-temporal",
        name="No Temporal",
        type=ConceptType.TERM,
        definition="Test",
        temporal_info=None
    )

    assert concept.temporal_info is None


def test_enhanced_concept_evidence_structure():
    """Test evidence dictionary structure validation"""
    from src.core.concept_model import EnhancedConcept, ConceptType

    # Valid evidence structures
    concept = EnhancedConcept(
        id="concept-evidence-struct",
        name="Evidence Structure",
        type=ConceptType.TERM,
        definition="Test"
    )

    concept.add_evidence("doc-1", "Quote 1", 0.9)
    concept.add_evidence("doc-2", "Quote 2", 0.8)

    # Verify evidence structure
    assert all("source" in ev for ev in concept.evidence)
    assert all("quote" in ev for ev in concept.evidence)
    assert all("confidence" in ev for ev in concept.evidence)

    # Verify confidence values are valid
    assert all(0.0 <= ev["confidence"] <= 1.0 for ev in concept.evidence)
