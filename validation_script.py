"""
Quick validation script for KnowledgeMiner 4.0
Tests all three layers independently and validates integration.
"""

import tempfile
import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_raw_layer():
    """Test Raw Layer components"""
    print("Testing Raw Layer...")
    try:
        from src.raw.source_loader import SourceLoader
        from src.raw.source_parser import SourceParser

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("---\ntitle: Test\n---\n\nContent")

            loader = SourceLoader()
            source = loader.load(str(test_file))
            assert source.content == test_file.read_text()

            parser = SourceParser()
            parsed = parser.parse(source)
            assert parsed["title"] == "Test"

        print("✓ Raw Layer working")
        return True
    except Exception as e:
        print(f"✗ Raw Layer failed: {e}")
        return False

def test_enhanced_layer():
    """Test Enhanced Layer components"""
    print("\nTesting Enhanced Layer...")
    try:
        from src.enhanced.extractors.concept_extractor import ConceptExtractor
        from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType

        doc = EnhancedDocument(
            source_type=SourceType.FILE,
            content="Machine Learning is a subset of Artificial Intelligence.",
            metadata=DocumentMetadata(title="Test")
        )

        extractor = ConceptExtractor()
        concepts = extractor.extract(doc)
        assert len(concepts) > 0

        print("✓ Enhanced Layer working")
        return True
    except Exception as e:
        print(f"✗ Enhanced Layer failed: {e}")
        return False

def test_wiki_layer():
    """Test Wiki Layer components"""
    print("\nTesting Wiki Layer...")
    try:
        from src.wiki.writers.page_writer import PageWriter
        from src.wiki.models import WikiPage, PageType
        from src.wiki.operations.page_reader import PageReader
        from src.wiki.operations.index_searcher import IndexSearcher

        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_dir = Path(temp_dir) / "wiki" / "concepts"
            wiki_dir.mkdir(parents=True)

            page = WikiPage(
                id="test",
                title="Test",
                page_type=PageType.CONCEPT,
                content="Test content",
                frontmatter={"type": "concept"}
            )

            writer = PageWriter()
            filepath = writer.write(page, str(wiki_dir))
            assert os.path.exists(filepath)

            reader = PageReader(str(Path(temp_dir) / "wiki"))
            retrieved = reader.read("test")
            assert retrieved.id == "test"

        print("✓ Wiki Layer working")
        return True
    except Exception as e:
        print(f"✗ Wiki Layer failed: {e}")
        return False

def test_integration():
    """Test full pipeline integration"""
    print("\nTesting Integration...")
    try:
        from src.raw.source_loader import SourceLoader
        from src.raw.source_parser import SourceParser
        from src.enhanced.extractors.concept_extractor import ConceptExtractor
        from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType
        from src.wiki.writers.page_writer import PageWriter
        from src.wiki.models import WikiPage, PageType

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test source
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("""---
title: Machine Learning Basics
tags: [ml, ai]
---

# Machine Learning

Machine Learning is a subset of Artificial Intelligence that enables systems to learn from data.
""")

            # Raw Layer
            loader = SourceLoader()
            source = loader.load(str(test_file))

            parser = SourceParser()
            parsed = parser.parse(source)

            # Enhanced Layer
            doc = EnhancedDocument(
                source_type=SourceType.FILE,
                content=parsed["content"],
                metadata=DocumentMetadata(
                    title=parsed.get("title", "Untitled"),
                    tags=parsed.get("tags", [])
                )
            )

            extractor = ConceptExtractor()
            concepts = extractor.extract(doc)

            # Wiki Layer
            wiki_dir = Path(temp_dir) / "wiki" / "concepts"
            wiki_dir.mkdir(parents=True)

            writer = PageWriter()
            for concept in concepts[:2]:  # Test with just first 2 concepts
                # Clean concept name to remove newlines and special characters
                clean_name = concept.name.replace("\n", " ").strip()
                clean_id = clean_name.lower().replace(" ", "-")
                # Remove any non-alphanumeric characters except hyphens
                clean_id = "".join(c if c.isalnum() or c == "-" else "" for c in clean_id)

                page = WikiPage(
                    id=clean_id,
                    title=clean_name,
                    page_type=PageType.CONCEPT,
                    content=concept.definition or "",
                    frontmatter={"type": "concept", "confidence": concept.confidence}
                )
                writer.write(page, str(wiki_dir))

            assert len(list(wiki_dir.glob("*.md"))) == len(concepts)

        print("✓ Integration working")
        return True
    except Exception as e:
        print(f"✗ Integration failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("KnowledgeMiner 4.0 Component Validation")
    print("=" * 60)

    results = {
        "Raw Layer": test_raw_layer(),
        "Enhanced Layer": test_enhanced_layer(),
        "Wiki Layer": test_wiki_layer(),
        "Integration": test_integration()
    }

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:20s}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All components validated successfully!")
    else:
        print("❌ Some components failed validation")
    print("=" * 60)
