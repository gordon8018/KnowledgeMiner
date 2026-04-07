"""
Enhanced models for KnowledgeMiner 4.0
These models are used in the processing layer for knowledge extraction and discovery
"""

from typing import List, Dict, Any, Optional
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

        Raises:
            ValueError: If confidence is not in [0,1] or source/quote are empty
        """
        if not source or not source.strip():
            raise ValueError("Source cannot be empty")
        if not quote or not quote.strip():
            raise ValueError("Quote cannot be empty")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")

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

        Raises:
            ValueError: If concept_name is empty or only whitespace
        """
        if not concept_name or not concept_name.strip():
            raise ValueError("Concept name cannot be empty")

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


class SourceType(str, Enum):
    """Types of sources"""
    FILE = "file"
    URL = "url"
    TEXT = "text"


class DocumentMetadata(BaseModel):
    """Metadata for documents"""
    title: str
    tags: List[str] = Field(default_factory=list)
    file_path: Optional[str] = None
    url: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    date: Optional[datetime] = None


class Relation(BaseModel):
    """Relation between concepts"""
    source: str
    target: str
    relation_type: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class EnhancedDocument(BaseModel):
    """
    Enhanced document model for document analysis

    Represents a document with full feature support for concept extraction,
    relation detection, and quality scoring
    """

    source_type: SourceType
    content: str

    # Metadata
    metadata: DocumentMetadata

    # Enhanced features
    embeddings: Optional[np.ndarray] = Field(default=None)
    concepts: List[EnhancedConcept] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)

    def add_concept(self, concept: EnhancedConcept) -> None:
        """
        Add a concept to this document

        Args:
            concept: EnhancedConcept instance
        """
        self.concepts.append(concept)

    def find_concepts_by_type(self, concept_type: ConceptType) -> List[EnhancedConcept]:
        """
        Find all concepts of a specific type

        Args:
            concept_type: Type of concept to find

        Returns:
            List of concepts of the specified type
        """
        return [c for c in self.concepts if c.type == concept_type]

    model_config = ConfigDict(arbitrary_types_allowed=True)
