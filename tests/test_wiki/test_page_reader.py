"""
Tests for PageReader functionality
"""

import os
import pytest
import tempfile
import shutil
from datetime import datetime

from src.wiki.operations.page_reader import PageReader, PageReadError
from src.wiki.models import WikiPage, PageType


@pytest.fixture
def temp_wiki():
    """Create temporary wiki directory structure"""
    temp_dir = tempfile.mkdtemp()

    # Create wiki subdirectories
    subdirs = ["entities", "concepts", "sources", "synthesis", "comparisons"]
    for subdir in subdirs:
        os.makedirs(os.path.join(temp_dir, subdir), exist_ok=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def reader(temp_wiki):
    """Create PageReader instance with temp wiki"""
    return PageReader(wiki_root=temp_wiki)


class TestPageReader:
    """Test PageReader functionality"""

    def test_read_page_with_frontmatter(self, reader, temp_wiki):
        """Test reading page with YAML frontmatter"""
        # Create test page
        page_id = "test_concept"
        content = """---
title: Test Concept
page_type: concept
version: 1
tags: [test, example]
created_at: 2025-01-01T12:00:00
updated_at: 2025-01-01T12:00:00
---

This is test content.

It includes a [[wikilink]] to another page.
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Read page
        page = reader.read(page_id)

        # Verify WikiPage object
        assert isinstance(page, WikiPage)
        assert page.id == page_id
        assert page.title == "Test Concept"
        assert page.page_type == PageType.CONCEPT
        assert page.version == 1
        assert page.tags == ["test", "example"]
        assert "This is test content" in page.content
        assert "[[wikilink]]" in page.content  # Wikilinks remain in content

    def test_read_page_without_frontmatter(self, reader, temp_wiki):
        """Test reading page without YAML frontmatter"""
        page_id = "simple_page"
        content = "Simple content without frontmatter"

        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Read page
        page = reader.read(page_id)

        # Verify basic fields
        assert page.id == page_id
        assert page.title == "Simple Page"  # Generated from ID
        assert page.page_type == PageType.CONCEPT  # Default
        assert page.content == content
        assert page.version == 1  # Default

    def test_extract_wikilinks(self, reader, temp_wiki):
        """Test wikilink extraction"""
        page_id = "linked_page"
        content = """---
title: Linked Page
page_type: concept
---

Content with multiple [[link1]], [[link2|Display Text]], and [[link3]].
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)

        # Should extract all link IDs (without display text)
        assert "link1" in page.links
        assert "link2" in page.links
        assert "link3" in page.links
        assert len(page.links) == 3

    def test_read_page_not_found(self, reader):
        """Test reading non-existent page raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            reader.read("nonexistent_page")

    def test_read_page_invalid_yaml(self, reader, temp_wiki):
        """Test reading page with invalid YAML frontmatter"""
        page_id = "invalid_yaml"
        content = """---
title: Test
page_type: concept
invalid_yaml: [unclosed bracket
---

Content here
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Should raise PageReadError
        with pytest.raises(PageReadError):
            reader.read(page_id)

    def test_read_page_empty_content(self, reader, temp_wiki):
        """Test reading page with empty content fails validation"""
        page_id = "empty_page"
        content = """---
title: Empty Page
page_type: concept
---

"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Should raise PageReadError
        with pytest.raises(PageReadError):
            reader.read(page_id)

    def test_read_different_page_types(self, reader, temp_wiki):
        """Test reading pages with different types"""
        test_cases = [
            ("entity1", "entities", PageType.ENTITY),
            ("concept1", "concepts", PageType.CONCEPT),
            ("source1", "sources", PageType.SOURCE),
            ("synthesis1", "synthesis", PageType.SYNTHESIS),
            ("comparison1", "comparisons", PageType.COMPARISON),
        ]

        for page_id, subdir, expected_type in test_cases:
            content = f"""---
title: {page_id.title()}
page_type: {expected_type.value}
---

Content for {page_id}
"""
            filepath = os.path.join(temp_wiki, subdir, f"{page_id}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            page = reader.read(page_id)
            assert page.page_type == expected_type

    def test_list_all_pages(self, reader, temp_wiki):
        """Test listing all pages"""
        # Create test pages in different directories
        test_pages = [
            ("entity1", "entities", "Entity 1 content"),
            ("concept1", "concepts", "Concept 1 content"),
            ("source1", "sources", "Source 1 content"),
        ]

        for page_id, subdir, content in test_pages:
            filepath = os.path.join(temp_wiki, subdir, f"{page_id}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        # List all pages
        page_ids = reader.list_all()

        # Verify all pages are listed
        assert len(page_ids) == 3
        assert "entity1" in page_ids
        assert "concept1" in page_ids
        assert "source1" in page_ids

    def test_exists(self, reader, temp_wiki):
        """Test checking if page exists"""
        # Create a page
        page_id = "existing_page"
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("Content")

        # Test exists
        assert reader.exists(page_id) == True
        assert reader.exists("nonexistent") == False

    def test_parse_datetime(self, reader):
        """Test datetime parsing"""
        # Valid ISO format
        dt = reader._parse_datetime("2025-01-01T12:00:00")
        assert isinstance(dt, datetime)
        assert dt.year == 2025

        # Invalid format - should return current time
        dt = reader._parse_datetime("invalid")
        assert isinstance(dt, datetime)

        # None - should return current time
        dt = reader._parse_datetime(None)
        assert isinstance(dt, datetime)

    def test_wikilink_with_display_text(self, reader, temp_wiki):
        """Test wikilink with display text is extracted correctly"""
        page_id = "display_link"
        content = """---
title: Display Link
page_type: concept
---

Check out [[complex_page_id|Display Text Here]] for more info.
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)

        # Should extract only the page ID, not display text
        assert "complex_page_id" in page.links
        assert "Display Text Here" not in page.links

    def test_multiple_wikilinks_same_page(self, reader, temp_wiki):
        """Test multiple links to same page are counted separately"""
        page_id = "multi_link"
        content = """---
title: Multi Link
page_type: concept
---

Link to [[same_page]] once and [[same_page]] twice.
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)

        # Should extract both occurrences
        assert page.links.count("same_page") == 2

    def test_sources_count_field(self, reader, temp_wiki):
        """Test sources_count field is preserved"""
        page_id = "with_sources"
        content = """---
title: With Sources
page_type: synthesis
sources_count: 5
---

Content with sources
"""
        filepath = os.path.join(temp_wiki, "synthesis", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)
        assert page.sources_count == 5

    def test_version_field(self, reader, temp_wiki):
        """Test version field is preserved"""
        page_id = "versioned"
        content = """---
title: Versioned Page
page_type: concept
version: 3
---

Content
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)
        assert page.version == 3

    def test_custom_wiki_root(self):
        """Test PageReader with custom wiki root"""
        temp_dir = tempfile.mkdtemp()
        custom_root = os.path.join(temp_dir, "custom_wiki")

        try:
            # Create custom structure
            os.makedirs(os.path.join(custom_root, "concepts"), exist_ok=True)

            # Create page
            page_id = "custom_page"
            filepath = os.path.join(custom_root, "concepts", f"{page_id}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("Custom content")

            # Create reader with custom root
            reader = PageReader(wiki_root=custom_root)
            page = reader.read(page_id)

            assert page.content == "Custom content"

        finally:
            shutil.rmtree(temp_dir)
