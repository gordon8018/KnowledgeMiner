"""
Spec compliance validation tests for PageReader
Tests that all spec requirements are met
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
    subdirs = ["entities", "concepts", "sources", "synthesis", "comparisons"]
    for subdir in subdirs:
        os.makedirs(os.path.join(temp_dir, subdir), exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def reader(temp_wiki):
    """Create PageReader instance"""
    return PageReader(wiki_root=temp_wiki)


class TestSpecCompliance:
    """Validate PageReader meets all spec requirements"""

    def test_file_location_spec(self, reader):
        """SPEC: File must be at src/wiki/operations/page_reader.py"""
        import src.wiki.operations.page_reader as pr_module
        assert hasattr(pr_module, 'PageReader')
        assert hasattr(pr_module, 'PageReadError')

    def test_return_type_spec(self, reader, temp_wiki):
        """SPEC: read() must return WikiPage object, not string"""
        page_id = "test_page"
        content = """---
title: Test Page
page_type: concept
---

Test content
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        result = reader.read(page_id)

        # Must return WikiPage, not string
        assert isinstance(result, WikiPage)
        assert not isinstance(result, str)

    def test_yaml_frontmatter_parsing(self, reader, temp_wiki):
        """SPEC: Must parse YAML frontmatter"""
        page_id = "yaml_test"
        content = """---
title: YAML Title
page_type: concept
version: 2
tags: [tag1, tag2]
custom_field: custom_value
---

Content here
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)

        # Verify frontmatter was parsed
        assert page.title == "YAML Title"
        assert page.version == 2
        assert page.tags == ["tag1", "tag2"]
        assert page.frontmatter["custom_field"] == "custom_value"

    def test_wikilink_extraction_for_backlinks(self, reader, temp_wiki):
        """SPEC: Must extract wikilinks for backlink tracking"""
        page_id = "link_extractor"
        content = """---
title: Link Extractor
page_type: concept
---

Content with [[link1]], [[link2|Display]], and [[link3]].
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)

        # Must extract wikilinks
        assert "link1" in page.links
        assert "link2" in page.links
        assert "link3" in page.links
        assert len(page.links) == 3

    def test_wikipage_object_construction(self, reader, temp_wiki):
        """SPEC: Must construct WikiPage objects with all fields"""
        page_id = "full_page"
        content = """---
title: Full Page
page_type: synthesis
version: 5
tags: [tag1, tag2]
sources_count: 10
created_at: 2025-01-01T12:00:00
updated_at: 2025-01-02T12:00:00
---

Content with [[link]].

More content.
"""
        filepath = os.path.join(temp_wiki, "synthesis", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)

        # Verify all WikiPage fields are populated
        assert page.id == page_id
        assert page.title == "Full Page"
        assert page.page_type == PageType.SYNTHESIS
        assert page.version == 5
        assert page.tags == ["tag1", "tag2"]
        assert page.sources_count == 10
        assert "Content with" in page.content
        assert "link" in page.links
        assert isinstance(page.created_at, datetime)
        assert isinstance(page.updated_at, datetime)

    def test_required_field_validation(self, reader, temp_wiki):
        """SPEC: Must validate required fields (id, title, page_type, content)"""
        # Test missing content
        page_id = "empty_content"
        content = """---
title: Empty
page_type: concept
---

"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Should raise error for empty content
        with pytest.raises(PageReadError):
            reader.read(page_id)

    def test_uses_correct_wikipage_model(self, reader, temp_wiki):
        """SPEC: Must use WikiPage from src.wiki.models"""
        from src.wiki.models import WikiPage as ModelWikiPage

        page_id = "model_test"
        content = """---
title: Model Test
page_type: concept
---

Content
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)

        # Must be same WikiPage class from models
        assert type(page).__name__ == 'WikiPage'
        assert type(page).__module__ == 'src.wiki.models'

    def test_follows_source_parser_pattern(self, reader, temp_wiki):
        """SPEC: Should follow SourceParser pattern for YAML parsing"""
        # Create page with complex YAML
        page_id = "complex_yaml"
        content = """---
title: Complex YAML
page_type: concept
tags:
  - tag1
  - tag2
nested:
  key: value
  list:
    - item1
    - item2
---

Content
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)

        # Should handle complex YAML like SourceParser
        assert page.tags == ["tag1", "tag2"]
        assert page.frontmatter["nested"]["key"] == "value"
        assert page.frontmatter["nested"]["list"] == ["item1", "item2"]

    def test_handles_pages_without_frontmatter(self, reader, temp_wiki):
        """SPEC: Should handle pages without frontmatter gracefully"""
        page_id = "no_frontmatter"
        content = "Just content without frontmatter"

        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        page = reader.read(page_id)

        # Should provide defaults
        assert page.id == page_id
        assert page.title == "No Frontmatter"  # Generated from ID
        assert page.page_type == PageType.CONCEPT  # Default
        assert page.content == content
        assert page.version == 1  # Default

    def test_error_handling_invalid_yaml(self, reader, temp_wiki):
        """SPEC: Should handle invalid YAML gracefully"""
        page_id = "bad_yaml"
        content = """---
title: Bad YAML
page_type: concept
invalid: [unclosed
---

Content
"""
        filepath = os.path.join(temp_wiki, "concepts", f"{page_id}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Should raise PageReadError
        with pytest.raises(PageReadError):
            reader.read(page_id)

    def test_error_handling_missing_file(self, reader):
        """SPEC: Should raise FileNotFoundError for missing pages"""
        with pytest.raises(FileNotFoundError):
            reader.read("nonexistent_page")
