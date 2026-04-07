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
    assert parsed.get("title") is None
    assert "path" in parsed

def test_parse_empty_frontmatter():
    """Test parsing with empty frontmatter"""
    content = """---
---

Content here."""

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    parsed = parser.parse(raw_source)

    # Empty YAML frontmatter should return empty dict, so content is just body
    assert parsed["content"] == "Content here."
    assert parsed.get("title") is None
    assert "path" in parsed

def test_parse_malformed_frontmatter_unclosed():
    """Test handling of malformed frontmatter (unclosed)"""
    content = """---
title: Test
Content here."""

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    # Should treat as regular content (no frontmatter)
    parsed = parser.parse(raw_source)

    assert "Content here." in parsed["content"]

def test_parse_frontmatter_with_multiline_strings():
    """Test parsing frontmatter with multi-line strings"""
    content = """---
description: |
  This is a
  multi-line
  description
---

Content"""

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    parsed = parser.parse(raw_source)

    assert "multi-line" in parsed["description"]

def test_parse_frontmatter_with_booleans():
    """Test parsing frontmatter with boolean values"""
    content = """---
published: true
featured: false
---

Content"""

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    parsed = parser.parse(raw_source)

    assert parsed["published"] is True
    assert parsed["featured"] is False

def test_parse_frontmatter_with_numbers():
    """Test parsing frontmatter with numeric values"""
    content = """---
priority: 1
score: 0.95
---

Content"""

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    parsed = parser.parse(raw_source)

    assert parsed["priority"] == 1
    assert parsed["score"] == 0.95

def test_parse_empty_content():
    """Test parsing document with no content"""
    content = "# Just a heading"

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    parsed = parser.parse(raw_source)

    assert parsed["content"] == "# Just a heading"

def test_parse_invalid_yaml_raises_error():
    """Test that invalid YAML raises SourceParseError"""
    content = """---
title: [unclosed list
---

Content"""

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    with pytest.raises(SourceParseError, match="Invalid YAML frontmatter"):
        parser.parse(raw_source)
