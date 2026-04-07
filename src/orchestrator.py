"""
KnowledgeMiner 4.0 Orchestrator

High-level coordinator for all KnowledgeMiner operations.
"""

import os
import glob
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.raw.source_loader import SourceLoader
from src.raw.source_parser import SourceParser
from src.enhanced.extractors.concept_extractor import ConceptExtractor
from src.enhanced.discovery.pattern_detector import PatternDetector
from src.enhanced.discovery.gap_analyzer import GapAnalyzer
from src.enhanced.discovery.insight_generator import InsightGenerator
from src.wiki.writers.page_writer import PageWriter
from src.wiki.writers.index_writer import IndexWriter
from src.wiki.writers.log_writer import LogWriter
from src.wiki.operations.page_reader import PageReader
from src.wiki.operations.index_searcher import IndexSearcher
from src.wiki.operations.lint import lint_wiki
from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType
from src.wiki.models import WikiPage, PageType


class KnowledgeMinerOrchestrator:
    """
    High-level orchestrator for KnowledgeMiner 4.0 operations
    """

    def __init__(self, wiki_root: str = "wiki", raw_root: str = "raw"):
        """
        Initialize orchestrator

        Args:
            wiki_root: Path to wiki directory
            raw_root: Path to raw sources directory
        """
        self.wiki_root = wiki_root
        self.raw_root = raw_root

        # Initialize components
        self.loader = SourceLoader()
        self.parser = SourceParser()
        self.extractor = ConceptExtractor()
        self.pattern_detector = PatternDetector()
        self.gap_analyzer = GapAnalyzer()
        self.insight_generator = InsightGenerator()
        self.page_writer = PageWriter()
        self.index_writer = IndexWriter()
        self.log_writer = LogWriter()
        self.page_reader = PageReader(wiki_root)
        self.index_searcher = IndexSearcher()

    def ingest_sources(self, source_paths: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Ingest sources into wiki

        Args:
            source_paths: List of source file paths (if None, processes all in raw/)

        Returns:
            Dictionary with statistics about ingestion
        """
        print("Starting ingest workflow...")

        # Get sources to process
        if source_paths is None:
            source_paths = glob.glob(f"{self.raw_root}/**/*.md", recursive=True)

        if not source_paths:
            print("No sources found to ingest")
            return {"sources_processed": 0, "concepts_extracted": 0, "pages_created": 0}

        print(f"Found {len(source_paths)} sources to process")

        stats = {
            "sources_processed": 0,
            "concepts_extracted": 0,
            "pages_created": 0,
            "errors": []
        }

        all_concepts = []
        source_pages = []

        # Process each source
        for i, source_path in enumerate(source_paths, 1):
            try:
                print(f"[{i}/{len(source_paths)}] Processing {os.path.basename(source_path)}...")

                # Load and parse
                source = self.loader.load(source_path)
                parsed = self.parser.parse(source)

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
                concepts = self.extractor.extract(doc)
                all_concepts.extend(concepts)

                # Detect patterns
                patterns = self.pattern_detector.detect(concepts)

                # Analyze gaps
                gaps = self.gap_analyzer.analyze(concepts)

                # Generate insights
                insights = self.insight_generator.generate(concepts, patterns, gaps)

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
                stats["sources_processed"] += 1

            except Exception as e:
                error_msg = f"Error processing {source_path}: {e}"
                print(f"  ✗ {error_msg}")
                stats["errors"].append(error_msg)

        # Write concept pages (unique only)
        print(f"\nWriting {len(all_concepts)} concept pages...")

        seen_concepts = set()
        for concept in all_concepts:
            concept_id = concept.name.lower().replace(" ", "_").replace("\n", "_")

            # Sanitize ID
            concept_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in concept_id)

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

                try:
                    self.page_writer.write(concept_page, f"{self.wiki_root}/concepts/")
                    seen_concepts.add(concept_id)
                    stats["pages_created"] += 1
                except Exception as e:
                    print(f"  ✗ Error writing concept {concept_id}: {e}")

        # Write source pages
        print(f"Writing {len(source_pages)} source pages...")
        for source_page in source_pages:
            try:
                self.page_writer.write(source_page, f"{self.wiki_root}/sources/")
                stats["pages_created"] += 1
            except Exception as e:
                print(f"  ✗ Error writing source {source_page.id}: {e}")

        # Create index
        print("Creating wiki index...")
        try:
            self.index_writer.write_index(source_pages, seen_concepts, f"{self.wiki_root}/index.md")
        except Exception as e:
            print(f"  ✗ Error creating index: {e}")

        # Log operation
        try:
            self.log_writer.append_ingest(
                sources_processed=stats["sources_processed"],
                concepts_extracted=len(all_concepts),
                pages_created=stats["pages_created"]
            )
        except Exception as e:
            print(f"  ✗ Error logging operation: {e}")

        stats["concepts_extracted"] = len(all_concepts)

        print(f"\nIngest complete:")
        print(f"  Sources processed: {stats['sources_processed']}")
        print(f"  Concepts extracted: {stats['concepts_extracted']}")
        print(f"  Pages created: {stats['pages_created']}")
        if stats["errors"]:
            print(f"  Errors: {len(stats['errors'])}")

        return stats

    def query(self, query_string: str) -> List[str]:
        """
        Query wiki for pages matching query string

        Args:
            query_string: Search query

        Returns:
            List of matching page IDs
        """
        print(f"Querying wiki for: {query_string}")

        results = self.index_searcher.search(query_string)

        print(f"Found {len(results)} matching pages")
        return results

    def get_page(self, page_id: str) -> Optional[WikiPage]:
        """
        Get a wiki page by ID

        Args:
            page_id: Page identifier

        Returns:
            WikiPage object or None if not found
        """
        try:
            return self.page_reader.read(page_id)
        except FileNotFoundError:
            print(f"Page not found: {page_id}")
            return None

    def list_pages(self) -> List[str]:
        """
        List all wiki pages

        Returns:
            List of page IDs
        """
        return self.page_reader.list_all()

    def lint_wiki(self, auto_fix: bool = False) -> Dict[str, Any]:
        """
        Lint wiki and generate report

        Args:
            auto_fix: Whether to auto-fix issues

        Returns:
            Dictionary with lint results
        """
        print("Linting wiki...")

        report = lint_wiki(auto_fix=auto_fix)

        print(f"Lint complete:")
        print(f"  Total pages: {report.total_pages}")
        print(f"  Issues found: {report.issues_found}")
        print(f"  Issues fixed: {report.issues_fixed}")

        return {
            "total_pages": report.total_pages,
            "issues_found": report.issues_found,
            "issues_fixed": report.issues_fixed,
            "recommendations": report.recommendations
        }

    def rebuild_wiki(self) -> Dict[str, int]:
        """
        Complete wiki rebuild from all sources

        Returns:
            Dictionary with rebuild statistics
        """
        print("Starting complete wiki rebuild...")

        return self.ingest_sources()


# Convenience functions for CLI usage

def ingest(source_paths: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Ingest sources into wiki

    Args:
        source_paths: List of source file paths

    Returns:
        Statistics dictionary
    """
    orchestrator = KnowledgeMinerOrchestrator()
    return orchestrator.ingest_sources(source_paths)


def query(query_string: str) -> List[str]:
    """
    Query wiki for pages

    Args:
        query_string: Search query

    Returns:
        List of matching page IDs
    """
    orchestrator = KnowledgeMinerOrchestrator()
    return orchestrator.query(query_string)


def lint(auto_fix: bool = False) -> Dict[str, Any]:
    """
    Lint wiki

    Args:
        auto_fix: Whether to auto-fix issues

    Returns:
        Lint results dictionary
    """
    orchestrator = KnowledgeMinerOrchestrator()
    return orchestrator.lint_wiki(auto_fix)
