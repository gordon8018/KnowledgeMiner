"""Unit tests for Relation model."""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.core.relation_model import Relation, RelationType
from src.core.base_models import BaseModel
from src.core.concept_model import TemporalInfo


class TestRelationType:
    """Test RelationType enum"""

    def test_relation_type_enum_exists(self):
        """Test that RelationType enum exists"""
        assert RelationType is not None
        assert hasattr(RelationType, '__members__')

    def test_relation_type_has_all_values(self):
        """Test that RelationType has all 12 required values"""
        expected_types = {
            'RELATED_TO',
            'CAUSES',
            'CAUSED_BY',
            'CONTAINS',
            'CONTAINED_IN',
            'SIMILAR_TO',
            'OPPOSES',
            'SUPPORTS',
            'PRECEDES',
            'FOLLOWS',
            'DEPENDS_ON',
            'ENABLES',
        }
        actual_types = {member.name for member in RelationType}
        assert expected_types == actual_types

    def test_relation_type_values_are_strings(self):
        """Test that RelationType values are strings"""
        for member in RelationType:
            assert isinstance(member.value, str)
            assert len(member.value) > 0

    def test_relation_type_is_enum(self):
        """Test that RelationType is an Enum"""
        from enum import Enum
        assert issubclass(RelationType, Enum)


class TestRelationCreation:
    """Test Relation model creation and basic functionality"""

    def test_relation_creation_minimal(self):
        """Test creating a relation with minimal required fields"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
        )

        assert relation.id == "rel-1"
        assert relation.source_concept == "concept-1"
        assert relation.target_concept == "concept-2"
        assert relation.relation_type == RelationType.RELATED_TO
        assert relation.strength == 0.5  # default value
        assert relation.confidence == 0.5  # default value
        assert relation.evidence == []
        assert relation.temporal is None

    def test_relation_creation_with_all_fields(self):
        """Test creating a relation with all fields"""
        temporal = TemporalInfo(
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 1, 2),
        )

        relation = Relation(
            id="rel-2",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.CAUSES,
            strength=0.8,
            evidence=[
                {"source": "doc1", "quote": "Evidence 1", "confidence": 0.9},
            ],
            confidence=0.75,
            temporal=temporal,
        )

        assert relation.id == "rel-2"
        assert relation.source_concept == "concept-1"
        assert relation.target_concept == "concept-2"
        assert relation.relation_type == RelationType.CAUSES
        assert relation.strength == 0.8
        assert len(relation.evidence) == 1
        assert relation.confidence == 0.75
        assert relation.temporal is not None
        assert relation.temporal.created == datetime(2024, 1, 1)

    def test_relation_inherits_from_basemodel(self):
        """Test that Relation inherits from BaseModel"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
        )

        assert isinstance(relation, BaseModel)
        assert hasattr(relation, 'id')
        assert hasattr(relation, 'created_at')
        assert hasattr(relation, 'updated_at')
        assert isinstance(relation.created_at, datetime)
        assert isinstance(relation.updated_at, datetime)

    def test_relation_default_strength(self):
        """Test that strength has a default value of 0.5"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
        )

        assert relation.strength == 0.5

    def test_relation_default_confidence(self):
        """Test that confidence has a default value of 0.5"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
        )

        assert relation.confidence == 0.5

    def test_relation_default_evidence(self):
        """Test that evidence defaults to empty list"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
        )

        assert relation.evidence == []
        assert isinstance(relation.evidence, list)


class TestRelationValidation:
    """Test Relation model validation"""

    def test_strength_must_be_between_0_and_1(self):
        """Test that strength must be between 0.0 and 1.0"""
        # Valid values
        relation1 = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            strength=0.0,
        )
        assert relation1.strength == 0.0

        relation2 = Relation(
            id="rel-2",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            strength=1.0,
        )
        assert relation2.strength == 1.0

        # Invalid values
        with pytest.raises(ValueError, match="strength"):
            Relation(
                id="rel-3",
                source_concept="concept-1",
                target_concept="concept-2",
                relation_type=RelationType.RELATED_TO,
                strength=-0.1,
            )

        with pytest.raises(ValueError, match="strength"):
            Relation(
                id="rel-4",
                source_concept="concept-1",
                target_concept="concept-2",
                relation_type=RelationType.RELATED_TO,
                strength=1.1,
            )

    def test_confidence_must_be_between_0_and_1(self):
        """Test that confidence must be between 0.0 and 1.0"""
        # Valid values
        relation1 = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            confidence=0.0,
        )
        assert relation1.confidence == 0.0

        relation2 = Relation(
            id="rel-2",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            confidence=1.0,
        )
        assert relation2.confidence == 1.0

        # Invalid values
        with pytest.raises(ValueError, match="confidence"):
            Relation(
                id="rel-3",
                source_concept="concept-1",
                target_concept="concept-2",
                relation_type=RelationType.RELATED_TO,
                confidence=-0.1,
            )

        with pytest.raises(ValueError, match="confidence"):
            Relation(
                id="rel-4",
                source_concept="concept-1",
                target_concept="concept-2",
                relation_type=RelationType.RELATED_TO,
                confidence=1.1,
            )

    def test_evidence_must_be_list(self):
        """Test that evidence must be a list"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            evidence=[],
        )

        assert isinstance(relation.evidence, list)


class TestRelationMethods:
    """Test Relation helper methods"""

    def test_add_evidence(self):
        """Test add_evidence method"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
        )

        # Add first evidence
        relation.add_evidence(
            source="doc1",
            quote="This is evidence",
            confidence=0.9,
        )

        assert len(relation.evidence) == 1
        assert relation.evidence[0]["source"] == "doc1"
        assert relation.evidence[0]["quote"] == "This is evidence"
        assert relation.evidence[0]["confidence"] == 0.9

        # Add second evidence
        relation.add_evidence(
            source="doc2",
            quote="More evidence",
            confidence=0.8,
        )

        assert len(relation.evidence) == 2
        assert relation.evidence[1]["source"] == "doc2"

    def test_add_evidence_validates_confidence(self):
        """Test that add_evidence validates confidence"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
        )

        with pytest.raises(ValueError, match="confidence"):
            relation.add_evidence(
                source="doc1",
                quote="Evidence",
                confidence=1.5,
            )

    def test_add_evidence_updates_timestamp(self):
        """Test that add_evidence updates the timestamp"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
        )

        original_updated_at = relation.updated_at

        import time
        time.sleep(0.01)  # Small delay to ensure timestamp difference

        relation.add_evidence(
            source="doc1",
            quote="Evidence",
            confidence=0.9,
        )

        assert relation.updated_at > original_updated_at

    def test_update_strength(self):
        """Test update_strength method"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            strength=0.5,
        )

        assert relation.strength == 0.5

        relation.update_strength(0.8)
        assert relation.strength == 0.8

        relation.update_strength(0.0)
        assert relation.strength == 0.0

        relation.update_strength(1.0)
        assert relation.strength == 1.0

    def test_update_strength_validates(self):
        """Test that update_strength validates the new value"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            strength=0.5,
        )

        with pytest.raises(ValueError, match="strength"):
            relation.update_strength(-0.1)

        with pytest.raises(ValueError, match="strength"):
            relation.update_strength(1.1)

    def test_update_strength_updates_timestamp(self):
        """Test that update_strength updates the timestamp"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            strength=0.5,
        )

        original_updated_at = relation.updated_at

        import time
        time.sleep(0.01)  # Small delay to ensure timestamp difference

        relation.update_strength(0.8)

        assert relation.updated_at > original_updated_at

    def test_update_confidence(self):
        """Test update_confidence method"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            confidence=0.5,
        )

        assert relation.confidence == 0.5

        relation.update_confidence(0.8)
        assert relation.confidence == 0.8

        relation.update_confidence(0.0)
        assert relation.confidence == 0.0

        relation.update_confidence(1.0)
        assert relation.confidence == 1.0

    def test_update_confidence_validates(self):
        """Test that update_confidence validates the new value"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            confidence=0.5,
        )

        with pytest.raises(ValueError, match="confidence"):
            relation.update_confidence(-0.1)

        with pytest.raises(ValueError, match="confidence"):
            relation.update_confidence(1.1)

    def test_update_confidence_updates_timestamp(self):
        """Test that update_confidence updates the timestamp"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            confidence=0.5,
        )

        original_updated_at = relation.updated_at

        import time
        time.sleep(0.01)  # Small delay to ensure timestamp difference

        relation.update_confidence(0.8)

        assert relation.updated_at > original_updated_at


class TestRelationTemporal:
    """Test Relation temporal field support"""

    def test_relation_with_temporal_info(self):
        """Test creating a relation with temporal information"""
        temporal = TemporalInfo(
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 1, 2),
        )

        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            temporal=temporal,
        )

        assert relation.temporal is not None
        assert relation.temporal.created == datetime(2024, 1, 1)
        assert relation.temporal.modified == datetime(2024, 1, 2)

    def test_relation_without_temporal_info(self):
        """Test creating a relation without temporal information"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
        )

        assert relation.temporal is None

    def test_temporal_info_is_reused_from_concept_model(self):
        """Test that TemporalInfo is reused from concept_model"""
        from src.core.concept_model import TemporalInfo as CTemporalInfo

        temporal = CTemporalInfo(
            created=datetime(2024, 1, 1),
        )

        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            temporal=temporal,
        )

        assert isinstance(relation.temporal, CTemporalInfo)


class TestRelationTypes:
    """Test all relation types work correctly"""

    @pytest.mark.parametrize("relation_type", [
        RelationType.RELATED_TO,
        RelationType.CAUSES,
        RelationType.CAUSED_BY,
        RelationType.CONTAINS,
        RelationType.CONTAINED_IN,
        RelationType.SIMILAR_TO,
        RelationType.OPPOSES,
        RelationType.SUPPORTS,
        RelationType.PRECEDES,
        RelationType.FOLLOWS,
        RelationType.DEPENDS_ON,
        RelationType.ENABLES,
    ])
    def test_all_relation_types(self, relation_type):
        """Test that all relation types can be used"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=relation_type,
        )

        assert relation.relation_type == relation_type


class TestRelationSerialization:
    """Test Relation serialization"""

    def test_relation_to_dict(self):
        """Test converting relation to dictionary"""
        relation = Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.RELATED_TO,
            strength=0.8,
            confidence=0.75,
        )

        data = relation.to_dict()

        assert data["id"] == "rel-1"
        assert data["source_concept"] == "concept-1"
        assert data["target_concept"] == "concept-2"
        assert data["relation_type"] == "related_to"  # enum value
        assert data["strength"] == 0.8
        assert data["confidence"] == 0.75
        assert "created_at" in data
        assert "updated_at" in data
