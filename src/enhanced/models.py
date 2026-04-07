"""
Enhanced models for KnowledgeMiner 4.0
These models are used in the processing layer for knowledge extraction and discovery
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import numpy as np
from pydantic import BaseModel, Field, ConfigDict


class ConceptType(str, Enum):
    """Types of concepts"""
    ENTITY = "entity"
    ABSTRACT = "abstract"
    RELATION = "relation"
    METHOD = "method"


class TemporalInfo(BaseModel):
    """Temporal information for concepts"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class EnhancedConcept(BaseModel):
    """
    Enhanced concept model for knowledge extraction and analysis

    This model represents a concept with full feature support including
    embeddings, confidence scoring, evidence tracking, and relation management
    """

    # Basic attributes
    name: str
    type: ConceptType
    definition: str

    # Enhanced features
    embeddings: Optional[np.ndarray] = Field(default=None)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Knowledge associations
    properties: Dict[str, Any] = Field(default_factory=dict)
    relations: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    temporal_info: Optional[TemporalInfo] = Field(default=None)
    source_documents: List[str] = Field(default_factory=list)

    def add_evidence(self, source: str, quote: str, confidence: float) -> None:
        """
        Add supporting evidence for this concept

        Args:
            source: Source document identifier
            quote: Relevant quote from source
            confidence: Confidence of this evidence (0-1)
        """
        evidence_entry = {
            "source": source,
            "quote": quote,
            "confidence": confidence,
            "added_at": datetime.now().isoformat()
        }
        self.evidence.append(evidence_entry)

    def add_relation(self, concept_name: str) -> None:
        """
        Add a related concept

        Args:
            concept_name: Name of related concept
        """
        if concept_name not in self.relations:
            self.relations.append(concept_name)

    def update_confidence(self, confidence: float) -> None:
        """
        Update confidence score

        Args:
            confidence: New confidence score (0-1)
        """
        if 0.0 <= confidence <= 1.0:
            self.confidence = confidence
        else:
            raise ValueError("Confidence must be between 0 and 1")

    model_config = ConfigDict(arbitrary_types_allowed=True)
