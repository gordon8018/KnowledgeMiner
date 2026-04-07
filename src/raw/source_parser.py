"""
Source parsing functionality for Raw Sources layer
"""

import re
import yaml
from typing import Dict, Any
from src.raw.source_loader import RawSource


class SourceParseError(Exception):
    """Raised when source fails to parse"""
    pass


class SourceParser:
    """
    Parses raw source documents and extracts frontmatter and content
    """

    # Compile regex for better performance
    # Match frontmatter between --- markers, allowing empty content
    # Pattern handles both "---\n---\n" and "---\ncontent\n---\n" cases
    FRONTMATTER_PATTERN = re.compile(r"^---\n([\s\S]*?)\n?---\n([\s\S]*)$")

    def parse(self, source: RawSource) -> Dict[str, Any]:
        """
        Parse a raw source and extract frontmatter and content

        Args:
            source: RawSource instance

        Returns:
            Dictionary with frontmatter fields and content

        Raises:
            SourceParseError: If frontmatter is malformed
        """
        content = source.content

        # Check for YAML frontmatter
        match = self.FRONTMATTER_PATTERN.match(content)

        if match:
            frontmatter_text, body_content = match.groups()
            frontmatter = self._parse_yaml_frontmatter(frontmatter_text)

            result = {
                **frontmatter,
                "content": body_content.strip(),
                "path": source.path
            }
        else:
            # No frontmatter - return basic structure
            result = {
                "content": content.strip(),
                "path": source.path
            }

        return result

    def _parse_yaml_frontmatter(self, text: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter using PyYAML

        Args:
            text: YAML frontmatter text

        Returns:
            Dictionary of frontmatter fields

        Raises:
            SourceParseError: If YAML is invalid
        """
        try:
            parsed = yaml.safe_load(text)
            return parsed if parsed is not None else {}
        except yaml.YAMLError as e:
            raise SourceParseError(f"Invalid YAML frontmatter: {e}")
