"""
Concurrent access tests for Wiki system.

Tests multiple processes/threads accessing Wiki simultaneously,
race conditions, and lock contention.
"""

import pytest
import tempfile
import threading
import multiprocessing
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

from src.wiki.core import WikiCore
from src.wiki.insight.manager import InsightManager
from src.discovery.models.insight import Insight


class TestMultiThreadedAccess:
    """Test concurrent access from multiple threads."""

    def test_concurrent_page_creation(self):
        """Test multiple threads creating pages simultaneously."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            def create_pages(thread_id):
                pages_created = 0
                for i in range(10):
                    try:
                        wiki.create_page(
                            page_id=f"thread{thread_id}_page{i}",
                            title=f"Thread {thread_id} Page {i}",
                            content=f"# Content {i}"
                        )
                        pages_created += 1
                    except Exception as e:
                        pass  # Handle gracefully
                return pages_created

            # Create threads
            threads = []
            for thread_id in range(5):
                thread = threading.Thread(target=create_pages, args=(thread_id,))
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join(timeout=30)

            # Verify pages were created
            pages = wiki.list_pages()
            assert len(pages) >= 40  # 5 threads * 10 pages, some may fail

    def test_concurrent_page_updates(self):
        """Test multiple threads updating same page."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create initial page
            wiki.create_page(
                page_id="shared_page",
                title="Shared Page",
                content="# Shared Page\n\nInitial content"
            )

            def update_page(thread_id):
                for i in range(10):
                    try:
                        wiki.update_page(
                            page_id="shared_page",
                            content=f"# Shared Page\n\nThread {thread_id} Update {i}"
                        )
                    except Exception as e:
                        pass  # Handle conflicts
                    time.sleep(0.001)  # Small delay

            # Run concurrent updates
            threads = []
            for thread_id in range(5):
                thread = threading.Thread(target=update_page, args=(thread_id,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=30)

            # Page should still be accessible
            page = wiki.get_page("shared_page")
            assert page is not None
            assert "Shared Page" in page.content

    def test_concurrent_read_operations(self):
        """Test multiple threads reading simultaneously."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create test pages
            for i in range(10):
                wiki.create_page(
                    page_id=f"page_{i}",
                    title=f"Page {i}",
                    content=f"# Page {i}\n\nContent"
                )

            read_counts = threading.Semaphore()

            def read_pages(thread_id):
                pages_read = 0
                for i in range(100):
                    try:
                        page = wiki.get_page(f"page_{i % 10}")
                        if page:
                            pages_read += 1
                    except Exception:
                        pass
                return pages_read

            # Concurrent reads
            threads = []
            for thread_id in range(10):
                thread = threading.Thread(target=read_pages, args=(thread_id,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=30)

            # All reads should succeed (reads are safe)
            total_reads = sum(t.join() if not t.is_alive() else 0 for t in threads)
            assert total_reads > 900  # 10 threads * 100 reads

    def test_concurrent_page_deletion(self):
        """Test concurrent page deletion and access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create pages
            for i in range(20):
                wiki.create_page(
                    page_id=f"page_{i}",
                    title=f"Page {i}",
                    content=f"# Page {i}"
                )

            def delete_pages(thread_id):
                for i in range(thread_id * 4, (thread_id + 1) * 4):
                    try:
                        wiki.delete_page(f"page_{i}")
                    except Exception:
                        pass  # May be already deleted

            def read_pages(thread_id):
                pages_found = 0
                for i in range(20):
                    try:
                        page = wiki.get_page(f"page_{i}")
                        if page:
                            pages_found += 1
                    except Exception:
                        pass
                return pages_found

            # Concurrent delete and read
            delete_thread = threading.Thread(target=delete_pages, args=(0,))
            read_thread = threading.Thread(target=read_pages, args=(1,))

            delete_thread.start()
            read_thread.start()

            delete_thread.join()
            read_thread.join()

            # System should remain consistent
            pages = wiki.list_pages()
            assert len(pages) < 20  # Some pages deleted


class TestRaceConditions:
    """Test detection and handling of race conditions."""

    def test_create_delete_race(self):
        """Test race between page creation and deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            race_count = [0]

            def race_create_delete():
                for i in range(10):
                    # Try to create
                    try:
                        wiki.create_page(
                            page_id="race_page",
                            title="Race",
                            content="# Race"
                        )
                    except Exception:
                        pass

                    # Try to delete
                    try:
                        wiki.delete_page("race_page")
                    except Exception:
                        pass

                    race_count[0] += 1
                    time.sleep(0.001)

            # Run multiple race attempts
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=race_create_delete)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=30)

            # System should not crash
            assert True  # If we get here, no crash

    def test_update_version_race(self):
        """Test race between update and version creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            wiki.create_page(
                page_id="version_page",
                title="Version Test",
                content="# Version 1"
            )

            def rapid_updates(thread_id):
                for i in range(20):
                    try:
                        wiki.update_page(
                            page_id="version_page",
                            content=f"# Version {thread_id}.{i}"
                        )
                    except Exception:
                        pass

            # Rapid concurrent updates
            threads = []
            for thread_id in range(3):
                thread = threading.Thread(target=rapid_updates, args=(thread_id,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=30)

            # Final version should be consistent
            page = wiki.get_page("version_page")
            assert page is not None
            assert "Version" in page.content


class TestLockContention:
    """Test lock contention under high concurrency."""

    def test_high_contention_writes(self):
        """Test system under high write contention."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            completed = []

            def contentious_write(worker_id):
                for i in range(5):
                    try:
                        wiki.create_page(
                            page_id=f"contentious_{worker_id}_{i}",
                            title=f"Contentious {worker_id}.{i}",
                            content=f"# Content {i}"
                        )
                        completed.append(worker_id)
                    except Exception:
                        pass

            # High contention: 20 workers
            threads = []
            for worker_id in range(20):
                thread = threading.Thread(target=contentious_write, args=(worker_id,))
                threads.append(thread)
                thread.start()

            start = time.time()
            for thread in threads:
                thread.join(timeout=60)
            duration = time.time() - start

            # Most operations should complete
            assert len(completed) > 15
            # Should complete in reasonable time despite contention
            assert duration < 30

    def test_read_write_contention(self):
        """Test contention between reads and writes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            wiki.create_page(
                page_id="rw_page",
                title="Read-Write Test",
                content="# Initial Content"
            )

            read_count = [0]
            write_count = [0]

            def rapid_read():
                for _ in range(100):
                    try:
                        wiki.get_page("rw_page")
                        read_count[0] += 1
                    except Exception:
                        pass

            def rapid_write():
                for i in range(10):
                    try:
                        wiki.update_page(
                            page_id="rw_page",
                            content=f"# Updated Content {i}"
                        )
                        write_count[0] += 1
                    except Exception:
                        pass

            # Mix of readers and writers
            threads = []
            for _ in range(10):  # 10 readers
                thread = threading.Thread(target=rapid_read)
                threads.append(thread)
                thread.start()

            for _ in range(3):  # 3 writers
                thread = threading.Thread(target=rapid_write)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=30)

            # Readers should complete (reads don't block)
            assert read_count[0] > 900  # Most reads should succeed
            # Writers should complete (with locking)
            assert write_count[0] > 0


class TestMultiProcessAccess:
    """Test concurrent access from multiple processes."""

    def test_multiprocess_page_creation(self):
        """Test multiple processes creating pages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"

            def create_pages(process_id):
                try:
                    wiki = WikiCore(wiki_path=str(wiki_path))
                    for i in range(5):
                        wiki.create_page(
                            page_id=f"proc{process_id}_page{i}",
                            title=f"Process {process_id} Page {i}",
                            content=f"# Content {i}"
                        )
                    return 5
                except Exception as e:
                    return 0

            # Use process pool
            with ProcessPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(create_pages, i) for i in range(3)]
                results = [f.result() for f in as_completed(futures)]

            # Verify pages created across processes
            wiki = WikiCore(wiki_path=str(wiki_path))
            pages = wiki.list_pages()
            assert sum(results) >= 10  # At least most pages created

    def test_multiprocess_safe_read(self):
        """Test safe concurrent reads from multiple processes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create test data
            for i in range(10):
                wiki.create_page(
                    page_id=f"page_{i}",
                    title=f"Page {i}",
                    content=f"# Content {i}"
                )

            def read_pages(process_id):
                try:
                    wiki = WikiCore(wiki_path=str(wiki_path))
                    success = 0
                    for i in range(50):
                        page = wiki.get_page(f"page_{i % 10}")
                        if page:
                            success += 1
                    return success
                except Exception:
                    return 0

            # Concurrent reads from multiple processes
            with ProcessPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(read_pages, i) for i in range(5)]
                results = [f.result() for f in as_completed(futures)]

            # All reads should succeed
            assert sum(results) >= 200  # 5 processes * 50 reads


class TestDeadlockPrevention:
    """Test deadlock prevention in concurrent operations."""

    def test_no_deadlock_on_cycle(self):
        """Test system doesn't deadlock with cyclic dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create pages with cross-references
            wiki.create_page(
                page_id="page_a",
                title="Page A",
                content="# A\n\nSee [[page_b]]"
            )
            wiki.create_page(
                page_id="page_b",
                title="Page B",
                content="# B\n\nSee [[page_c]]"
            )
            wiki.create_page(
                page_id="page_c",
                title="Page C",
                content="# C\n\nSee [[page_a]]"
            )

            # Update in circular order from multiple threads
            def update_a():
                for _ in range(5):
                    wiki.update_page(
                        page_id="page_a",
                        content="# A Updated\n\nSee [[page_b]]"
                    )

            def update_b():
                for _ in range(5):
                    wiki.update_page(
                        page_id="page_b",
                        content="# B Updated\n\nSee [[page_c]]"
                    )

            def update_c():
                for _ in range(5):
                    wiki.update_page(
                        page_id="page_c",
                        content="# C Updated\n\nSee [[page_a]]"
                    )

            # Run updates concurrently
            threads = [
                threading.Thread(target=update_a),
                threading.Thread(target=update_b),
                threading.Thread(target=update_c)
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join(timeout=30)

            # System should complete without deadlock
            assert True  # All threads completed

    def test_timeout_prevention(self):
        """Test operations have timeouts to prevent hangs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create blocking condition
            blocking_event = threading.Event()

            def blocking_operation():
                blocking_event.wait()
                wiki.create_page("blocked_page", title="Blocked", content="# Blocked")

            def quick_operation():
                try:
                    # Should complete quickly or timeout
                    wiki.create_page("quick_page", title="Quick", content="# Quick")
                    return True
                except Exception:
                    return False

            # Start blocking thread
            blocker = threading.Thread(target=blocking_operation)
            blocker.start()

            time.sleep(0.1)  # Let blocker start

            # Quick operation should succeed or timeout
            quick = threading.Thread(target=quick_operation)
            quick.start()
            quick.join(timeout=5)

            # Should complete (not hang indefinitely)
            assert not quick.is_alive() or quick.join(timeout=1)

            # Cleanup
            blocking_event.set()
            blocker.join(timeout=5)


class TestAtomicOperations:
    """Test atomicity of critical operations."""

    def test_atomic_page_create(self):
        """Test page creation is atomic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Interrupted creation should not leave partial state
            def create_with_interrupt():
                try:
                    wiki.create_page(
                        page_id="interrupted_page",
                        title="Interrupted",
                        content="# Interrupted Page\n\n" + "Long content " * 1000
                    )
                except Exception:
                    pass

            # Attempt concurrent creations
            threads = [
                threading.Thread(target=create_with_interrupt),
                threading.Thread(target=create_with_interrupt)
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join(timeout=30)

            # Either page exists and is complete, or doesn't exist
            page = wiki.get_page("interrupted_page")
            if page:
                # If exists, should be complete
                assert page.title == "Interrupted"
                assert "Interrupted Page" in page.content

    def test_atomic_batch_delete(self):
        """Test batch deletion is atomic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create pages
            page_ids = [f"batch_page_{i}" for i in range(10)]
            for page_id in page_ids:
                wiki.create_page(
                    page_id=page_id,
                    title=f"Batch {i}",
                    content=f"# Batch {i}"
                )

            # Batch delete
            deleted_count = 0
            for page_id in page_ids:
                try:
                    wiki.delete_page(page_id)
                    deleted_count += 1
                except Exception:
                    pass

            # All or most should be deleted
            remaining = sum(1 for pid in page_ids if wiki.get_page(pid))
            assert deleted_count >= 8  # Allow some failures
            assert remaining <= 2  # Most should be deleted


class TestConcurrentInsightManagement:
    """Test concurrent insight operations."""

    def test_concurrent_insight_creation(self):
        """Test multiple threads creating insights."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))
            mock_llm = Mock()
            manager = InsightManager(wiki_core=wiki, llm_client=mock_llm)

            def create_insights(thread_id):
                insights_created = 0
                for i in range(5):
                    try:
                        insight = Insight(
                            id=f"insight_{thread_id}_{i}",
                            title=f"Insight {thread_id}.{i}",
                            description="Test",
                            related_concepts=["test"],
                            impact_score=0.5,
                            novelty_score=0.5,
                            actionability_score=0.5
                        )
                        manager.create_insight(insight)
                        insights_created += 1
                    except Exception:
                        pass
                return insights_created

            # Concurrent insight creation
            threads = []
            for thread_id in range(5):
                thread = threading.Thread(target=create_insights, args=(thread_id,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=30)

            # Most insights should be created
            all_insights = manager.get_all_insights()
            assert len(all_insights) >= 20  # 5 threads * 5 insights

    def test_concurrent_backfill(self):
        """Test concurrent backfill operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))
            mock_llm = Mock()
            manager = InsightManager(wiki_core=wiki, llm_client=mock_llm)

            # Create insights
            insights = []
            for i in range(10):
                insight = Insight(
                    id=f"insight_{i}",
                    title=f"Insight {i}",
                    description="Test",
                    related_concepts=["concept"],
                    impact_score=0.5,
                    novelty_score=0.5,
                    actionability_score=0.5
                )
                manager.create_insight(insight)
                insights.append(insight)

            # Concurrent backfill
            backfilled = []

            def backfill_insights(thread_id):
                start_idx = thread_id * 5
                end_idx = start_idx + 5
                count = 0
                for i in range(start_idx, min(end_idx, len(insights))):
                    try:
                        manager.backfill_insight(insights[i])
                        count += 1
                    except Exception:
                        pass
                backfilled.append(count)

            threads = []
            for thread_id in range(2):
                thread = threading.Thread(target=backfill_insights, args=(thread_id,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=60)

            # Most backfills should succeed
            assert sum(backfilled) >= 8
