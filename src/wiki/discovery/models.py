"""
Models for wiki discovery component.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class ChangeSet(BaseModel):
    """
    Set of document changes detected by InputProcessor.

    Tracks new, changed, and deleted documents along with metadata
    for impact scoring and batch processing.
    """
    new_docs: List[str] = Field(default_factory=list, description="New document IDs")
    changed_docs: List[str] = Field(default_factory=list, description="Changed document IDs")
    deleted_docs: List[str] = Field(default_factory=list, description="Deleted document IDs")
    timestamp: datetime = Field(default_factory=datetime.now)
    batch_id: str = Field(..., description="Unique batch identifier")
    impact_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Estimated impact (0-1)")

    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return len(self.new_docs) + len(self.changed_docs) + len(self.deleted_docs)

    def is_empty(self) -> bool:
        """Check if changeset is empty."""
        return self.total_changes == 0
