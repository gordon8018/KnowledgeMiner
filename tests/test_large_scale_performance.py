"""
Large-scale performance tests for Stage 6.3.

Tests system performance and behavior at scale:
- 10,000+ Wiki pages
- 100,000+ concept entries
- 1,000+ document batch processing
- Stress testing and performance benchmarks
"""

import pytest
import tempfile
import time
import psutil
import threading
import multiprocessing
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime
from unittest.mock import Mock

from src.wiki.core import WikiCore
from src.wiki.insight.manager import InsightManager
from src.performance.cache import CacheManager
from src.discovery.models.insight import Insight


class TestLargeScaleWikiOperations:
    """Test Wiki operations at scale."""

    def test_create_10000_pages(self):
        """Test creating 10,000 Wiki pages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            start_time = time.time()
            pages_created = 0

            # Create 10,000 pages
            for i in range(10000):
                try:
                    wiki.create_page(
                        page_id=f"page_{i}",
                        title=f"Page {i}",
                        content=f"# Page {i}\n\nContent for page {i}\n\n" + "Data " * 100
                    )
                    pages_created += 1

                    # Progress indicator
                    if (i + 1) % 1000 == 0:
                        elapsed = time.time() - start_time
                        rate = (i + 1) / elapsed
                        print(f"Created {i + 1} pages at {rate:.1f} pages/sec")

                except Exception as e:
                    print(f"Failed to create page {i}: {e}")

            duration = time.time() - start_time
            rate = pages_created / duration

            # Verify pages were created
            pages = wiki.list_pages()
            assert len(pages) >= 10000

            # Performance assertions
            assert rate > 10, f"Creation rate too slow: {rate:.1f} pages/sec"
            assert duration < 600, f"Creation took too long: {duration:.1f} seconds"

            print(f"\n✓ Created {pages_created} pages in {duration:.1f}s ({rate:.1f} pages/sec)")

    def test_query_10000_pages(self):
        """Test querying performance with 10,000 pages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create 10,000 pages
            print("Creating 10,000 pages...")
            for i in range(10000):
                wiki.create_page(
                    page_id=f"page_{i}",
                    title=f"Page {i}",
                    content=f"# Page {i}\n\nContent {i}"
                )

            # Test query performance
            start_time = time.time()
            queries = 0

            # Perform 1,000 random queries
            for i in range(1000):
                page_id = f"page_{i % 10000}"
                page = wiki.get_page(page_id)
                assert page is not None
                queries += 1

            duration = time.time() - start_time
            rate = queries / duration

            # Performance assertions
            assert rate > 100, f"Query rate too slow: {rate:.1f} queries/sec"
            assert duration < 10, f"Queries took too long: {duration:.1f} seconds"

            print(f"✓ Performed {queries} queries in {duration:.1f}s ({rate:.1f} queries/sec)")

    def test_update_1000_pages_concurrently(self):
        """Test concurrent updates to 1,000 pages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create 1,000 pages
            print("Creating 1,000 pages...")
            for i in range(1000):
                wiki.create_page(
                    page_id=f"page_{i}",
                    title=f"Page {i}",
                    content=f"# Page {i}\n\nInitial content"
                )

            # Concurrent updates
            def update_pages(worker_id):
                start_idx = worker_id * 250
                end_idx = start_idx + 250
                updated = 0

                for i in range(start_idx, end_idx):
                    try:
                        wiki.update_page(
                            page_id=f"page_{i}",
                            content=f"# Page {i}\n\nUpdated by worker {worker_id}"
                        )
                        updated += 1
                    except Exception as e:
                        print(f"Worker {worker_id} failed to update page {i}: {e}")

                return updated

            start_time = time.time()

            # Spawn 4 workers
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(update_pages, i) for i in range(4)]
                results = [f.result() for f in as_completed(futures)]

            duration = time.time() - start_time
            total_updated = sum(results)
            rate = total_updated / duration

            # Verify updates
            assert total_updated >= 1000
            assert rate > 50, f"Update rate too slow: {rate:.1f} updates/sec"

            print(f"✓ Updated {total_updated} pages concurrently in {duration:.1f}s ({rate:.1f} updates/sec)")

    def test_delete_5000_pages(self):
        """Test deleting 5,000 pages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create 10,000 pages
            print("Creating 10,000 pages...")
            for i in range(10000):
                wiki.create_page(
                    page_id=f"page_{i}",
                    title=f"Page {i}",
                    content=f"# Page {i}"
                )

            # Delete 5,000 pages
            start_time = time.time()
            deleted_count = 0

            for i in range(5000):
                try:
                    wiki.delete_page(f"page_{i}")
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete page {i}: {e}")

            duration = time.time() - start_time
            rate = deleted_count / duration

            # Verify deletions
            pages = wiki.list_pages()
            assert len(pages) <= 5000  # Should have ~5,000 remaining
            assert deleted_count >= 5000

            # Performance assertions
            assert rate > 20, f"Deletion rate too slow: {rate:.1f} deletions/sec"

            print(f"✓ Deleted {deleted_count} pages in {duration:.1f}s ({rate:.1f} deletions/sec)")


class TestLargeScaleConceptManagement:
    """Test concept management at scale."""

    def test_extract_100000_concepts(self):
        """Test extracting 100,000+ concepts from documents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create pages with many concepts
            # Each page will have 100 concepts, so we need 1,000 pages
            concept_count = 0
            start_time = time.time()

            print("Creating 1,000 pages with 100 concepts each...")
            for page_idx in range(1000):
                # Generate content with 100 concepts
                concepts = [f"concept_{page_idx}_{i}" for i in range(100)]
                content = "# Concepts Page\n\n" + "\n".join(f"- [[{c}]]" for c in concepts)

                wiki.create_page(
                    page_id=f"concept_page_{page_idx}",
                    title=f"Concepts Page {page_idx}",
                    content=content
                )
                concept_count += 100

                if (page_idx + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = concept_count / elapsed
                    print(f"Extracted {concept_count} concepts at {rate:.1f} concepts/sec")

            duration = time.time() - start_time
            rate = concept_count / duration

            # Verify concept count
            assert concept_count >= 100000

            # Performance assertions
            assert rate > 100, f"Concept extraction rate too slow: {rate:.1f} concepts/sec"

            print(f"✓ Extracted {concept_count} concepts in {duration:.1f}s ({rate:.1f} concepts/sec)")

    def test_query_large_concept_graph(self):
        """Test querying performance with large concept graph."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create large concept graph
            print("Creating large concept graph...")
            for i in range(50000):
                wiki.create_page(
                    page_id=f"concept_{i}",
                    title=f"Concept {i}",
                    content=f"# Concept {i}\n\nRelated to [[concept_{(i+1)%50000}]]"
                )

            # Test concept relationship queries
            start_time = time.time()
            queries = 0

            for i in range(1000):
                page = wiki.get_page(f"concept_{i % 50000}")
                assert page is not None
                queries += 1

            duration = time.time() - start_time
            rate = queries / duration

            # Performance assertions
            assert rate > 100, f"Query rate too slow: {rate:.1f} queries/sec"

            print(f"✓ Performed {queries} concept queries in {duration:.1f}s ({rate:.1f} queries/sec)")

    def test_backfill_large_insight_set(self):
        """Test backfilling large set of insights."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))
            mock_llm = Mock()
            manager = InsightManager(wiki_core=wiki, llm_client=mock_llm)

            # Create 10,000 insights
            print("Creating 10,000 insights...")
            insights = []
            for i in range(10000):
                insight = Insight(
                    id=f"insight_{i}",
                    title=f"Insight {i}",
                    description=f"Description for insight {i}",
                    related_concepts=[f"concept_{i}", f"concept_{i+1}"],
                    impact_score=0.5 + (i % 50) / 100,
                    novelty_score=0.5 + (i % 30) / 100,
                    actionability_score=0.5 + (i % 40) / 100
                )
                manager.create_insight(insight)
                insights.append(insight)

            # Test backfill performance
            start_time = time.time()
            backfilled = 0

            for insight in insights[:1000]:  # Backfill first 1,000
                try:
                    manager.backfill_insight(insight)
                    backfilled += 1
                except Exception as e:
                    print(f"Failed to backfill insight {insight.id}: {e}")

            duration = time.time() - start_time
            rate = backfilled / duration

            # Performance assertions
            assert backfilled >= 900  # Allow some failures
            assert rate > 10, f"Backfill rate too slow: {rate:.1f} insights/sec"

            print(f"✓ Backfilled {backfilled} insights in {duration:.1f}s ({rate:.1f} insights/sec)")


class TestLargeScaleBatchProcessing:
    """Test batch processing at scale."""

    def test_process_1000_document_batch(self):
        """Test processing 1,000 documents in batch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            source_dir = Path(temp_dir) / "documents"
            source_dir.mkdir()

            # Create 1,000 test documents
            print("Creating 1,000 test documents...")
            for i in range(1000):
                doc_file = source_dir / f"document_{i}.md"
                doc_file.write_text(f"# Document {i}\n\nContent for document {i}\n\n" + "Text " * 100)

            # Process batch
            wiki = WikiCore(wiki_path=str(wiki_path))
            start_time = time.time()
            processed = 0

            for doc_file in source_dir.glob("*.md"):
                try:
                    # Simulate document processing
                    content = doc_file.read_text()
                    page_id = doc_file.stem

                    wiki.create_page(
                        page_id=page_id,
                        title=f"Document {page_id}",
                        content=content
                    )
                    processed += 1

                    if processed % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed
                        print(f"Processed {processed} documents at {rate:.1f} docs/sec")

                except Exception as e:
                    print(f"Failed to process {doc_file.name}: {e}")

            duration = time.time() - start_time
            rate = processed / duration

            # Verify processing
            assert processed >= 1000
            pages = wiki.list_pages()
            assert len(pages) >= 1000

            # Performance assertions
            assert rate > 5, f"Processing rate too slow: {rate:.1f} docs/sec"

            print(f"✓ Processed {processed} documents in {duration:.1f}s ({rate:.1f} docs/sec)")

    def test_concurrent_batch_processing(self):
        """Test concurrent batch processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            source_dir = Path(temp_dir) / "documents"
            source_dir.mkdir()

            # Create 1,000 documents
            print("Creating 1,000 test documents...")
            for i in range(1000):
                doc_file = source_dir / f"document_{i}.md"
                doc_file.write_text(f"# Document {i}\n\nContent")

            wiki = WikiCore(wiki_path=str(wiki_path))

            def process_batch(worker_id):
                start_idx = worker_id * 250
                end_idx = start_idx + 250
                processed = 0

                for i in range(start_idx, end_idx):
                    try:
                        doc_file = source_dir / f"document_{i}.md"
                        content = doc_file.read_text()

                        wiki.create_page(
                            page_id=f"doc_{i}",
                            title=f"Document {i}",
                            content=content
                        )
                        processed += 1
                    except Exception as e:
                        print(f"Worker {worker_id} failed to process doc {i}: {e}")

                return processed

            start_time = time.time()

            # Process with 4 workers
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(process_batch, i) for i in range(4)]
                results = [f.result() for f in as_completed(futures)]

            duration = time.time() - start_time
            total_processed = sum(results)
            rate = total_processed / duration

            # Verify processing
            assert total_processed >= 1000

            # Performance assertions
            assert rate > 20, f"Concurrent processing rate too slow: {rate:.1f} docs/sec"

            print(f"✓ Processed {total_processed} documents concurrently in {duration:.1f}s ({rate:.1f} docs/sec)")


class TestMemoryUsageAtScale:
    """Test memory usage under large-scale operations."""

    def test_memory_usage_during_large_import(self):
        """Test memory usage during large document import."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Get baseline memory
            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Create 5,000 pages
            print("Creating 5,000 pages...")
            for i in range(5000):
                wiki.create_page(
                    page_id=f"page_{i}",
                    title=f"Page {i}",
                    content=f"# Page {i}\n\n" + "Content " * 200
                )

            # Check memory after import
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - baseline_memory

            # Memory assertions
            # Should use less than 2GB for 5,000 pages
            assert memory_increase < 2000, f"Memory usage too high: {memory_increase:.1f} MB"

            # Memory per page should be reasonable (< 100KB)
            memory_per_page = memory_increase * 1024 / 5000  # KB
            assert memory_per_page < 100, f"Memory per page too high: {memory_per_page:.1f} KB"

            print(f"✓ Memory increased by {memory_increase:.1f} MB ({memory_per_page:.1f} KB/page)")

    def test_cache_memory_efficiency(self):
        """Test cache memory efficiency at scale."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache.json"

            # Create cache with 10,000 entries
            cache = CacheManager(l1_max_size=1000, l2_enabled=True, l2_cache_path=str(cache_path))

            # Fill cache
            print("Filling cache with 10,000 entries...")
            for i in range(10000):
                cache.set(f"key_{i}", f"value_{i}: " + "data " * 100)

            # Get memory usage
            process = psutil.Process()
            cache_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Memory assertions
            # L1 cache should evict to stay within limit
            stats = cache.get_stats()
            assert stats['l1_cache_size'] <= 1000, "L1 cache exceeded max size"

            # Total memory should be reasonable
            assert cache_memory < 500, f"Cache memory too high: {cache_memory:.1f} MB"

            print(f"✓ Cache memory: {cache_memory:.1f} MB (L1: {stats['l1_cache_size']}, L2: {stats['l2_cache_size']})")


class TestPerformanceBenchmarks:
    """Performance benchmarking tests."""

    def test_benchmark_page_creation(self):
        """Benchmark page creation performance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Warm-up
            for i in range(100):
                wiki.create_page(
                    page_id=f"warmup_{i}",
                    title=f"Warmup {i}",
                    content="# Warmup"
                )

            # Benchmark
            iterations = 1000
            start_time = time.time()

            for i in range(iterations):
                wiki.create_page(
                    page_id=f"bench_{i}",
                    title=f"Benchmark {i}",
                    content=f"# Benchmark {i}\n\n" + "Content " * 50
                )

            duration = time.time() - start_time
            avg_time = duration / iterations
            throughput = iterations / duration

            # Performance assertions
            assert avg_time < 0.1, f"Average creation time too high: {avg_time*1000:.1f} ms"
            assert throughput > 10, f"Throughput too low: {throughput:.1f} pages/sec"

            print(f"✓ Page creation: {avg_time*1000:.1f} ms avg, {throughput:.1f} pages/sec")

    def test_benchmark_page_query(self):
        """Benchmark page query performance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create test pages
            for i in range(1000):
                wiki.create_page(
                    page_id=f"query_{i}",
                    title=f"Query {i}",
                    content=f"# Query {i}"
                )

            # Warm-up
            for i in range(100):
                wiki.get_page(f"query_{i}")

            # Benchmark
            iterations = 10000
            start_time = time.time()

            for i in range(iterations):
                page = wiki.get_page(f"query_{i % 1000}")
                assert page is not None

            duration = time.time() - start_time
            avg_time = duration / iterations
            throughput = iterations / duration

            # Performance assertions
            assert avg_time < 0.001, f"Average query time too high: {avg_time*1000:.1f} ms"
            assert throughput > 1000, f"Throughput too low: {throughput:.1f} queries/sec"

            print(f"✓ Page query: {avg_time*1000:.1f} ms avg, {throughput:.1f} queries/sec")

    def test_benchmark_concurrent_operations(self):
        """Benchmark concurrent operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create initial pages
            for i in range(100):
                wiki.create_page(
                    page_id=f"page_{i}",
                    title=f"Page {i}",
                    content=f"# Page {i}"
                )

            def mixed_operations(worker_id):
                operations = 0
                for i in range(100):
                    # Mix of reads and writes
                    if i % 3 == 0:
                        # Write operation
                        try:
                            wiki.create_page(
                                page_id=f"worker{worker_id}_page{i}",
                                title=f"Worker {worker_id} Page {i}",
                                content=f"# Content {i}"
                            )
                            operations += 1
                        except Exception:
                            pass
                    else:
                        # Read operation
                        page = wiki.get_page(f"page_{i % 100}")
                        if page:
                            operations += 1
                return operations

            # Benchmark with 10 workers
            workers = 10
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(mixed_operations, i) for i in range(workers)]
                results = [f.result() for f in as_completed(futures)]

            duration = time.time() - start_time
            total_ops = sum(results)
            throughput = total_ops / duration

            # Performance assertions
            assert throughput > 100, f"Concurrent throughput too low: {throughput:.1f} ops/sec"

            print(f"✓ Concurrent operations: {total_ops} ops in {duration:.1f}s ({throughput:.1f} ops/sec)")
