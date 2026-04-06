import pytest
import tempfile
from src.analyzers.document_analyzer import DocumentAnalyzer
from src.analyzers.hash_calculator import calculate_file_hash
from src.utils.markdown_utils import parse_frontmatter, parse_sections, extract_latex_formulas

def test_analyze_simple_document():
    content = """---
title: Test Document
date: 2026-04-04
tags: [test, example]
---

# Introduction

This is a test document.

## Section 1

Content here.
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        f.flush()
        temp_path = f.name

    try:
        analyzer = DocumentAnalyzer()
        doc = analyzer.analyze(temp_path)

        assert doc.title == "Test Document"
        assert str(doc.metadata["date"]) == "2026-04-04"
        assert doc.tags == ["test", "example"]
        assert len(doc.sections) == 2
        assert doc.sections[0].title == "Introduction"
        assert doc.sections[0].level == 1
        assert doc.hash == calculate_file_hash(temp_path)
    finally:
        import os
        os.unlink(temp_path)

def test_parse_frontmatter():
    """Test YAML frontmatter parsing."""
    content = """---
title: Test Title
date: 2026-04-04
tags: [tag1, tag2]
---
Content here"""

    metadata, content = parse_frontmatter(content)

    assert metadata["title"] == "Test Title"
    assert str(metadata["date"]) == "2026-04-04"
    assert metadata["tags"] == ["tag1", "tag2"]
    assert "Content here" in content

def test_parse_sections():
    """Test markdown section parsing."""
    content = """# Introduction

Test content.

## Section 1

More content.

### Subsection

Deep content."""

    sections = parse_sections(content)

    assert len(sections) == 3
    assert sections[0]["title"] == "Introduction"
    assert sections[0]["level"] == 1
    assert sections[1]["title"] == "Section 1"
    assert sections[1]["level"] == 2
    assert sections[2]["title"] == "Subsection"
    assert sections[2]["level"] == 3

def test_extract_latex_formulas():
    """Test LaTeX formula extraction."""
    content = "Inline formula: $x^2$ and block: $$y = mx + b$$"

    formulas = extract_latex_formulas(content)

    assert "x^2" in formulas
    assert "y = mx + b" in formulas