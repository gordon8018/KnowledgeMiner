import pytest
from src.raw.source_parser import SourceParser, SourceParseError
from src.raw.source_loader import RawSource

def test_parse_markdown_with_frontmatter():
    """Test parsing markdown with YAML frontmatter"""
    content = """---
title: "Test Paper"
source_type: "paper"
authors: ["Author A", "Author B"]
tags: ["test", "example"]
---

# Main Content

This is the main content of the document.
"""

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    parsed = parser.parse(raw_source)

    assert parsed["title"] == "Test Paper"
    assert parsed["source_type"] == "paper"
    assert parsed["authors"] == ["Author A", "Author B"]
    assert parsed["tags"] == ["test", "example"]
    assert parsed["content"] == "# Main Content\n\nThis is the main content of the document."

def test_parse_markdown_without_frontmatter():
    """Test parsing markdown without frontmatter"""
    content = "# Simple Document\n\nNo frontmatter here."

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    parsed = parser.parse(raw_source)

    assert parsed["content"] == "# Simple Document\n\nNo frontmatter here."
    assert parsed["title"] is None
