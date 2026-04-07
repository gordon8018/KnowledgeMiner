"""
Page reading functionality for wiki
"""

import os
import re
import yaml
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.wiki.models import WikiPage, PageType


class PageReadError(Exception):
    """Raised when page fails to read or parse"""
    pass


class PageReader:
    """
    Reads wiki pages from disk and parses them into WikiPage objects

    Handles:
    - Finding pages by ID across wiki directories
    - Parsing YAML frontmatter
    - Extracting wikilinks for backlink tracking
    - Constructing WikiPage objects with all fields
    - Validating required fields
    """

    # Compile regex patterns for better performance
    FRONTMATTER_PATTERN = re.compile(r"^---\n([\s\S]*?)\n?---\n([\s\S]*)$")
    WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

    # Required fields for WikiPage
    REQUIRED_FIELDS = {"id", "title", "page_type", "content"}

    def __init__(self, wiki_root: str = "wiki"):
        """
        Initialize PageReader

        Args:
            wiki_root: Root directory of wiki (default: "wiki")
        """
        self.wiki_root = wiki_root
        self.search_paths = [
            os.path.join(wiki_root, "entities"),
            os.path.join(wiki_root, "concepts"),
            os.path.join(wiki_root, "sources"),
            os.path.join(wiki_root, "synthesis"),
            os.path.join(wiki_root, "comparisons")
        ]

    def read(self, page_id: str) -> WikiPage:
        """
        Read a wiki page by ID and parse into WikiPage object

        Args:
            page_id: Page identifier (filename without .md)

        Returns:
            WikiPage object with all fields populated

        Raises:
            FileNotFoundError: If page not found
            PageReadError: If page fails to parse or validate
        """
        # Find the page file
        filepath = self._find_page(page_id)
        if not filepath:
            raise FileNotFoundError(f"Page not found: {page_id}")

        # Read file content
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse into WikiPage
        try:
            page = self._parse_page(page_id, content, filepath)
        except Exception as e:
            raise PageReadError(f"Failed to parse page {page_id}: {e}")

        # Validate required fields
        self._validate_page(page)

        return page

    def _find_page(self, page_id: str) -> Optional[str]:
        """
        Find a page file by ID

        Args:
            page_id: Page identifier

        Returns:
            Full path to page file, or None if not found
        """
        filename = f"{page_id}.md"

        for search_path in self.search_paths:
            filepath = os.path.join(search_path, filename)
            if os.path.exists(filepath):
                return filepath

        return None

    def _parse_page(self, page_id: str, content: str, filepath: str) -> WikiPage:
        """
        Parse page content into WikiPage object

        Args:
            page_id: Page identifier
            content: Raw markdown content
            filepath: Path to page file

        Returns:
            WikiPage object

        Raises:
            PageReadError: If parsing fails
        """
        # Parse YAML frontmatter
        frontmatter, body_content = self._parse_frontmatter(content)

        # Extract wikilinks from content
        links = self._extract_wikilinks(body_content)

        # Build frontmatter dict with metadata
        frontmatter_dict = {
            **frontmatter,
            "tags": frontmatter.get("tags", []),
            "sources_count": frontmatter.get("sources_count", 0)
        }

        # Get page type from frontmatter or infer from path
        page_type_str = frontmatter.get("page_type", "concept")
        try:
            page_type = PageType(page_type_str)
        except ValueError:
            # Default to concept if invalid type
            page_type = PageType.CONCEPT

        # Parse timestamps
        created_at = self._parse_datetime(frontmatter.get("created_at"))
        updated_at = self._parse_datetime(frontmatter.get("updated_at"))

        # Parse version
        version = frontmatter.get("version", 1)

        # Get title from frontmatter or generate from ID
        title = frontmatter.get("title", page_id.replace("_", " ").title())

        # Construct WikiPage object
        page = WikiPage(
            id=page_id,
            title=title,
            page_type=page_type,
            content=body_content,
            frontmatter=frontmatter_dict,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
            links=links,
            backlinks=[],  # Will be populated by Indexer
            tags=frontmatter_dict.get("tags", []),
            sources_count=frontmatter_dict.get("sources_count", 0)
        )

        return page

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """
        Parse YAML frontmatter from content

        Args:
            content: Raw markdown content

        Returns:
            Tuple of (frontmatter_dict, body_content)

        Raises:
            PageReadError: If YAML is invalid
        """
        match = self.FRONTMATTER_PATTERN.match(content)

        if match:
            frontmatter_text, body_content = match.groups()
            try:
                frontmatter = yaml.safe_load(frontmatter_text)
                frontmatter = frontmatter if frontmatter is not None else {}
            except yaml.YAMLError as e:
                raise PageReadError(f"Invalid YAML frontmatter: {e}")

            return frontmatter, body_content.strip()
        else:
            # No frontmatter found
            return {}, content.strip()

    def _extract_wikilinks(self, content: str) -> List[str]:
        """
        Extract wikilinks from content

        Args:
            content: Page content

        Returns:
            List of linked page IDs
        """
        matches = self.WIKILINK_PATTERN.findall(content)

        # Clean up links: handle [[page|display]] format
        cleaned_links = []
        for link in matches:
            # Split on | to handle display text
            link_id = link.split("|")[0].strip()
            if link_id:
                cleaned_links.append(link_id)

        return cleaned_links

    def _parse_datetime(self, value: Optional[str]) -> datetime:
        """
        Parse datetime from string or return current time

        Args:
            value: Datetime string or None

        Returns:
            datetime object
        """
        if value:
            try:
                return datetime.fromisoformat(value)
            except (ValueError, TypeError):
                pass

        return datetime.now()

    def _validate_page(self, page: WikiPage) -> None:
        """
        Validate that WikiPage has all required fields

        Args:
            page: WikiPage to validate

        Raises:
            PageReadError: If validation fails
        """
        missing_fields = []

        for field in self.REQUIRED_FIELDS:
            if not hasattr(page, field) or getattr(page, field) is None:
                missing_fields.append(field)

        if missing_fields:
            raise PageReadError(
                f"Page missing required fields: {', '.join(missing_fields)}"
            )

        # Validate content is not empty
        if not page.content or page.content.strip() == "":
            raise PageReadError("Page content cannot be empty")

    def list_all(self) -> List[str]:
        """
        List all wiki page IDs

        Returns:
            List of page IDs
        """
        page_ids = []

        for search_path in self.search_paths:
            if os.path.exists(search_path):
                for filename in os.listdir(search_path):
                    if filename.endswith(".md"):
                        page_id = filename[:-3]  # Remove .md
                        page_ids.append(page_id)

        return sorted(page_ids)

    def exists(self, page_id: str) -> bool:
        """
        Check if a page exists

        Args:
            page_id: Page identifier

        Returns:
            True if page exists, False otherwise
        """
        return self._find_page(page_id) is not None
