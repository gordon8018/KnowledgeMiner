"""Enhanced concept model with temporal information and evidence tracking."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from pydantic import Field, field_validator

from src.core.base_models import BaseModel


class ConceptType(str, Enum):
    """Types of concepts in the knowledge graph"""

    TERM = "term"
    INDICATOR = "indicator"
    STRATEGY = "strategy"
    THEORY = "theory"
    PERSON = "person"


class TemporalInfo(BaseModel):
    """Temporal information for concepts"""

    id: str = Field(default="temporal-info", description="Default ID for TemporalInfo")
    created: Optional[datetime] = Field(None, description="When the concept was created")
    modified: Optional[datetime] = Field(None, description="When the concept was last modified")
    valid_period: Optional[Tuple[datetime, datetime]] = Field(
        None,
        description="Period during which the concept is valid (start, end)"
    )


class EnhancedConcept(BaseModel):
    """Enhanced concept model with embeddings, evidence, and temporal information"""

    model_config = {
        'arbitrary_types_allowed': True,
        'use_enum_values': True,
    }

    # Core fields
    name: str = Field(..., description="Concept name")
    type: ConceptType = Field(..., description="Concept type")
    definition: str = Field(..., description="Concept definition")

    # Optional fields
    embeddings: Optional[np.ndarray] = Field(None, description="Concept embedding vector")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Dynamic properties")
    relations: List[str] = Field(default_factory=list, description="List of relation IDs")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting evidence")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    temporal_info: Optional[TemporalInfo] = Field(None, description="Temporal information")
    source_documents: List[str] = Field(default_factory=list, description="Document IDs where concept appears")

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate that confidence is between 0.0 and 1.0"""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {v}")
        return v

    def add_evidence(self, source: str, quote: str, confidence: float) -> None:
        """
        Add supporting evidence for this concept.

        Args:
            source: Source document ID or reference
            quote: Text quote supporting the concept
            confidence: Confidence level of this evidence (0.0 to 1.0)
        """
        evidence_entry = {
            "source": source,
            "quote": quote,
            "confidence": confidence
        }
        self.evidence.append(evidence_entry)
        self.update_timestamp()

    def add_source_document(self, document_id: str) -> None:
        """
        Add a source document ID where this concept appears.

        Args:
            document_id: ID of the document where the concept appears

        Note:
            Duplicate document IDs are ignored.
            This modifies the concept in place and updates the timestamp.
        """
        if document_id not in self.source_documents:
            # Create a new list to avoid shared references in copies
            self.source_documents = list(self.source_documents)
            self.source_documents.append(document_id)
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
