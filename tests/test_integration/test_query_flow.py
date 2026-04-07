"""
Integration tests for query flow
"""

import pytest
import os
import tempfile
from pathlib import Path

from src.wiki.operations.index_searcher import IndexSearcher
from src.wiki.operations.page_reader import PageReader
from src.wiki.models import WikiPage, PageType
from src.wiki.writers.page_writer import PageWriter


def test_full_query_flow():
    """Test complete query flow: search → retrieve → parse"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory so IndexSearcher finds wiki/index.md
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            wiki_dir = Path(temp_dir) / "wiki"
            (wiki_dir / "concepts").mkdir(parents=True, exist_ok=True)
            (wiki_dir / "entities").mkdir(parents=True, exist_ok=True)

            # Create test wiki pages
            writer = PageWriter()

            # Create concept pages
            ml_page = WikiPage(
                id="machine_learning",
                title="Machine Learning",
                page_type=PageType.CONCEPT,
                content="Machine Learning is a subset of AI.",
                frontmatter={"type": "concept", "confidence": 0.9}
            )

            ai_page = WikiPage(
                id="artificial_intelligence",
                title="Artificial Intelligence",
                page_type=PageType.CONCEPT,
                content="AI is the simulation of human intelligence.",
                frontmatter={"type": "concept", "confidence": 0.95}
            )

            dl_page = WikiPage(
                id="deep_learning",
                title="Deep Learning",
                page_type=PageType.CONCEPT,
                content="Deep Learning uses neural networks.",
                frontmatter={"type": "concept", "confidence": 0.85}
            )

            # Write pages
            ml_path = writer.write(ml_page, str(wiki_dir / "concepts"))
            ai_path = writer.write(ai_page, str(wiki_dir / "concepts"))
            dl_path = writer.write(dl_page, str(wiki_dir / "concepts"))

            # Create index
            index_content = """# Wiki Index

## Concepts
- [[Machine Learning]]
- [[Artificial Intelligence]]
- [[Deep Learning]]

## Entities
(No entities yet)
"""

            index_path = wiki_dir / "index.md"
            index_path.write_text(index_content)

            # Step 1: Search for pages
            searcher = IndexSearcher()
            results = searcher.search("machine")

            assert len(results) > 0
            # IndexSearcher returns display text from wikilinks, not IDs
            assert "Machine Learning" in results

            # Step 2: Retrieve page
            reader = PageReader(str(wiki_dir))
            page = reader.read("machine_learning")

            assert isinstance(page, WikiPage)
            assert page.id == "machine_learning"
            assert page.title == "Machine Learning"
            assert "Machine Learning" in page.content
            assert page.page_type == PageType.CONCEPT

            # Step 3: Verify parsed content
            assert page.frontmatter["type"] == "concept"
            assert page.frontmatter["confidence"] == 0.9

        finally:
            os.chdir(original_cwd)


def test_search_multiple_results():
    """Test search returning multiple results"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory so IndexSearcher finds wiki/index.md
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            wiki_dir = Path(temp_dir) / "wiki" / "concepts"
            wiki_dir.mkdir(parents=True, exist_ok=True)

            # Create multiple pages with similar content
            writer = PageWriter()

            for i in range(3):
                page = WikiPage(
                    id=f"neural_network_{i}",
                    title=f"Neural Network {i}",
                    page_type=PageType.CONCEPT,
                    content=f"This is about neural networks and deep learning.",
                    frontmatter={"index": i}
                )
                writer.write(page, str(wiki_dir))

            # Create index
            index_content = """# Index
- [[Neural Network 0]]
- [[Neural Network 1]]
- [[Neural Network 2]]
"""
            (Path(temp_dir) / "wiki" / "index.md").write_text(index_content)

            # Search for common term
            searcher = IndexSearcher()
            results = searcher.search("neural")

            assert len(results) == 3
            # IndexSearcher returns display text from wikilinks, not IDs
            assert all(f"Neural Network {i}" in results for i in range(3))

        finally:
            os.chdir(original_cwd)


def test_retrieve_with_backlinks():
    """Test page retrieval with backlink parsing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        wiki_dir = Path(temp_dir) / "wiki"
        (wiki_dir / "concepts").mkdir(parents=True, exist_ok=True)

        writer = PageWriter()

        # Create page that links to others
        main_page = WikiPage(
            id="main_topic",
            title="Main Topic",
            page_type=PageType.CONCEPT,
            content="This page links to [[Related Topic]] and [[Another Topic]].",
            frontmatter={"type": "concept"}
        )

        related_page = WikiPage(
            id="related_topic",
            title="Related Topic",
            page_type=PageType.CONCEPT,
            content="Related content here.",
            frontmatter={"type": "concept"}
        )

        writer.write(main_page, str(wiki_dir / "concepts"))
        writer.write(related_page, str(wiki_dir / "concepts"))

        # Retrieve and verify backlinks
        reader = PageReader(str(wiki_dir))
        page = reader.read("main_topic")

        # PageReader extracts links as they appear in content (not normalized to IDs)
        assert "Related Topic" in page.links
        assert "Another Topic" in page.links
        assert len(page.links) == 2


def test_query_nonexistent_page():
    """Test querying non-existent page"""
    with tempfile.TemporaryDirectory() as temp_dir:
        wiki_dir = Path(temp_dir) / "wiki"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        (wiki_dir / "concepts").mkdir(parents=True, exist_ok=True)

        reader = PageReader(str(wiki_dir))

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            reader.read("nonexistent_page")


def test_search_with_wikilink_formats():
    """Test search with different wikilink formats"""
    with tempfile.TemporaryDirectory() as temp_dir:
        wiki_dir = Path(temp_dir) / "wiki"
        (wiki_dir / "concepts").mkdir(parents=True, exist_ok=True)

        writer = PageWriter()

        # Create page with various wikilink formats
        page = WikiPage(
            id="links_test",
            title="Links Test",
            page_type=PageType.CONCEPT,
            content="""
This page has various link formats:
- Simple: [[Simple Link]]
- With display text: [[Display Link|Click Here]]
- Multiple: [[Link 1]] and [[Link 2|Display]]
""",
            frontmatter={"type": "concept"}
        )

        writer.write(page, str(wiki_dir / "concepts"))

        # Retrieve and parse links
        reader = PageReader(str(wiki_dir))
        retrieved = reader.read("links_test")

        # PageReader extracts links as they appear in content (before | for display text)
        assert "Simple Link" in retrieved.links
        assert "Display Link" in retrieved.links
        assert "Link 1" in retrieved.links
        assert "Link 2" in retrieved.links


def test_search_case_insensitive():
    """Test case-insensitive search"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory so IndexSearcher finds wiki/index.md
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            wiki_dir = Path(temp_dir) / "wiki" / "concepts"
            wiki_dir.mkdir(parents=True, exist_ok=True)

            writer = PageWriter()

            page = WikiPage(
                id="machine_learning",
                title="Machine Learning",
                page_type=PageType.CONCEPT,
                content="Content about ML and AI.",
                frontmatter={"type": "concept"}
            )

            writer.write(page, str(wiki_dir))

            # Create index
            index_content = """# Index
- [[Machine Learning]]
"""
            (Path(temp_dir) / "wiki" / "index.md").write_text(index_content)

            searcher = IndexSearcher()

            # Should find with different cases
            # IndexSearcher returns display text from wikilinks, not IDs
            assert "Machine Learning" in searcher.search("MACHINE")
            assert "Machine Learning" in searcher.search("Machine")
            assert "Machine Learning" in searcher.search("machine")

        finally:
            os.chdir(original_cwd)


def test_retrieve_page_with_complex_frontmatter():
    """Test retrieving page with complex nested frontmatter"""
    with tempfile.TemporaryDirectory() as temp_dir:
        wiki_dir = Path(temp_dir) / "wiki"
        (wiki_dir / "concepts").mkdir(parents=True, exist_ok=True)

        writer = PageWriter()

        page = WikiPage(
            id="complex_page",
            title="Complex Page",
            page_type=PageType.CONCEPT,
            content="Content here",
            frontmatter={
                "type": "concept",
                "metadata": {
                    "authors": ["Alice", "Bob"],
                    "metrics": {"accuracy": 0.95}
                },
                "tags": ["ml", "ai"]
            }
        )

        filepath = writer.write(page, str(wiki_dir / "concepts"))

        # Retrieve and verify
        reader = PageReader(str(wiki_dir))
        retrieved = reader.read("complex_page")

        assert retrieved.frontmatter["type"] == "concept"
        assert retrieved.frontmatter["metadata"]["authors"] == ["Alice", "Bob"]
        assert retrieved.frontmatter["metadata"]["metrics"]["accuracy"] == 0.95
        assert retrieved.frontmatter["tags"] == ["ml", "ai"]
