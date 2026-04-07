import pytest
import os
from src.wiki.writers.page_writer import PageWriter
from src.wiki.models import WikiPage, PageType

def test_write_wiki_page():
    """Test writing a wiki page to disk"""
    page = WikiPage(
        id="test-page",
        title="Test Page",
        page_type=PageType.CONCEPT,
        content="# Test\n\nContent here"
    )

    writer = PageWriter()
    writer.write(page, "wiki/concepts/")

    # Check file exists
    assert os.path.exists("wiki/concepts/test-page.md")

    # Check content
    with open("wiki/concepts/test-page.md", "r", encoding="utf-8") as f:
        content = f.read()
    assert "# Test" in content
    assert "Content here" in content

    # Cleanup
    os.remove("wiki/concepts/test-page.md")
