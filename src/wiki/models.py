"""
Wiki models for KnowledgeMiner 4.0
These models represent the persistent storage layer in markdown format
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class PageType(str, Enum):
    """Types of wiki pages"""
    ENTITY = "entity"
    CONCEPT = "concept"
    SOURCE = "source"
    SYNTHESIS = "synthesis"
    COMPARISON = "comparison"


class UpdateType(str, Enum):
    """Types of wiki updates"""
    INGEST = "ingest"
    QUERY = "query"
    LINT = "lint"


class WikiPage(BaseModel):
    """
    Wiki page model for persistent markdown storage

    Represents a page in the wiki with full support for versioning,
    linking, and Obsidian compatibility
    """

    # Page identification
    id: str
    title: str
    page_type: PageType

    # Content
    content: str
    frontmatter: Dict[str, Any] = Field(default_factory=dict)

    # Version control
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Links
    links: List[str] = Field(default_factory=list)
    backlinks: List[str] = Field(default_factory=list)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    sources_count: int = Field(default=0)

    def to_markdown(self) -> str:
        """
        Convert wiki page to markdown format

        Returns:
            Markdown string with YAML frontmatter
        """
        lines = []

        # YAML frontmatter
        lines.append("---")
        for key, value in self.frontmatter.items():
            if isinstance(value, list):
                lines.append(f"{key}: {value}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")

        # Content
        lines.append(self.content)

        return "\n".join(lines)
