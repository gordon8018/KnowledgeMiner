"""
Tests for PageReader
"""

import pytest
import os
from src.wiki.readers.page_reader import PageReader


def test_read_page():
    """Test reading a wiki page"""
    # Create test page
    os.makedirs("wiki/concepts", exist_ok=True)
    with open("wiki/concepts/test.md", "w") as f:
        f.write("# Test Concept\n\nThis is a test concept.")

    reader = PageReader()
    content = reader.read("test")

    assert "Test Concept" in content
    assert "test concept" in content.lower()

    # Cleanup
    os.remove("wiki/concepts/test.md")


def test_read_page_not_found():
    """Test reading non-existent page raises error"""
    reader = PageReader()

    with pytest.raises(FileNotFoundError):
        reader.read("nonexistent")


def test_list_all_pages():
    """Test listing all wiki pages"""
    # Create test pages in different directories
    os.makedirs("wiki/concepts", exist_ok=True)
    os.makedirs("wiki/entities", exist_ok=True)

    with open("wiki/concepts/concept1.md", "w") as f:
        f.write("# Concept 1")
    with open("wiki/entities/entity1.md", "w") as f:
        f.write("# Entity 1")

    reader = PageReader()
    pages = reader.list_all()

    assert "concept1" in pages
    assert "entity1" in pages
    assert len(pages) >= 2

    # Cleanup
    os.remove("wiki/concepts/concept1.md")
    os.remove("wiki/entities/entity1.md")
