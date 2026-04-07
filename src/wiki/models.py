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


class IndexEntry(BaseModel):
    """Entry in the wiki index"""
    page_id: str
    title: str
    summary: str
    tags: List[str] = Field(default_factory=list)
    date: Optional[datetime] = None


class WikiUpdate(BaseModel):
    """
    Wiki update record for tracking changes in log.md

    Each update represents a change to a wiki page
    """

    timestamp: datetime
    update_type: UpdateType
    page_id: str
    changes: str
    parent_version: int


class WikiIndex(BaseModel):
    """
    Wiki index for organizing all pages

    Used to generate index.md with categorized page listings
    """

    categories: Dict[str, List[IndexEntry]] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

    def add_entry(self, category: str, entry: IndexEntry) -> None:
        """
        Add an entry to a category

        Args:
            category: Category name (e.g., "concepts", "entities")
            entry: IndexEntry instance
        """
        if category not in self.categories:
            self.categories[category] = []

        self.categories[category].append(entry)
        self.last_updated = datetime.now()

    def to_markdown(self) -> str:
        """
        Convert index to markdown format

        Returns:
            Markdown string for index.md
        """
        lines = []
        lines.append("# KnowledgeMiner Wiki Index")
        lines.append("")
        lines.append(f"*Last updated: {self.last_updated.strftime('%Y-%m-%d %H:%M')}*")
        lines.append("")

        for category, entries in self.categories.items():
            lines.append(f"## {category.title()}")
            lines.append("")

            for entry in entries:
                tags_str = ", ".join(entry.tags) if entry.tags else ""
                lines.append(f"- [[{entry.page_id}|{entry.title}]] - {entry.summary}")
                if tags_str:
                    lines.append(f"  Tags: {tags_str}")
                lines.append("")

        return "\n".join(lines)
