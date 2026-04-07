"""
Source parsing functionality for Raw Sources layer
"""

import re
from typing import Dict, Any
from src.raw.source_loader import RawSource


class SourceParseError(Exception):
    """Raised when source fails to parse"""
    pass


class SourceParser:
    """
    Parses raw source documents and extracts frontmatter and content
    """

    def parse(self, source: RawSource) -> Dict[str, Any]:
        """
        Parse a raw source and extract frontmatter and content

        Args:
            source: RawSource instance

        Returns:
            Dictionary with frontmatter fields and content
        """
        content = source.content

        # Check for YAML frontmatter
        frontmatter_pattern = r"^---\n(.*?)\n---\n(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter_text, body_content = match.groups()
            frontmatter = self._parse_yaml_frontmatter(frontmatter_text)

            result = {
                **frontmatter,
                "content": body_content.strip(),
                "path": source.path
            }
        else:
            # No frontmatter - return default structure with None values
            result = {
                "title": None,
                "source_type": None,
                "authors": None,
                "tags": None,
                "content": content.strip(),
                "path": source.path
            }

        return result

    def _parse_yaml_frontmatter(self, text: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter (simple implementation)

        Args:
            text: YAML frontmatter text

        Returns:
            Dictionary of frontmatter fields
        """
        result = {}

        for line in text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Handle quoted strings
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("[") and value.endswith("]"):
                    # Handle lists
                    value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]

                result[key] = value

        return result
