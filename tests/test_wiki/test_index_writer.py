import pytest
import os
from src.wiki.writers.index_writer import IndexWriter
from src.wiki.models import WikiIndex, IndexEntry

def test_update_index():
    """Test updating wiki index"""
    index = WikiIndex()

    entry1 = IndexEntry(
        page_id="concept1",
        title="Machine Learning",
        summary="A subset of AI"
    )

    entry2 = IndexEntry(
        page_id="concept2",
        title="Deep Learning",
        summary="A type of ML"
    )

    index.add_entry("concepts", entry1)
    index.add_entry("concepts", entry2)

    writer = IndexWriter()
    writer.update(index)

    # Check file exists
    assert os.path.exists("wiki/index.md")

    # Check content
    with open("wiki/index.md", "r") as f:
        content = f.read()

    assert "Machine Learning" in content
    assert "Deep Learning" in content
    assert "## Concepts" in content

    # Cleanup
    os.remove("wiki/index.md")
