import pytest
from datetime import datetime
from src.wiki.models import WikiUpdate, WikiIndex, UpdateType, IndexEntry

def test_wiki_update_creation():
    """Test creating a WikiUpdate"""
    update = WikiUpdate(
        timestamp=datetime.now(),
        update_type=UpdateType.INGEST,
        page_id="test-page",
        changes="Created new page",
        parent_version=0
    )

    assert update.update_type == UpdateType.INGEST
    assert update.page_id == "test-page"
    assert update.changes == "Created new page"

def test_wiki_index():
    """Test WikiIndex operations"""
    index = WikiIndex()

    entry = IndexEntry(
        page_id="test",
        title="Test Page",
        summary="A test page"
    )

    index.add_entry("concepts", entry)

    assert "concepts" in index.categories
    assert len(index.categories["concepts"]) == 1
    assert index.categories["concepts"][0].page_id == "test"
