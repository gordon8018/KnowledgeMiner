"""Relation model for knowledge graph relationships."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator

from src.core.base_models import BaseModel
from src.core.concept_model import TemporalInfo


class RelationType(str, Enum):
    """Types of relationships between concepts"""

    RELATED_TO = "related_to"
    CAUSES = "causes"
    CAUSED_BY = "caused_by"
    CONTAINS = "contains"
    CONTAINED_IN = "contained_in"
    SIMILAR_TO = "similar_to"
    OPPOSES = "opposes"
    SUPPORTS = "supports"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    DEPENDS_ON = "depends_on"
    ENABLES = "enables"


class Relation(BaseModel):
    """Relationship between two concepts in the knowledge graph"""

    model_config = {
        'use_enum_values': True,
    }

    # Core fields
    source_concept: str = Field(..., description="Source concept ID")
    target_concept: str = Field(..., description="Target concept ID")
    relation_type: RelationType = Field(..., description="Type of relationship")

    # Optional fields with defaults
    strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Relationship strength (0.0 to 1.0)")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting evidence")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    temporal: Optional[TemporalInfo] = Field(None, description="Temporal information")

    @field_validator('strength')
    @classmethod
    def validate_strength(cls, v: float) -> float:
        """Validate that strength is between 0.0 and 1.0"""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"strength must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate that confidence is between 0.0 and 1.0"""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {v}")
        return v

    def add_evidence(self, source: str, quote: str, confidence: float) -> None:
        """
        Add supporting evidence for this relation.

        Args:
            source: Source document ID or reference
            quote: Text quote supporting the relation
            confidence: Confidence level of this evidence (0.0 to 1.0)

        Raises:
            ValueError: If confidence is not between 0.0 and 1.0
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

        evidence_entry = {
            "source": source,
            "quote": quote,
            "confidence": confidence
        }
        self.evidence.append(evidence_entry)
        self.update_timestamp()

    def update_strength(self, strength: float) -> None:
        """
        Update the strength score with validation.

        Args:
            strength: New strength score (0.0 to 1.0)

        Raises:
            ValueError: If strength is not between 0.0 and 1.0
        """
        if not 0.0 <= strength <= 1.0:
            raise ValueError(f"strength must be between 0.0 and 1.0, got {strength}")
        self.strength = strength
        self.update_timestamp()

    def update_confidence(self, confidence: float) -> None:
        """
        Update the confidence score with validation.

        Args:
            confidence: New confidence score (0.0 to 1.0)

        Raises:
            ValueError: If confidence is not between 0.0 and 1.0
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")
        self.confidence = confidence
        self.update_timestamp()
