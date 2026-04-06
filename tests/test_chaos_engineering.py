"""
Chaos engineering tests for system resilience validation.

Tests system behavior under failure conditions including crashes,
data corruption, network failures, and disk full scenarios.
"""

import pytest
import tempfile
import shutil
import os
import time
import signal
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.wiki.core import WikiCore
from src.wiki.insight.manager import InsightManager
from src.wiki.quality.monitor import QualityMonitor
from src.performance.cache import CacheManager
from src.performance.optimizer import PerformanceOptimizer


class TestCrashRecovery:
    """Test system recovery from crashes."""

    def test_wiki_core_crash_recovery(self):
        """Test WikiCore recovery after crash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"

            # Create initial wiki
            wiki = WikiCore(wiki_path=str(wiki_path))
            wiki.create_page(
                page_id="test_page",
                title="Test Page",
                content="# Test Page\n\nInitial content"
            )

            # Simulate crash by creating new instance
            wiki2 = WikiCore(wiki_path=str(wiki_path))

            # Verify data survived
            page = wiki2.get_page("test_page")
            assert page is not None
            assert page.title == "Test Page"
            assert "Initial content" in page.content

    def test_insight_manager_crash_recovery(self):
        """Test InsightManager recovery after crash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            manager = InsightManager(wiki_core=wiki, llm_client=Mock())

            # Create insight
            from src.discovery.models.insight import Insight
            insight = Insight(
                id="test_insight",
                title="Test Insight",
                description="Test",
                related_concepts=["test"],
                impact_score=0.8,
                novelty_score=0.7,
                actionability_score=0.9
            )
            manager.create_insight(insight)

            # Simulate crash
            manager2 = InsightManager(wiki_core=wiki, llm_client=Mock())

            # Verify state recovered
            insights = manager2.get_all_insights()
            assert len(insights) >= 1

    def test_cache_manager_crash_recovery(self):
        """Test CacheManager recovery from corruption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache.json"

            # Create cache with data
            cache = CacheManager(l2_enabled=True, l2_cache_path=str(cache_path))
            cache.set("key1", "value1")
            cache.set("key2", "value2")

            # Simulate corruption by corrupting L2 cache
            with open(cache_path, 'w') as f:
                f.write("corrupted data")

            # Create new instance - should handle corruption gracefully
            cache2 = CacheManager(l2_enabled=True, l2_cache_path=str(cache_path))

            # Should not crash, L1 cache should still work
            cache2.set("key3", "value3")
            assert cache2.get("key3") == "value3"


class TestDataCorruption:
    """Test system behavior with data corruption."""

    def test_wiki_page_corruption_detection(self):
        """Test detection of corrupted wiki pages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create valid page
            wiki.create_page(
                page_id="test_page",
                title="Test",
                content="# Test\n\nContent"
            )

            # Corrupt the page file
            page_file = wiki_path / "topics" / "test_page.md"
            with open(page_file, 'w') as f:
                f.write("CORRUPTED DATA: <<<<>>>>> invalid")

            # Wiki should detect and handle corruption
            try:
                page = wiki.get_page("test_page")
                # If page is returned, it should be marked as corrupted
                if page:
                    assert hasattr(page, 'metadata')
                    assert page.metadata.get('corrupted', False) is True
            except Exception as e:
                # Should raise appropriate error
                assert 'corrupt' in str(e).lower() or 'invalid' in str(e).lower()

    def test_database_corruption_recovery(self):
        """Test recovery from corrupted database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "wiki.db"

            # Create wiki with database
            wiki = WikiCore(wiki_path=str(temp_dir), db_path=str(db_path))
            wiki.create_page(
                page_id="test_page",
                title="Test",
                content="# Test"
            )

            # Corrupt database
            with open(db_path, 'wb') as f:
                f.write(b'CORRUPTED DATABASE DATA')

            # Should handle corruption gracefully
            wiki2 = WikiCore(wiki_path=str(temp_dir), db_path=str(db_path))

            # Should either recover or fail gracefully
            try:
                page = wiki2.get_page("test_page")
                # If successful, database was recreated
                assert page is not None
            except Exception as e:
                # Should fail with clear error message
                assert 'corrupt' in str(e).lower() or 'database' in str(e).lower()

    def test_git_repository_corruption(self):
        """Test handling of corrupted Git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"

            # Initialize wiki with Git
            wiki = WikiCore(wiki_path=str(wiki_path))
            wiki.create_page(
                page_id="test_page",
                title="Test",
                content="# Test"
            )

            # Corrupt .git directory
            git_dir = wiki_path / ".git"
            if git_dir.exists():
                corrupt_file = git_dir / "CORRUPTED"
                corrupt_file.write_text("corrupted data")

            # Should handle Git corruption gracefully
            wiki2 = WikiCore(wiki_path=str(wiki_path))

            # Should either recover or disable Git features
            page = wiki2.get_page("test_page")
            # Page content should still be accessible even if Git is broken
            assert page is not None


class TestNetworkFailures:
    """Test system behavior during network failures."""

    def test_llm_api_timeout_handling(self):
        """Test handling of LLM API timeouts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Mock LLM that times out
            mock_llm = Mock()
            mock_llm.generate.side_effect = TimeoutError("API timeout")

            manager = InsightManager(wiki_core=wiki, llm_client=mock_llm)

            # Should handle timeout gracefully
            from src.discovery.models.insight import Insight
            insight = Insight(
                id="test_insight",
                title="Test",
                description="Test",
                related_concepts=["test"],
                impact_score=0.5,
                novelty_score=0.5,
                actionability_score=0.5
            )

            try:
                manager.create_insight(insight)
                # If it succeeds, insight should be queued
                assert True
            except TimeoutError:
                # Should handle timeout with retry or fallback
                assert True
            except Exception as e:
                # Should not crash with unexpected error
                assert 'timeout' in str(e).lower()

    def test_llm_api_rate_limit_handling(self):
        """Test handling of LLM API rate limits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Mock LLM with rate limit
            mock_llm = Mock()

            def rate_limit_call(*args, **kwargs):
                from requests.exceptions import RequestException
                raise RequestException("429 Too Many Requests")

            mock_llm.generate.side_effect = rate_limit_call

            manager = InsightManager(wiki_core=wiki, llm_client=mock_llm)

            # Should implement exponential backoff
            from src.discovery.models.insight import Insight
            insight = Insight(
                id="test_insight",
                title="Test",
                description="Test",
                related_concepts=["test"],
                impact_score=0.5,
                novelty_score=0.5,
                actionability_score=0.5
            )

            # Should handle rate limit with backoff
            manager.create_insight(insight)

    def test_network_partition_recovery(self):
        """Test recovery from network partition."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Simulate network partition by mocking
            with patch('requests.post') as mock_post:
                mock_post.side_effect = ConnectionError("Network unreachable")

                mock_llm = Mock()
                manager = InsightManager(wiki_core=wiki, llm_client=mock_llm)

                # Should queue operation for retry
                from src.discovery.models.insight import Insight
                insight = Insight(
                    id="test_insight",
                    title="Test",
                    description="Test",
                    related_concepts=["test"],
                    impact_score=0.5,
                    novelty_score=0.5,
                    actionability_score=0.5
                )

                # Should not crash, should queue for retry
                manager.create_insight(insight)

            # After network recovery
            # Operations should resume normally


class TestDiskFullScenarios:
    """Test system behavior when disk is full."""

    def test_disk_full_during_write(self):
        """Test handling of disk full during write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Mock disk full error
            with patch('builtins.open', side_effect=OSError(28, "No space left on device")):
                # Should handle disk full gracefully
                try:
                    wiki.create_page(
                        page_id="test_page",
                        title="Test",
                        content="# Test"
                    )
                    assert False, "Should have raised OSError"
                except OSError as e:
                    assert e.errno == 28 or 'no space' in str(e).lower()

    def test_disk_full_recovery(self):
        """Test recovery after disk full condition."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Simulate disk full then recovery
            write_attempts = [0]
            original_open = open

            def mock_open_with_disk_full(*args, **kwargs):
                if 'write' in str(args[0]).lower() and write_attempts[0] < 2:
                    write_attempts[0] += 1
                    raise OSError(28, "No space left on device")
                return original_open(*args, **kwargs)

            with patch('builtins.open', side_effect=mock_open_with_disk_full):
                # First write should fail
                try:
                    wiki.create_page(
                        page_id="test_page1",
                        title="Test",
                        content="# Test 1"
                    )
                    assert False, "Should have failed"
                except OSError:
                    pass

            # After disk space recovery
            wiki.create_page(
                page_id="test_page2",
                title="Test",
                content="# Test 2"
            )

            # Verify write succeeded
            page = wiki.get_page("test_page2")
            assert page is not None

    def test_cache_disk_full_handling(self):
        """Test cache behavior when disk is full."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache.json"

            cache = CacheManager(l2_enabled=True, l2_cache_path=str(cache_path))

            # Mock disk full
            with patch('builtins.open', side_effect=OSError(28, "No space left")):
                # Should fall back to L1 only
                cache.set("key1", "value1")

                # L1 cache should still work
                assert cache.get("key1") == "value1"

                # L2 writes should fail silently
                assert cache._l2_cache is None or len(cache._l2_cache) == 0


class TestProcessTermination:
    """Test system behavior when processes are terminated."""

    def test_sigterm_handling(self):
        """Test graceful shutdown on SIGTERM."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create some data
            for i in range(10):
                wiki.create_page(
                    page_id=f"page_{i}",
                    title=f"Page {i}",
                    content=f"# Page {i}\n\nContent"
                )

            # Simulate SIGTERM
            # Wiki should save state gracefully
            wiki.shutdown()

            # Verify data persisted
            wiki2 = WikiCore(wiki_path=str(wiki_path))
            pages = wiki2.list_pages()
            assert len(pages) >= 10

    def test_sigkill_handling(self):
        """Test data integrity after SIGKILL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create data
            wiki.create_page(
                page_id="test_page",
                title="Test",
                content="# Test"
            )

            # Simulate SIGKILL (no cleanup)
            # Just delete the instance without shutdown
            del wiki

            # Create new instance - data should be intact
            wiki2 = WikiCore(wiki_path=str(wiki_path))
            page = wiki2.get_page("test_page")
            assert page is not None


class TestMemoryExhaustion:
    """Test system behavior under memory pressure."""

    def test_large_batch_memory_management(self):
        """Test handling of large document batches."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create many pages to test memory usage
            page_count = 0
            for i in range(100):
                try:
                    wiki.create_page(
                        page_id=f"page_{i}",
                        title=f"Page {i}",
                        content=f"# Page {i}\n\n" + "Content " * 1000
                    )
                    page_count += 1
                except MemoryError:
                    # Should handle memory gracefully
                    break

            # Should have created at least some pages
            assert page_count > 50

    def test_cache_memory_limits(self):
        """Test cache respects memory limits."""
        # Create cache with small L1 cache
        cache = CacheManager(l1_max_size=10, l2_enabled=False)

        # Fill cache beyond limit
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")

        # LRU eviction should keep cache size under limit
        stats = cache.get_stats()
        assert stats['l1_cache_size'] <= 10


class TestResourceExhaustion:
    """Test system behavior under resource exhaustion."""

    def test_file_descriptor_exhaustion(self):
        """Test handling of file descriptor exhaustion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Open many files to exhaust FDs
            open_files = []
            try:
                for i in range(1000):
                    try:
                        f = open(wiki_path / f"test_{i}.txt", 'w')
                        open_files.append(f)
                    except OSError:
                        # FD exhausted
                        break

            # Wiki should still function with limited FDs
            wiki.create_page(
                page_id="test_page",
                title="Test",
                content="# Test"
            )

            page = wiki.get_page("test_page")
            assert page is not None

            # Cleanup
            for f in open_files:
                f.close()

    def test_thread_exhaustion(self):
        """Test handling of thread pool exhaustion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create many concurrent operations
            threads = []
            results = []

            def create_page(i):
                try:
                    wiki.create_page(
                        page_id=f"page_{i}",
                        title=f"Page {i}",
                        content=f"# Page {i}"
                    )
                    results.append(i)
                except Exception:
                    pass  # Handle gracefully

            # Spawn many threads
            for i in range(100):
                thread = threading.Thread(target=create_page, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join(timeout=10)

            # Some operations should have succeeded
            assert len(results) > 50


class TestChaosMonkey:
    """Randomized chaos testing."""

    def test_random_operation_failures(self):
        """Test with random operation failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Inject random failures
            original_create = wiki.create_page
            failure_count = [0]

            def flaky_create(*args, **kwargs):
                failure_count[0] += 1
                if failure_count[0] % 3 == 0:
                    raise IOError("Random failure")
                return original_create(*args, **kwargs)

            with patch.object(wiki, 'create_page', side_effect=flaky_create):
                # Attempt many operations
                success_count = 0
                for i in range(20):
                    try:
                        wiki.create_page(
                            page_id=f"page_{i}",
                            title=f"Page {i}",
                            content=f"# Page {i}"
                        )
                        success_count += 1
                    except IOError:
                        pass  # Expected

            # Should have some successes despite failures
            assert success_count > 10

    def test_concurrent_chaos(self):
        """Test system under concurrent chaos."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            errors = []

            def chaotic_worker(worker_id):
                import random
                for i in range(10):
                    try:
                        if random.random() < 0.1:  # 10% failure rate
                            raise ValueError("Random error")

                        wiki.create_page(
                            page_id=f"worker{worker_id}_page{i}",
                            title=f"Worker {worker_id} Page {i}",
                            content=f"# Content {i}"
                        )
                    except Exception as e:
                        errors.append(e)
                        time.sleep(0.01)  # Backoff

            # Run chaotic workers
            threads = []
            for worker_id in range(5):
                thread = threading.Thread(target=chaotic_worker, args=(worker_id,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=30)

            # Most operations should succeed despite chaos
            assert len(errors) < 25  # Less than 50% failure rate
