"""
Pytest fixtures for quality assurance tests.
"""

import pytest
import tempfile
import os
from src.wiki.core.storage import WikiStore
from src.wiki.core.models import WikiPage, PageType


@pytest.fixture
def wiki_store():
    """Create a fresh WikiStore for each test."""
    test_dir = tempfile.mkdtemp()
    store = WikiStore(storage_path=test_dir)

    # Monkey-patch create_page to accept simple parameters for testing
    original_create_page = store.create_page

    def simple_create_page(page_id, content, metadata=None):
        page = WikiPage(
            id=page_id,
            title=page_id.replace("-", " ").title(),
            content=content,
            page_type=PageType.TOPIC,
            metadata=metadata or {}
        )
        return original_create_page(page)

    store.create_page = simple_create_page
    yield store

    # Cleanup - close database connections first
    try:
        store.conn.close()
    except:
        pass

    # Try to cleanup temp directory
    import shutil
    import time
    try:
        # Give Windows a moment to release file handles
        time.sleep(0.1)
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
    except:
        pass


@pytest.fixture
def sample_page():
    """Create a sample WikiPage."""
    return WikiPage(
        id="test-page",
        title="Test Page",
        content="Test content",
        page_type=PageType.TOPIC,
        metadata={}
    )
