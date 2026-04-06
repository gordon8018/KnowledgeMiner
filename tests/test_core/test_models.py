"""Tests for Wiki data models."""

import pytest
from datetime import datetime
from src.wiki.core.models import WikiPage, WikiVersion, WikiUpdate


def test_wiki_page_creation():
    """Test creating a WikiPage with all fields."""
    page = WikiPage(
        id="test-page",
        title="Test Page",
        content="Test content",
        page_type="topic",
        created_at=datetime.now()
    )
    assert page.id == "test-page"
    assert page.page_type == "topic"
    assert page.version == 0


def test_wiki_version_creation():
    """Test creating a WikiVersion with all fields."""
    version = WikiVersion(
        page_id="test-page",
        version=1,
        content="Updated content",
        parent_version=0,
        change_summary="Initial update",
        created_at=datetime.now()
    )
    assert version.version == 1
    assert version.parent_version == 0


def test_wiki_update_creation():
    """Test creating a WikiUpdate with all fields."""
    update = WikiUpdate(
        page_id="test-page",
        update_type="create",
        content="New content",
        metadata={"key": "value"},
        version=1,
        parent_version=0,
        change_summary="Create page"
    )
    assert update.update_type == "create"
    assert "key" in update.metadata
