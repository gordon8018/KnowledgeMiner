"""Wiki data models for WikiCore."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class PageType(str, Enum):
    """Type of Wiki page."""
    TOPIC = "topic"
    CONCEPT = "concept"
    RELATION = "relation"


class UpdateType(str, Enum):
    """Type of Wiki update."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"


class WikiPage(BaseModel):
    """A Wiki page representing a topic, concept, or relation."""

    id: str = Field(..., description="Unique page identifier")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content (markdown)")
    page_type: PageType = Field(..., description="Type of page")
    version: int = Field(default=0, description="Current version number")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def increment_version(self) -> int:
        """Increment version number and return new version."""
        self.version += 1
        self.updated_at = datetime.now()
        return self.version


class WikiVersion(BaseModel):
    """A specific version of a Wiki page."""

    page_id: str
    version: int
    content: str
    parent_version: int
    change_summary: str
    created_at: datetime = Field(default_factory=datetime.now)
    author: str = Field(default="system")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WikiUpdate(BaseModel):
    """An update to be applied to a Wiki page."""

    page_id: str
    update_type: UpdateType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: int
    parent_version: int
    change_summary: str
    repair_id: Optional[str] = None  # If from auto-repair
