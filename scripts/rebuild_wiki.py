"""
Rebuild wiki from sources after migration
"""

import os
import shutil
import glob
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.raw.source_loader import SourceLoader
from src.raw.source_parser import SourceParser
from src.enhanced.extractors.concept_extractor import ConceptExtractor
from src.enhanced.discovery.pattern_detector import PatternDetector
from src.enhanced.discovery.gap_analyzer import GapAnalyzer
from src.enhanced.discovery.insight_generator import InsightGenerator
from src.wiki.writers.page_writer import PageWriter
from src.wiki.writers.index_writer import IndexWriter
from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType
from src.wiki.models import WikiPage, PageType


def rebuild_wiki():
    """Rebuild entire wiki from raw sources"""
    print("Rebuilding wiki from sources...")

    # Clear old wiki
    if os.path.exists("wiki"):
        print("Clearing old wiki directory...")
        shutil.rmtree("wiki")

    print("Creating wiki structure...")
    os.makedirs("wiki/entities", exist_ok=True)
    os.makedirs("wiki/concepts", exist_ok=True)
    os.makedirs("wiki/sources", exist_ok=True)
    os.makedirs("wiki/synthesis", exist_ok=True)
    os.makedirs("wiki/comparisons", exist_ok=True)

    # Get all sources
    sources = glob.glob("raw/**/*.md", recursive=True)

    if not sources:
        print("No sources found in raw/ directory")
        return

    print(f"Found {len(sources)} sources to process")

    # Initialize components
    loader = SourceLoader()
    parser = SourceParser()
    extractor = ConceptExtractor()
    pattern_detector = PatternDetector()
    gap_analyzer = GapAnalyzer()
    insight_generator = InsightGenerator()
    page_writer = PageWriter()
    index_writer = IndexWriter()

    all_concepts = []
    source_pages = []

    # Process each source
    for i, source_path in enumerate(sources, 1):
        try:
            print(f"[{i}/{len(sources)}] Processing {os.path.basename(source_path)}...")

            # Load and parse
            source = loader.load(source_path)
            parsed = parser.parse(source)

            # Create enhanced document
            doc = EnhancedDocument(
                source_type=SourceType.FILE,
                content=parsed["content"],
                metadata=DocumentMetadata(
                    title=parsed.get("title", os.path.basename(source_path)),
                    tags=parsed.get("tags", []),
                    file_path=source_path
                )
            )

            # Extract concepts
            concepts = extractor.extract(doc)
            all_concepts.extend(concepts)

            # Detect patterns
            patterns = pattern_detector.detect(concepts)

            # Analyze gaps
            gaps = gap_analyzer.analyze(concepts)

            # Generate insights
            insights = insight_generator.generate(concepts)

            # Create source page
            source_page = WikiPage(
                id=parsed.get("title", os.path.basename(source_path)).lower().replace(" ", "_"),
                title=parsed.get("title", os.path.basename(source_path)),
                page_type=PageType.SOURCE,
                content=f"# {parsed.get('title', os.path.basename(source_path))}\n\n{parsed['content'][:500]}...",
                frontmatter={
                    "tags": parsed.get("tags", []),
                    "concepts_count": len(concepts),
                    "patterns_count": len(patterns),
                    "insights_count": len(insights)
                }
            )

            source_pages.append(source_page)

            # Write source page
            source_path = page_writer.write(source_page, "wiki/sources/")

        except Exception as e:
            print(f"✗ Error processing {source_path}: {e}")

    # Write concept pages (unique concepts only)
    print(f"\nWriting {len(all_concepts)} concept pages...")

    seen_concepts = set()
    for concept in all_concepts:
        # Sanitize concept_id for safe filename
        concept_id = concept.name.lower().replace(" ", "_").replace("\n", "").replace("/", "_").replace("\\", "_")

        if concept_id not in seen_concepts:
            concept_page = WikiPage(
                id=concept_id,
                title=concept.name,
                page_type=PageType.CONCEPT,
                content=f"# {concept.name}\n\n{concept.definition}",
                frontmatter={
                    "type": concept.type.value,
                    "confidence": concept.confidence,
                    "properties_count": len(concept.properties),
                    "relations_count": len(concept.relations)
                }
            )

            page_writer.write(concept_page, "wiki/concepts/")
            seen_concepts.add(concept_id)

    # Create index
    print("Creating wiki index...")
    from src.wiki.models import WikiIndex
    index = WikiIndex(
        sources=[p.id for p in source_pages],
        concepts=list(seen_concepts),
        entities=[],
        synthesis=[],
        comparisons=[]
    )
    index_writer.update(index, "wiki/index.md")

    print(f"\nWiki rebuild complete!")
    print(f"  Source pages: {len(source_pages)}")
    print(f"  Concept pages: {len(seen_concepts)}")


if __name__ == "__main__":
    rebuild_wiki()
