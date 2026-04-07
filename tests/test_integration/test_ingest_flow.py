"""
Integration tests for complete ingest flow
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path

from src.raw.source_loader import SourceLoader
from src.raw.source_parser import SourceParser
from src.enhanced.extractors.concept_extractor import ConceptExtractor
from src.enhanced.discovery.pattern_detector import PatternDetector
from src.enhanced.discovery.gap_analyzer import GapAnalyzer
from src.enhanced.discovery.insight_generator import InsightGenerator
from src.wiki.writers.page_writer import PageWriter
from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType
from src.wiki.models import WikiPage, PageType


def test_full_ingest_flow():
    """Test complete ingest flow from source to wiki"""
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "raw" / "tests"
        wiki_dir = Path(temp_dir) / "wiki" / "sources"
        raw_dir.mkdir(parents=True, exist_ok=True)
        wiki_dir.mkdir(parents=True, exist_ok=True)

        # Create test source
        test_content = """---
title: "Test Paper"
source_type: "paper"
tags: ["test", "ml"]
author: "Test Author"
date: "2026-04-07"
---

# Machine Learning

Machine Learning is a subset of Artificial Intelligence.
Deep Learning is a type of Machine Learning.

## Key Concepts

- Neural Networks
- Training Data
- Model Architecture
"""

        test_file = raw_dir / "test_paper.md"
        test_file.write_text(test_content)

        # Step 1: Load source
        loader = SourceLoader()
        source = loader.load(str(test_file))

        assert source.content == test_content
        assert source.filename == "test_paper.md"

        # Step 2: Parse source
        parser = SourceParser()
        parsed = parser.parse(source)

        assert parsed["title"] == "Test Paper"
        assert parsed["source_type"] == "paper"
        assert parsed["tags"] == ["test", "ml"]
        assert "Machine Learning" in parsed["content"]

        # Step 3: Create enhanced document
        doc = EnhancedDocument(
            source_type=SourceType.FILE,
            content=parsed["content"],
            metadata=DocumentMetadata(
                title=parsed["title"],
                tags=parsed.get("tags", []),
                file_path=source.path,
                custom_fields={
                    "author": parsed.get("author"),
                    "date": parsed.get("date")
                }
            )
        )

        assert doc.metadata.title == "Test Paper"
        assert doc.source_type == SourceType.FILE

        # Step 4: Extract concepts
        extractor = ConceptExtractor()
        concepts = extractor.extract(doc)

        assert len(concepts) > 0
        # Should extract concepts like "Machine Learning", "Artificial Intelligence", etc.

        # Step 5: Detect patterns
        pattern_detector = PatternDetector()
        patterns = pattern_detector.detect(concepts)

        assert isinstance(patterns, list)

        # Step 6: Analyze gaps
        gap_analyzer = GapAnalyzer()
        gaps = gap_analyzer.analyze(concepts)

        assert isinstance(gaps, list)

        # Step 7: Generate insights
        insight_generator = InsightGenerator()
        insights = insight_generator.generate(concepts)

        assert isinstance(insights, list)

        # Step 8: Write to wiki
        writer = PageWriter()

        # Create wiki page for the source
        source_page = WikiPage(
            id="test_paper",
            title=parsed["title"],
            page_type=PageType.SOURCE,
            content=f"# {parsed['title']}\n\n{parsed['content'][:200]}...",
            frontmatter={
                "tags": parsed.get("tags", []),
                "author": parsed.get("author"),
                "source_date": parsed.get("date"),
                "concepts_count": len(concepts)
            }
        )

        filepath = writer.write(source_page, str(wiki_dir))

        assert os.path.exists(filepath)
        assert "test_paper.md" in filepath

        # Verify wiki page content
        with open(filepath, "r", encoding="utf-8") as f:
            wiki_content = f.read()

        assert "---" in wiki_content  # Has frontmatter
        assert "Test Paper" in wiki_content
        assert "test" in wiki_content or "ml" in wiki_content


def test_complex_source_ingest():
    """Test ingest with complex nested structures"""
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "raw" / "complex"
        wiki_dir = Path(temp_dir) / "wiki" / "concepts"
        raw_dir.mkdir(parents=True, exist_ok=True)
        wiki_dir.mkdir(parents=True, exist_ok=True)

        # Complex source with nested frontmatter
        complex_content = """---
title: "Advanced ML Techniques"
source_type: "paper"
tags: ["ml", "advanced", "neural"]
metadata:
  conference: "ICML 2026"
  authors:
    - "Alice Researcher"
    - "Bob Scientist"
  metrics:
    accuracy: 95.2
    precision: 93.8
---

# Introduction

This paper explores advanced Machine Learning techniques.

## Methodology

We propose a novel approach combining:
- Convolutional Neural Networks
- Recurrent Neural Networks
- Attention Mechanisms

## Results

Our method achieves state-of-the-art performance.
"""

        test_file = raw_dir / "advanced_ml.md"
        test_file.write_text(complex_content)

        # Load and parse
        loader = SourceLoader()
        source = loader.load(str(test_file))

        parser = SourceParser()
        parsed = parser.parse(source)

        # Verify nested frontmatter parsed correctly
        assert parsed["title"] == "Advanced ML Techniques"
        assert parsed["metadata"]["conference"] == "ICML 2026"
        assert len(parsed["metadata"]["authors"]) == 2
        assert parsed["metadata"]["metrics"]["accuracy"] == 95.2

        # Extract concepts
        doc = EnhancedDocument(
            source_type=SourceType.FILE,
            content=parsed["content"],
            metadata=DocumentMetadata(
                title=parsed["title"],
                tags=parsed.get("tags", []),
                file_path=source.path
            )
        )

        extractor = ConceptExtractor()
        concepts = extractor.extract(doc)

        # Should extract multiple concepts
        assert len(concepts) >= 3

        # Write concept pages to wiki
        writer = PageWriter()

        for i, concept in enumerate(concepts[:3]):  # Write first 3 concepts
            # Clean concept name for valid filename
            clean_name = concept.name.replace("\n", " ").strip()
            concept_id = f"concept_{i}_{clean_name.lower().replace(' ', '_')}"
            concept_id = "".join(c for c in concept_id if c.isalnum() or c in "_-")

            concept_page = WikiPage(
                id=concept_id,
                title=clean_name,
                page_type=PageType.CONCEPT,
                content=f"# {clean_name}\n\n{concept.definition}",
                frontmatter={
                    "type": concept.type.value,
                    "confidence": concept.confidence,
                    "properties_count": len(concept.properties)
                }
            )

            filepath = writer.write(concept_page, str(wiki_dir))
            assert os.path.exists(filepath)


def test_ingest_error_handling():
    """Test ingest flow with various error conditions"""
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "raw" / "errors"
        raw_dir.mkdir(parents=True, exist_ok=True)

        loader = SourceLoader()
        parser = SourceParser()

        # Test 1: Non-existent file
        with pytest.raises(Exception):
            loader.load("non_existent_file.md")

        # Test 2: File with invalid YAML
        invalid_yaml = raw_dir / "invalid.yaml"
        invalid_yaml.write_text("---\ntitle: unclosed yaml\ncontent")

        source = loader.load(str(invalid_yaml))
        # Should handle gracefully or raise appropriate error
        try:
            parsed = parser.parse(source)
            # If it doesn't raise, check if it handled gracefully
            assert "content" in parsed or "title" in parsed
        except Exception as e:
            # Expected to raise SourceParseError
            assert "parse" in str(e).lower() or "yaml" in str(e).lower()


def test_end_to_end_data_integrity():
    """Verify data integrity through entire pipeline"""
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "raw" / "integrity"
        wiki_dir = Path(temp_dir) / "wiki"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (wiki_dir / "sources").mkdir(parents=True, exist_ok=True)

        # Create source with specific testable content
        test_content = """---
title: "Data Integrity Test"
tags: ["test"]
---

Test content with special chars: @#$%^&*()
Numbers: 123456789
Unicode: 你好世界
"""

        test_file = raw_dir / "integrity_test.md"
        test_file.write_text(test_content, encoding="utf-8")

        # Full pipeline
        loader = SourceLoader()
        source = loader.load(str(test_file))

        parser = SourceParser()
        parsed = parser.parse(source)

        doc = EnhancedDocument(
            source_type=SourceType.FILE,
            content=parsed["content"],
            metadata=DocumentMetadata(
                title=parsed["title"],
                tags=parsed.get("tags", []),
                file_path=source.path
            )
        )

        extractor = ConceptExtractor()
        concepts = extractor.extract(doc)

        writer = PageWriter()
        page = WikiPage(
            id="integrity_test",
            title=parsed["title"],
            page_type=PageType.SOURCE,
            content=parsed["content"],
            frontmatter={"tags": parsed.get("tags", [])}
        )

        filepath = writer.write(page, str(wiki_dir / "sources"))

        # Verify data integrity
        with open(filepath, "r", encoding="utf-8") as f:
            wiki_content = f.read()

        # Check special characters preserved
        assert "@#$%^&*()" in wiki_content
        assert "123456789" in wiki_content
        assert "你好世界" in wiki_content


def test_multiple_sources_integration():
    """Test ingest flow with multiple source documents"""
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "raw" / "multiple"
        wiki_dir = Path(temp_dir) / "wiki"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (wiki_dir / "sources").mkdir(parents=True, exist_ok=True)

        # Create multiple test sources
        sources_data = [
            {
                "filename": "source1.md",
                "content": """---
title: "Source One"
tags: ["ml", "basics"]
---
Machine Learning basics and fundamentals."""
            },
            {
                "filename": "source2.md",
                "content": """---
title: "Source Two"
tags: ["dl", "advanced"]
---
Deep Learning and Neural Networks."""
            },
            {
                "filename": "source3.md",
                "content": """---
title: "Source Three"
tags: ["nlp", "applications"]
---
Natural Language Processing applications."""
            }
        ]

        loader = SourceLoader()
        parser = SourceParser()
        extractor = ConceptExtractor()
        writer = PageWriter()

        all_concepts = []

        for source_data in sources_data:
            # Create source file
            test_file = raw_dir / source_data["filename"]
            test_file.write_text(source_data["content"])

            # Load and parse
            source = loader.load(str(test_file))
            parsed = parser.parse(source)

            # Create enhanced document
            doc = EnhancedDocument(
                source_type=SourceType.FILE,
                content=parsed["content"],
                metadata=DocumentMetadata(
                    title=parsed["title"],
                    tags=parsed.get("tags", []),
                    file_path=source.path
                )
            )

            # Extract concepts
            concepts = extractor.extract(doc)
            all_concepts.extend(concepts)

            # Write wiki page
            page = WikiPage(
                id=parsed["title"].lower().replace(" ", "_"),
                title=parsed["title"],
                page_type=PageType.SOURCE,
                content=f"# {parsed['title']}\n\n{parsed['content']}",
                frontmatter={"tags": parsed.get("tags", [])}
            )

            filepath = writer.write(page, str(wiki_dir / "sources"))
            assert os.path.exists(filepath)

        # Verify we processed all sources
        assert len(all_concepts) > 0

        # Verify all wiki pages created
        wiki_files = list((wiki_dir / "sources").glob("*.md"))
        assert len(wiki_files) == 3


def test_discovery_pipeline_integration():
    """Test the complete discovery pipeline integration"""
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "raw" / "discovery"
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Create source with various concept types
        test_content = """---
title: "Discovery Test"
tags: ["test"]
---

# Machine Learning Research

Machine Learning is a rapidly evolving field.
Deep Learning has gained significant attention.
Neural Networks are fundamental to Deep Learning.

Research shows that combining multiple approaches
yields better results than single methods.
"""

        test_file = raw_dir / "discovery_test.md"
        test_file.write_text(test_content)

        # Load and parse
        loader = SourceLoader()
        source = loader.load(str(test_file))

        parser = SourceParser()
        parsed = parser.parse(source)

        # Create enhanced document with concepts that have relations
        doc = EnhancedDocument(
            source_type=SourceType.FILE,
            content=parsed["content"],
            metadata=DocumentMetadata(
                title=parsed["title"],
                tags=parsed.get("tags", []),
                file_path=source.path
            )
        )

        # Extract concepts
        extractor = ConceptExtractor()
        concepts = extractor.extract(doc)

        # Add some relations to test insight generation
        if len(concepts) > 0:
            for i in range(min(3, len(concepts) - 1)):
                concepts[i].add_relation(concepts[i + 1].name)

        # Run discovery pipeline
        pattern_detector = PatternDetector()
        patterns = pattern_detector.detect(concepts)

        gap_analyzer = GapAnalyzer()
        gaps = gap_analyzer.analyze(concepts)

        insight_generator = InsightGenerator()
        insights = insight_generator.generate(concepts)

        # Verify discovery results
        assert isinstance(patterns, list)
        assert isinstance(gaps, list)
        assert isinstance(insights, list)

        # Should find some gaps (low confidence concepts)
        low_confidence_concepts = [c for c in concepts if c.confidence < 0.5]
        if len(low_confidence_concepts) > 0:
            assert len(gaps) > 0

        # Should find insights for highly connected concepts
        highly_connected = [c for c in concepts if len(c.relations) >= 3]
        if len(highly_connected) > 0:
            assert len(insights) > 0
