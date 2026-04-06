"""Tests for QueryEngine with Whoosh."""

import pytest
import tempfile
import shutil
from src.wiki.core.query import QueryEngine
from src.wiki.core.storage import WikiStore
from src.wiki.core.models import WikiPage, PageType


@pytest.fixture
def query_engine():
    """Create a QueryEngine with sample data."""
    temp_dir = tempfile.mkdtemp()
    store = WikiStore(storage_path=temp_dir)

    # Create sample pages
    pages = [
        WikiPage(
            id="ml",
            title="Machine Learning",
            content="Machine learning is a subset of artificial intelligence.",
            page_type=PageType.TOPIC
        ),
        WikiPage(
            id="dl",
            title="Deep Learning",
            content="Deep learning uses neural networks with multiple layers.",
            page_type=PageType.TOPIC
        ),
        WikiPage(
            id="nn",
            title="Neural Networks",
            content="Neural networks are computing systems inspired by biological neural networks.",
            page_type=PageType.CONCEPT
        )
    ]

    for page in pages:
        store.create_page(page)

    engine = QueryEngine(store)
    yield engine

    # Cleanup - handle Windows Git file permission issues
    try:
        shutil.rmtree(temp_dir)
    except PermissionError:
        # Windows sometimes has issues deleting Git files immediately
        import time
        time.sleep(0.1)
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass  # Temporary directory will be cleaned up by OS


def test_basic_search(query_engine):
    """Test basic full-text search."""
    results = query_engine.search("artificial intelligence")
    assert len(results) > 0
    assert any("ml" in r.id for r in results)


def test_search_returns_empty(query_engine):
    """Test search with no results."""
    results = query_engine.search("nonexistent term xyzabc")
    assert len(results) == 0


def test_get_page_by_id(query_engine):
    """Test retrieving a page by ID."""
    page = query_engine.get_page("ml")
    assert page is not None
    assert page.title == "Machine Learning"


def test_search_title_boosting(query_engine):
    """Test that title matches are boosted."""
    # Search for "learning" - should match "Machine Learning" title first
    results = query_engine.search("learning")
    assert len(results) > 0
    # First result should have "learning" in title
    assert "learning" in results[0].title.lower()
