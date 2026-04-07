"""
Shared constants for wiki operations

Centralizes configuration values to ensure consistency across components.
"""

import re

# Wiki directory structure
WIKI_DIRECTORIES = ["entities", "concepts", "sources", "synthesis", "comparisons"]

# Regex patterns for wikilink extraction
# Matches [[page]] or [[page|display]] format
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

# Regex pattern for YAML frontmatter detection
FRONTMATTER_PATTERN = re.compile(r"^---\n([\s\S]*?)\n?---\n([\s\S]*)$")

# File extensions
MARKDOWN_EXTENSION = ".md"
