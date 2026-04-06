"""Enhanced Document model for Knowledge Compiler."""

from datetime import datetime
from typing import Optional, List, Dict, Any
import numpy as np
from pydantic import BaseModel as PydanticBaseModel, Field, field_validator, ConfigDict

from src.core.base_models import BaseModel, SourceType, ProcessingStatus


class DocumentMetadata(PydanticBaseModel):
    """Metadata for documents including title, author, and other descriptive information."""

    model_config = ConfigDict(
        use_enum_values=True,
    )

    title: Optional[str] = Field(None, description="Document title")
    author: Optional[str] = Field(None, description="Document author or creator")
    date: Optional[datetime] = Field(None, description="Document creation or publication date")
    tags: List[str] = Field(default_factory=list, description="Tags or categories for the document")
    source_url: Optional[str] = Field(None, description="URL if document is from web")
    file_path: Optional[str] = Field(None, description="Local file path if document is from file")


class EnhancedDocument(BaseModel):
    """Enhanced document model with content, metadata, embeddings, and relationships."""

    model_config = BaseModel.model_config.copy()
    model_config['arbitrary_types_allowed'] = True

    source_type: SourceType = Field(..., description="Type of document source")
    content: str = Field(..., description="Original document content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    embeddings: Optional[np.ndarray] = Field(None, description="Content embedding vector as numpy array")
    concepts: List[str] = Field(default_factory=list, description="List of concept IDs referenced in document")
    relations: List[str] = Field(default_factory=list, description="List of relation IDs for document relationships")
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Quality score from 0.0 to 1.0")
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Current processing status of the document"
    )

    @field_validator('embeddings', mode='before')
    @classmethod
    def validate_embeddings(cls, v):
        """Validate embeddings field."""
        if v is None:
            return None
        if isinstance(v, list):
            return np.array(v)
        return v

    def add_concept(self, concept_id: str) -> None:
        """
        Add a concept ID to the document's concept list.

        Args:
            concept_id: The concept ID to add

        Note:
            Duplicate concept IDs are ignored.
            This modifies the document in place and updates the timestamp.
        """
        if concept_id not in self.concepts:
            # Create a new list to avoid shared references in copies
            self.concepts = list(self.concepts)
            self.concepts.append(concept_id)
            self.update_timestamp()

    def add_relation(self, relation_id: str) -> None:
        """
        Add a relation ID to the document's relation list.

        Args:
            relation_id: The relation ID to add

        Note:
            Duplicate relation IDs are ignored.
            This modifies the document in place and updates the timestamp.
        """
        if relation_id not in self.relations:
            # Create a new list to avoid shared references in copies
            self.relations = list(self.relations)
            self.relations.append(relation_id)
            self.update_timestamp()

    def update_quality_score(self, score: float) -> None:
        """
        Update the quality score with validation.

        Args:
            score: New quality score (must be between 0.0 and 1.0)

        Raises:
            ValueError: If score is not between 0.0 and 1.0
        """
        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"quality_score must be between 0.0 and 1.0, got {score}"
            )
        self.quality_score = score
        self.update_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert document to dictionary.

        Returns:
            Dictionary representation of the document with numpy arrays converted to lists
        """
        doc_dict = super().to_dict()

        # Convert numpy array to list for JSON serialization
        if self.embeddings is not None:
            doc_dict['embeddings'] = self.embeddings.tolist()

        return doc_dict
