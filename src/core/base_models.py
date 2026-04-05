"""Base data models with common functionality."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict, field_serializer


class SourceType(str, Enum):
    """Types of document sources"""
    WEB_CLIPPER = "web_clipper"
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    IMAGE = "image"


class ProcessingStatus(str, Enum):
    """Processing status of documents"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


class BaseModel(PydanticBaseModel):
    """Base model with common fields and functionality"""

    model_config = ConfigDict(
        use_enum_values=True,
    )

    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO format"""
        return dt.isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return self.model_dump()

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()
