"""Tests for WikiStore storage engine."""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.wiki.core.storage import WikiStore
from src.wiki.core.models import WikiPage, PageType


@pytest.fixture
def temp_store():
    """Create a temporary WikiStore for testing."""
    temp_dir = tempfile.mkdtemp()
    store = WikiStore(storage_path=temp_dir)
    yield store
    # Close database connection before cleanup
    store.conn.close()
    # Clean up temp directory
    try:
        shutil.rmtree(temp_dir)
    except PermissionError:
        # Windows file lock issue - try again after a short delay
        import time
        time.sleep(0.1)
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_store_initialization(temp_store):
    """Test that WikiStore initializes correctly."""
    assert temp_store.storage_path.exists()
    assert temp_store.topics_dir.exists()
    assert temp_store.concepts_dir.exists()
    assert temp_store.relations_dir.exists()
    assert temp_store.meta_dir.exists()


def test_create_topic_page(temp_store):
    """Test creating a topic page."""
    page = WikiPage(
        id="machine-learning",
        title="Machine Learning",
        content="# Machine Learning\n\nA field of AI...",
        page_type=PageType.TOPIC
    )

    temp_store.create_page(page)

    # Check file exists
    file_path = temp_store.topics_dir / "machine-learning.md"
    assert file_path.exists()

    # Check content
    content = file_path.read_text()
    assert content == "# Machine Learning\n\nA field of AI..."


def test_create_concept_page(temp_store):
    """Test creating a concept page."""
    page = WikiPage(
        id="q-learning",
        title="Q-Learning",
        content="Q-learning is a model-free algorithm...",
        page_type=PageType.CONCEPT
    )

    temp_store.create_page(page)

    file_path = temp_store.concepts_dir / "q-learning.md"
    assert file_path.exists()


def test_get_page(temp_store):
    """Test retrieving a page."""
    # Create page first
    page = WikiPage(
        id="test-page",
        title="Test",
        content="Test content",
        page_type=PageType.TOPIC
    )
    temp_store.create_page(page)

    # Retrieve page
    retrieved = temp_store.get_page("test-page")
    assert retrieved.id == "test-page"
    assert retrieved.title == "Test"
    assert retrieved.content == "Test content"


def test_update_page(temp_store):
    """Test updating a page."""
    # Create page
    page = WikiPage(
        id="test-page",
        title="Test",
        content="Original content",
        page_type=PageType.TOPIC
    )
    temp_store.create_page(page)

    # Update page
    page.content = "Updated content"
    updated = temp_store.update_page(page)

    assert updated.version == 1
    assert updated.content == "Updated content"


def test_delete_page(temp_store):
    """Test deleting a page."""
    # Create page
    page = WikiPage(
        id="test-page",
        title="Test",
        content="Test content",
        page_type=PageType.TOPIC
    )
    temp_store.create_page(page)

    # Delete page
    temp_store.delete_page("test-page")

    # Verify page is deleted
    retrieved = temp_store.get_page("test-page")
    assert retrieved is None
