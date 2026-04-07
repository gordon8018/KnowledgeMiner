import pytest
from datetime import datetime
from src.wiki.models import WikiPage, PageType

def test_wiki_page_creation():
    """Test creating a WikiPage"""
    page = WikiPage(
        id="test-page",
        title="Test Page",
        page_type=PageType.CONCEPT,
        content="# Test Page\n\nThis is a test page."
    )

    assert page.id == "test-page"
    assert page.title == "Test Page"
    assert page.page_type == PageType.CONCEPT
    assert page.version == 1
    assert isinstance(page.created_at, datetime)
    assert page.links == []
    assert page.backlinks == []

def test_wiki_page_to_markdown():
    """Test converting WikiPage to markdown"""
    page = WikiPage(
        id="test",
        title="Test",
        page_type=PageType.CONCEPT,
        content="# Test\n\nContent here",
        frontmatter={"tags": ["test", "example"]}
    )

    markdown = page.to_markdown()

    assert "---" in markdown
    assert "tags:" in markdown
    assert "# Test" in markdown
    assert "Content here" in markdown
