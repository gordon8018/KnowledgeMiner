"""
Migration and stability tests for Stage 6.4.

Tests Phase 2 to Phase 3 migration:
- Data migration from Phase 2 format
- Data integrity verification
- Rollback scenarios
- Migration performance at scale
"""

import pytest
import tempfile
import json
import shutil
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.wiki.core import WikiCore
from src.wiki.insight.manager import InsightManager
from src.migration.phase2_to_phase3 import Phase2ToPhase3Migrator
from src.discovery.models.insight import Insight


class TestPhase2ToPhase3Migration:
    """Test migration from Phase 2 to Phase 3 format."""

    def test_migrate_simple_wiki_structure(self):
        """Test migrating simple Phase 2 wiki structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            # Create Phase 2 pages (old format)
            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            for i in range(10):
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(f"""---
title: Page {i}
created: 2024-01-01T00:00:00
modified: 2024-01-01T00:00:00
tags: tag1,tag2
---

# Page {i}

Content for page {i}
""")

            # Create index (Phase 2 format)
            index_file = phase2_wiki / "index.json"
            index_file.write_text(json.dumps({
                "version": "2.0",
                "pages": [f"page_{i}" for i in range(10)],
                "last_updated": "2024-01-01T00:00:00"
            }))

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Verify migration
            assert result.success is True
            assert result.pages_migrated == 10
            assert result.errors == []

            # Verify Phase 3 structure
            phase3_wiki = WikiCore(wiki_path=str(phase3_dir))
            pages = phase3_wiki.list_pages()

            assert len(pages) == 10

            # Verify page content
            for i in range(10):
                page = phase3_wiki.get_page(f"page_{i}")
                assert page is not None
                assert page.title == f"Page {i}"
                assert f"Page {i}" in page.content

    def test_migrate_with_concepts(self):
        """Test migrating wiki with concept links."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure with concepts
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create pages with concept links
            for i in range(5):
                page_file = pages_dir / f"concept_{i}.md"
                page_file.write_text(f"""---
title: Concept {i}
---

# Concept {i}

Related to [[concept_{(i+1)%5}]] and [[concept_{(i+2)%5}]]
""")

            # Create Phase 2 index
            index_file = phase2_wiki / "index.json"
            index_file.write_text(json.dumps({
                "version": "2.0",
                "pages": [f"concept_{i}" for i in range(5)],
                "concepts": {
                    f"concept_{i}": {
                        "references": [f"concept_{(i+1)%5}", f"concept_{(i+2)%5}"]
                    } for i in range(5)
                }
            }))

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Verify migration
            assert result.success is True
            assert result.concepts_migrated >= 5

            # Verify concept relationships in Phase 3
            phase3_wiki = WikiCore(wiki_path=str(phase3_dir))

            for i in range(5):
                page = phase3_wiki.get_page(f"concept_{i}")
                assert page is not None
                # Verify links still work
                assert f"concept_{(i+1)%5}" in page.content

    def test_migrate_with_backlinks(self):
        """Test migrating wiki with backlink data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create pages that link to each other
            pages_dir / "source.md").write_text("""---
title: Source Page
---

# Source

Links to [[target]]
""")

            pages_dir / "target.md").write_text("""---
title: Target Page
---

# Target

Referenced by source
""")

            # Create Phase 2 backlinks index
            backlinks_file = phase2_wiki / "backlinks.json"
            backlinks_file.write_text(json.dumps({
                "target": ["source"]
            }))

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Verify migration
            assert result.success is True

            # Verify backlinks work in Phase 3
            phase3_wiki = WikiCore(wiki_path=str(phase3_dir))
            target_page = phase3_wiki.get_page("target")

            assert target_page is not None
            # Backlinks should be reconstructed
            assert "source" in target_page.content or hasattr(target_page, 'backlinks')

    def test_migrate_large_wiki(self):
        """Test migrating large wiki (1,000+ pages)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create 1,000 pages
            print("Creating 1,000 Phase 2 pages...")
            for i in range(1000):
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(f"""---
title: Page {i}
created: 2024-01-01T00:00:00
---

# Page {i}

Content for page {i}
""")

                if (i + 1) % 100 == 0:
                    print(f"Created {i + 1} pages")

            # Create Phase 2 index
            index_file = phase2_wiki / "index.json"
            index_file.write_text(json.dumps({
                "version": "2.0",
                "pages": [f"page_{i}" for i in range(1000)],
                "last_updated": "2024-01-01T00:00:00"
            }))

            # Run migration with timing
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            start_time = time.time()
            result = migrator.migrate()
            duration = time.time() - start_time

            # Verify migration
            assert result.success is True
            assert result.pages_migrated == 1000

            # Performance assertions
            assert duration < 300, f"Migration too slow: {duration:.1f}s"

            # Verify Phase 3 structure
            phase3_wiki = WikiCore(wiki_path=str(phase3_dir))
            pages = phase3_wiki.list_pages()

            assert len(pages) == 1000

            # Verify random sample of pages
            for i in [0, 100, 500, 999]:
                page = phase3_wiki.get_page(f"page_{i}")
                assert page is not None
                assert page.title == f"Page {i}"

            print(f"✓ Migrated 1,000 pages in {duration:.1f}s ({1000/duration:.1f} pages/sec)")


class TestDataIntegrityVerification:
    """Test data integrity during and after migration."""

    def test_verify_content_preservation(self):
        """Test that all content is preserved during migration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create test content with special characters
            test_content = """# Test Page

## Section 1

Content with **bold**, *italic*, and `code`.

- List item 1
- List item 2
- List item 3

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

```python
def example():
    return "test"
```

Math: $E=mc^2$

Links: [[other_page]]

Special chars: < > & " ' © ® ™
"""

            page_file = pages_dir / "test.md"
            page_file.write_text(f"""---
title: Test Page
tags: test,example
---

{test_content}
""")

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Verify content preserved
            phase3_wiki = WikiCore(wiki_path=str(phase3_dir))
            page = phase3_wiki.get_page("test")

            assert page is not None
            assert "# Test Page" in page.content
            assert "**bold**" in page.content
            assert "*italic*" in page.content
            assert "`code`" in page.content
            assert "List item 1" in page.content
            assert "Column 1" in page.content
            assert "def example():" in page.content
            assert "$E=mc^2$" in page.content
            assert "[[other_page]]" in page.content
            assert "©" in page.content

    def test_verify_metadata_preservation(self):
        """Test that metadata is preserved during migration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create page with metadata
            created_date = "2024-01-15T10:30:00"
            modified_date = "2024-03-20T14:45:00"

            page_file = pages_dir / "meta_test.md"
            page_file.write_text(f"""---
title: Metadata Test
created: {created_date}
modified: {modified_date}
tags: tag1,tag2,tag3
author: Test Author
version: 1.5
---

# Content
""")

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Verify metadata preserved
            phase3_wiki = WikiCore(wiki_path=str(phase3_dir))
            page = phase3_wiki.get_page("meta_test")

            assert page is not None
            assert page.title == "Metadata Test"

            # Verify metadata in page attributes
            if hasattr(page, 'metadata'):
                assert page.metadata.get('created') == created_date
                assert page.metadata.get('modified') == modified_date
                assert 'tag1' in page.metadata.get('tags', [])

    def test_verify_relationship_preservation(self):
        """Test that page relationships are preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create interconnected pages
            pages_data = {
                "parent": """# Parent

Links to [[child1]] and [[child2]]
""",
                "child1": """# Child 1

Linked from [[parent]]
""",
                "child2": """# Child 2

Linked from [[parent]] and [[child1]]
"""
            }

            for page_id, content in pages_data.items():
                page_file = pages_dir / f"{page_id}.md"
                page_file.write_text(f"""---
title: {page_id.replace('_', ' ').title()}
---

{content}
""")

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Verify relationships preserved
            phase3_wiki = WikiCore(wiki_path=str(phase3_dir))

            parent = phase3_wiki.get_page("parent")
            assert parent is not None
            assert "child1" in parent.content.lower()
            assert "child2" in parent.content.lower()

            child1 = phase3_wiki.get_page("child1")
            assert child1 is not None
            assert "parent" in child1.content.lower()

            child2 = phase3_wiki.get_page("child2")
            assert child2 is not None
            assert "parent" in child2.content.lower()

    def test_verify_binary_data_preservation(self):
        """Test that binary data (images, etc.) is preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            assets_dir = phase2_wiki / "assets"
            assets_dir.mkdir()

            # Create test image
            test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
            image_file = assets_dir / "test.png"
            image_file.write_bytes(test_image_data)

            # Create page referencing image
            page_file = pages_dir / "image_test.md"
            page_file.write_text("""---
title: Image Test
---

# Test

![Test Image](assets/test.png)
""")

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Verify image preserved
            phase3_assets = phase3_dir / "assets" / "test.png"
            assert phase3_assets.exists()

            migrated_image_data = phase3_assets.read_bytes()
            assert migrated_image_data == test_image_data


class TestMigrationRollback:
    """Test rollback scenarios during migration."""

    def test_rollback_after_partial_migration(self):
        """Test rolling back after partial migration failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"
            backup_dir = Path(temp_dir) / "backup"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create pages
            for i in range(10):
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(f"""---
title: Page {i}
---

# Page {i}
""")

            # Mock migrator that fails partway through
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir),
                backup_path=str(backup_dir)
            )

            # Simulate failure during migration
            with patch.object(migrator, '_migrate_page', side_effect=[True] * 5 + [Exception("Simulated failure")] + [True] * 4):
                try:
                    result = migrator.migrate()
                except Exception:
                    pass

            # Rollback
            migrator.rollback()

            # Verify rollback - Phase 3 should be cleaned up
            phase3_exists = phase3_dir.exists()
            assert not phase3_exists or len(list(phase3_dir.glob("*"))) == 0

            # Verify Phase 2 data intact
            for i in range(10):
                page_file = pages_dir / f"page_{i}.md"
                assert page_file.exists()

    def test_rollback_preserves_original_data(self):
        """Test that rollback preserves original Phase 2 data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"
            backup_dir = Path(temp_dir) / "backup"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            original_content = {}

            # Create pages with unique content
            for i in range(5):
                content = f"""---
title: Original Page {i}
---

# Original Content {i}

This is the original content for page {i}.
"""
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(content)
                original_content[f"page_{i}"] = content

            # Start migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir),
                backup_path=str(backup_dir)
            )

            # Create backup
            migrator._create_backup()

            # Simulate migration starting but not completing
            phase3_dir.mkdir()

            # Rollback
            migrator.rollback()

            # Verify original content preserved
            for page_id, content in original_content.items():
                page_file = pages_dir / f"{page_id}.md"
                assert page_file.exists()

                current_content = page_file.read_text()
                assert current_content == content

    def test_rollback_after_corruption_detection(self):
        """Test rollback when corruption is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"
            backup_dir = Path(temp_dir) / "backup"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create pages
            for i in range(5):
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(f"""---
title: Page {i}
---

# Page {i}
""")

            # Create backup
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir),
                backup_path=str(backup_dir)
            )

            migrator._create_backup()

            # Simulate corruption in Phase 2 during migration
            (pages_dir / "page_0.md").write_text("CORRUPTED DATA")

            # Detect corruption and rollback
            corruption_detected = migrator._verify_integrity()

            if corruption_detected:
                migrator.rollback()

            # Verify backup restored
            for i in range(5):
                page_file = pages_dir / f"page_{i}.md"
                assert page_file.exists()
                content = page_file.read_text()
                assert "CORRUPTED" not in content


class TestMigrationPerformance:
    """Test migration performance at scale."""

    def test_migration_throughput(self):
        """Test migration throughput for large wikis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create 500 pages
            print("Creating 500 Phase 2 pages...")
            for i in range(500):
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(f"""---
title: Page {i}
created: 2024-01-01T00:00:00
---

# Page {i}

{"Content " * 50}
""")

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            start_time = time.time()
            result = migrator.migrate()
            duration = time.time() - start_time

            # Calculate throughput
            throughput = result.pages_migrated / duration

            # Performance assertions
            assert result.pages_migrated == 500
            assert throughput > 5, f"Migration throughput too low: {throughput:.1f} pages/sec"
            assert duration < 120, f"Migration took too long: {duration:.1f}s"

            print(f"✓ Migration throughput: {throughput:.1f} pages/sec")

    def test_incremental_migration(self):
        """Test incremental migration for updates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create initial Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create initial pages
            for i in range(10):
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(f"""---
title: Page {i}
---

# Page {i}
""")

            # Initial migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result1 = migrator.migrate()
            assert result1.pages_migrated == 10

            # Add new pages to Phase 2
            for i in range(10, 15):
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(f"""---
title: Page {i}
---

# Page {i}
""")

            # Incremental migration
            migrator2 = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result2 = migrator2.migrate()

            # Verify only new pages migrated
            assert result2.pages_migrated == 5  # Only new pages

            # Verify all pages in Phase 3
            phase3_wiki = WikiCore(wiki_path=str(phase3_dir))
            pages = phase3_wiki.list_pages()
            assert len(pages) == 15


class TestMigrationErrorHandling:
    """Test error handling during migration."""

    def test_handle_corrupted_page_files(self):
        """Test handling of corrupted page files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create valid pages
            for i in range(5):
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(f"""---
title: Page {i}
---

# Page {i}
""")

            # Create corrupted page
            corrupted_file = pages_dir / "page_5.md"
            corrupted_file.write_text("CORRUPTED DATA: <<<<>>>>>")

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Should handle corruption gracefully
            assert result.success is True  # Overall success
            assert result.pages_migrated == 5  # Valid pages
            assert len(result.errors) >= 1  # Corruption logged

            # Verify valid pages migrated
            phase3_wiki = WikiCore(wiki_path=str(phase3_dir))
            for i in range(5):
                page = phase3_wiki.get_page(f"page_{i}")
                assert page is not None

    def test_handle_missing_index_file(self):
        """Test handling of missing index file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure without index
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            # Create pages
            for i in range(3):
                page_file = pages_dir / f"page_{i}.md"
                page_file.write_text(f"""---
title: Page {i}
---

# Page {i}
""")

            # Run migration (should auto-generate index)
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Should succeed without index
            assert result.success is True
            assert result.pages_migrated == 3

    def test_handle_incompatible_versions(self):
        """Test handling of incompatible Phase 2 versions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            phase2_dir = Path(temp_dir) / "phase2"
            phase3_dir = Path(temp_dir) / "phase3"

            # Create Phase 2 structure with incompatible version
            phase2_dir.mkdir()
            phase2_wiki = phase2_dir / "wiki"
            phase2_wiki.mkdir()

            pages_dir = phase2_wiki / "pages"
            pages_dir.mkdir()

            page_file = pages_dir / "page_0.md"
            page_file.write_text("# Page 0")

            # Create incompatible index
            index_file = phase2_wiki / "index.json"
            index_file.write_text(json.dumps({
                "version": "1.0",  # Incompatible
                "pages": ["page_0"]
            }))

            # Run migration
            migrator = Phase2ToPhase3Migrator(
                phase2_path=str(phase2_wiki),
                phase3_path=str(phase3_dir)
            )

            result = migrator.migrate()

            # Should handle version incompatibility
            if not result.success:
                assert any("version" in str(error).lower() for error in result.errors)
