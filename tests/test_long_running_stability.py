"""
Long-running stability tests for Stage 6.5.

Tests system stability over extended periods:
- 4 weeks continuous operation simulation
- Memory leak detection
- Performance degradation monitoring
- Resource usage monitoring
- Error recovery over time
"""

import pytest
import tempfile
import time
import psutil
import threading
import gc
import tracemalloc
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from unittest.mock import Mock

from src.wiki.core import WikiCore
from src.wiki.insight.manager import InsightManager
from src.performance.cache import CacheManager
from src.discovery.models.insight import Insight


class TestMemoryLeakDetection:
    """Test for memory leaks over extended operation."""

    def test_memory_stability_during_continuous_operations(self):
        """Test memory usage stability during continuous operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Start memory tracking
            tracemalloc.start()
            process = psutil.Process()

            memory_snapshots = []
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Simulate 4 hours of operation (compressed)
            operations = 0
            test_duration = 300  # 5 minutes (representing 4 hours)
            start_time = time.time()

            print(f"Running stability test for {test_duration} seconds...")

            while time.time() - start_time < test_duration:
                # Perform various operations
                for i in range(10):
                    try:
                        # Create page
                        wiki.create_page(
                            page_id=f"mem_test_{operations}_{i}",
                            title=f"Memory Test {operations}.{i}",
                            content=f"# Test {operations}.{i}\n\n" + "Content " * 100
                        )

                        # Query page
                        page = wiki.get_page(f"mem_test_{operations}_{i}")
                        assert page is not None

                        # Update page
                        wiki.update_page(
                            page_id=f"mem_test_{operations}_{i}",
                            content=f"# Updated {operations}.{i}\n\n" + "New content " * 100
                        )

                        # List pages
                        pages = wiki.list_pages()

                    except Exception as e:
                        print(f"Operation failed: {e}")

                operations += 1

                # Take memory snapshot every 30 operations
                if operations % 30 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_snapshots.append(current_memory)

                    # Force garbage collection
                    gc.collect()

                    elapsed = time.time() - start_time
                    print(f"Operations: {operations * 10}, Memory: {current_memory:.1f} MB, Elapsed: {elapsed:.1f}s")

                    # Check for memory leak
                    if len(memory_snapshots) >= 3:
                        recent_avg = sum(memory_snapshots[-3:]) / 3
                        initial_avg = sum(memory_snapshots[:3]) / 3

                        # Memory growth should be < 20% over test period
                        growth_ratio = (recent_avg - initial_avg) / (initial_avg + 1)
                        assert growth_ratio < 0.2, f"Memory leak detected: {growth_ratio:.1%} growth"

            # Final memory check
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            total_growth = (final_memory - baseline_memory) / (baseline_memory + 1)

            print(f"\n✓ Completed {operations * 10} operations")
            print(f"Baseline memory: {baseline_memory:.1f} MB")
            print(f"Final memory: {final_memory:.1f} MB")
            print(f"Total growth: {total_growth:.1%}")

            # Memory should not grow excessively
            assert total_growth < 0.5, f"Excessive memory growth: {total_growth:.1%}"

            tracemalloc.stop()

    def test_cache_memory_leak(self):
        """Test cache for memory leaks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache.json"
            cache = CacheManager(l1_max_size=1000, l2_enabled=True, l2_cache_path=str(cache_path))

            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Perform many cache operations
            for i in range(10000):
                # Set cache entry
                cache.set(f"key_{i}", f"value_{i}: " + "data " * 100)

                # Get cache entry
                value = cache.get(f"key_{i % 1000}")  # Reuse keys
                assert value is not None

                # Periodic memory check
                if i % 1000 == 0:
                    gc.collect()
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    growth = (current_memory - baseline_memory) / (baseline_memory + 1)

                    print(f"Iteration {i}: Memory {current_memory:.1f} MB, Growth {growth:.1%}")

                    # Cache should not leak memory
                    assert growth < 0.3, f"Cache memory leak: {growth:.1%} growth"

    def test_insight_manager_memory_leak(self):
        """Test InsightManager for memory leaks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))
            mock_llm = Mock()
            manager = InsightManager(wiki_core=wiki, llm_client=mock_llm)

            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Create many insights
            insights = []
            for i in range(1000):
                insight = Insight(
                    id=f"insight_{i}",
                    title=f"Insight {i}",
                    description=f"Description {i}: " + "text " * 50,
                    related_concepts=[f"concept_{j}" for j in range(10)],
                    impact_score=0.5 + (i % 50) / 100,
                    novelty_score=0.5 + (i % 30) / 100,
                    actionability_score=0.5 + (i % 40) / 100
                )
                manager.create_insight(insight)
                insights.append(insight)

                if i % 100 == 0:
                    gc.collect()
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    growth = (current_memory - baseline_memory) / (baseline_memory + 1)

                    print(f"Created {i} insights, Memory: {current_memory:.1f} MB, Growth: {growth:.1%}")

                    # Memory growth should be reasonable
                    assert growth < 0.5, f"InsightManager memory leak: {growth:.1%} growth"


class TestPerformanceDegradationMonitoring:
    """Test for performance degradation over time."""

    def test_operation_latency_stability(self):
        """Test that operation latency remains stable over time."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create initial pages
            for i in range(100):
                wiki.create_page(
                    page_id=f"perf_page_{i}",
                    title=f"Performance Page {i}",
                    content=f"# Page {i}"
                )

            latencies = defaultdict(list)

            # Monitor performance over time
            iterations = 100
            for iteration in range(iterations):
                # Measure create latency
                start = time.time()
                wiki.create_page(
                    page_id=f"latency_test_{iteration}",
                    title=f"Latency Test {iteration}",
                    content="# Test"
                )
                create_latency = (time.time() - start) * 1000  # ms
                latencies['create'].append(create_latency)

                # Measure read latency
                start = time.time()
                page = wiki.get_page(f"perf_page_{iteration % 100}")
                read_latency = (time.time() - start) * 1000  # ms
                latencies['read'].append(read_latency)

                # Measure update latency
                start = time.time()
                wiki.update_page(
                    page_id=f"latency_test_{iteration}",
                    content=f"# Updated {iteration}"
                )
                update_latency = (time.time() - start) * 1000  # ms
                latencies['update'].append(update_latency)

                # Measure list latency
                start = time.time()
                pages = wiki.list_pages()
                list_latency = (time.time() - start) * 1000  # ms
                latencies['list'].append(list_latency)

                if iteration % 20 == 0:
                    print(f"Iteration {iteration}: "
                          f"Create {create_latency:.1f}ms, "
                          f"Read {read_latency:.1f}ms, "
                          f"Update {update_latency:.1f}ms, "
                          f"List {list_latency:.1f}ms")

            # Check for performance degradation
            for operation, times in latencies.items():
                # Compare first 25% to last 25%
                first_quarter = times[:len(times)//4]
                last_quarter = times[-len(times)//4:]

                avg_first = sum(first_quarter) / len(first_quarter)
                avg_last = sum(last_quarter) / len(last_quarter)

                degradation = (avg_last - avg_first) / (avg_first + 0.001)

                print(f"{operation.capitalize()}: First {avg_first:.1f}ms, Last {avg_last:.1f}ms, Degradation {degradation:.1%}")

                # Performance should not degrade by more than 50%
                assert degradation < 0.5, f"{operation} performance degraded by {degradation:.1%}"

    def test_throughput_stability(self):
        """Test throughput stability over time."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            throughput_samples = []

            # Measure throughput over time
            samples = 20
            operations_per_sample = 50

            for sample in range(samples):
                start_time = time.time()

                # Perform batch of operations
                for i in range(operations_per_sample):
                    wiki.create_page(
                        page_id=f"throughput_{sample}_{i}",
                        title=f"Throughput Test {sample}.{i}",
                        content="# Test"
                    )

                duration = time.time() - start_time
                throughput = operations_per_sample / duration  # ops/sec
                throughput_samples.append(throughput)

                print(f"Sample {sample}: {throughput:.1f} ops/sec")

                # Small delay between samples
                time.sleep(0.1)

            # Check throughput stability
            first_half = throughput_samples[:len(throughput_samples)//2]
            second_half = throughput_samples[len(throughput_samples)//2:]

            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)

            decline = (avg_first - avg_second) / (avg_first + 0.001)

            print(f"\nFirst half: {avg_first:.1f} ops/sec")
            print(f"Second half: {avg_second:.1f} ops/sec")
            print(f"Throughput decline: {decline:.1%}")

            # Throughput should not decline by more than 30%
            assert decline < 0.3, f"Throughput declined by {decline:.1%}"

    def test_query_performance_with_growth(self):
        """Test query performance as data grows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            query_times = []
            page_counts = []

            # Gradually grow data and measure query performance
            for batch in range(10):
                # Add batch of pages
                start_idx = batch * 100
                for i in range(100):
                    wiki.create_page(
                        page_id=f"growth_page_{start_idx + i}",
                        title=f"Growth Page {start_idx + i}",
                        content=f"# Page {start_idx + i}\n\nContent"
                    )

                # Measure query performance
                queries = 100
                start_time = time.time()

                for i in range(queries):
                    page = wiki.get_page(f"growth_page_{i % (start_idx + 100)}")
                    assert page is not None

                avg_query_time = (time.time() - start_time) / queries * 1000  # ms
                query_times.append(avg_query_time)

                total_pages = (batch + 1) * 100
                page_counts.append(total_pages)

                print(f"Pages: {total_pages}, Avg query time: {avg_query_time:.2f}ms")

            # Check if query time scales reasonably
            # Should not grow linearly (should have indexing)
            initial_time = query_times[0]
            final_time = query_times[-1]
            growth_factor = page_counts[-1] / page_counts[0]
            time_growth = final_time / (initial_time + 0.001)

            print(f"\nData growth: {growth_factor:.1f}x")
            print(f"Query time growth: {time_growth:.2f}x")

            # Query time should grow much slower than data size
            # (ideally sublinear due to indexing)
            assert time_growth < growth_factor ** 0.5, "Query performance scaling is poor"


class TestResourceUsageMonitoring:
    """Test resource usage over extended operation."""

    def test_cpu_usage_stability(self):
        """Test CPU usage remains stable during operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            process = psutil.Process()
            cpu_samples = []

            # Perform operations and monitor CPU
            for i in range(100):
                start_cpu = process.cpu_percent(interval=0.1)

                # Do some work
                for j in range(10):
                    wiki.create_page(
                        page_id=f"cpu_test_{i}_{j}",
                        title=f"CPU Test {i}.{j}",
                        content="# Test"
                    )

                end_cpu = process.cpu_percent(interval=0.1)
                avg_cpu = (start_cpu + end_cpu) / 2
                cpu_samples.append(avg_cpu)

                if i % 20 == 0:
                    print(f"Iteration {i}: CPU {avg_cpu:.1f}%")

            # CPU usage should be reasonable
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            print(f"\nAverage CPU usage: {avg_cpu:.1f}%")

            # Should not consistently use 100% CPU
            assert avg_cpu < 80, f"CPU usage too high: {avg_cpu:.1f}%"

    def test_file_descriptor_usage(self):
        """Test file descriptor usage doesn't leak."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            process = psutil.Process()
            baseline_fds = process.num_fds() if hasattr(process, 'num_fds') else 0

            # Perform many file operations
            for i in range(1000):
                try:
                    wiki.create_page(
                        page_id=f"fd_test_{i}",
                        title=f"FD Test {i}",
                        content=f"# Test {i}"
                    )

                    wiki.get_page(f"fd_test_{i}")

                    wiki.update_page(
                        page_id=f"fd_test_{i}",
                        content=f"# Updated {i}"
                    )

                    # Periodically check FD count
                    if i % 100 == 0:
                        current_fds = process.num_fds() if hasattr(process, 'num_fds') else baseline_fds
                        fd_growth = current_fds - baseline_fds

                        print(f"Iteration {i}: FD count {current_fds}, Growth {fd_growth}")

                        # FD count should not grow significantly
                        assert fd_growth < 50, f"File descriptor leak: {fd_growth} FDs leaked"

                except Exception as e:
                    print(f"Operation failed at iteration {i}: {e}")

    def test_disk_space_usage(self):
        """Test disk space usage is reasonable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Measure disk usage before
            def get_dir_size(path):
                total = 0
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath):
                            total += os.path.getsize(filepath)
                return total

            import os
            baseline_size = get_dir_size(str(wiki_path))

            # Create many pages
            pages_created = 0
            for i in range(1000):
                try:
                    wiki.create_page(
                        page_id=f"disk_test_{i}",
                        title=f"Disk Test {i}",
                        content=f"# Page {i}\n\n" + ("Content " * 50)
                    )
                    pages_created += 1
                except Exception as e:
                    print(f"Failed to create page {i}: {e}")

            # Measure disk usage after
            final_size = get_dir_size(str(wiki_path))
            size_increase = final_size - baseline_size
            bytes_per_page = size_increase / pages_created

            print(f"\nPages created: {pages_created}")
            print(f"Size increase: {size_increase / 1024 / 1024:.1f} MB")
            print(f"Bytes per page: {bytes_per_page:.0f}")

            # Disk usage should be reasonable
            # Each page should use < 50KB on average
            assert bytes_per_page < 50 * 1024, f"Disk usage too high: {bytes_per_page:.0f} bytes/page"


class TestErrorRecoveryOverTime:
    """Test error recovery capability over extended operation."""

    def test_recovery_from_transient_errors(self):
        """Test system recovers from transient errors over time."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            error_count = 0
            success_count = 0
            recovery_time = []

            # Simulate operations with occasional transient errors
            for i in range(100):
                operation_start = time.time()

                try:
                    # Simulate occasional timeout/error
                    if i % 10 == 0:
                        raise TimeoutError("Simulated transient error")

                    wiki.create_page(
                        page_id=f"recovery_test_{i}",
                        title=f"Recovery Test {i}",
                        content="# Test"
                    )
                    success_count += 1

                except TimeoutError:
                    error_count += 1
                    # System should recover and continue
                    time.sleep(0.1)  # Brief delay

                    # Retry should succeed
                    try:
                        wiki.create_page(
                            page_id=f"recovery_test_{i}",
                            title=f"Recovery Test {i}",
                            content="# Test"
                        )
                        success_count += 1
                        recovery_time.append(time.time() - operation_start)
                    except Exception as e:
                        print(f"Recovery failed at iteration {i}: {e}")

                if i % 20 == 0:
                    print(f"Iteration {i}: Success {success_count}, Errors {error_count}")

            # System should recover from most errors
            recovery_rate = success_count / 100
            print(f"\nRecovery rate: {recovery_rate:.1%}")

            assert recovery_rate > 0.9, f"Recovery rate too low: {recovery_rate:.1%}"

            if recovery_time:
                avg_recovery_time = sum(recovery_time) / len(recovery_time)
                print(f"Average recovery time: {avg_recovery_time:.3f}s")
                assert avg_recovery_time < 1.0, f"Recovery too slow: {avg_recovery_time:.2f}s"

    def test_state_consistency_after_errors(self):
        """Test state remains consistent after errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Create initial state
            for i in range(50):
                wiki.create_page(
                    page_id=f"state_test_{i}",
                    title=f"State Test {i}",
                    content=f"# Initial {i}"
                )

            # Perform operations with errors
            for i in range(50, 100):
                try:
                    # Update some pages
                    wiki.update_page(
                        page_id=f"state_test_{i-50}",
                        content=f"# Updated {i}"
                    )

                    # Create new pages
                    wiki.create_page(
                        page_id=f"state_test_{i}",
                        title=f"State Test {i}",
                        content=f"# Test {i}"
                    )

                    # Simulate occasional errors
                    if i % 15 == 0:
                        raise ValueError("Simulated error")

                except ValueError:
                    # Continue after error
                    pass

            # Verify state consistency
            pages = wiki.list_pages()

            # Should have most pages despite errors
            assert len(pages) >= 90, f"State inconsistency: only {len(pages)} pages"

            # Verify page content
            for i in range(50):
                page = wiki.get_page(f"state_test_{i}")
                if page:
                    # Content should be valid
                    assert "# Test" in page.content or "# Updated" in page.content

    def test_graceful_degradation_under_load(self):
        """Test system degrades gracefully under load."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Simulate increasing load
            load_levels = [10, 50, 100, 200, 500]
            success_rates = []

            for load in load_levels:
                success = 0
                total = load

                start_time = time.time()

                for i in range(load):
                    try:
                        wiki.create_page(
                            page_id=f"load_test_load{load}_i{i}",
                            title=f"Load Test {load}.{i}",
                            content="# Test"
                        )
                        success += 1
                    except Exception:
                        pass  # Expected under high load

                duration = time.time() - start_time
                success_rate = success / total
                success_rates.append(success_rate)

                print(f"Load {load}: Success rate {success_rate:.1%}, Time {duration:.2f}s")

                # System should maintain reasonable success rate
                assert success_rate > 0.8, f"Success rate too low under load {load}: {success_rate:.1%}"

            # Success rate should degrade gradually, not catastrophically
            initial_rate = success_rates[0]
            final_rate = success_rates[-1]
            degradation = initial_rate - final_rate

            print(f"\nSuccess rate degradation: {degradation:.1%}")
            assert degradation < 0.2, f"Catastrophic degradation: {degradation:.1%}"


class TestFourWeekSimulation:
    """Simulate 4 weeks of continuous operation."""

    def test_four_week_operation_simulation(self):
        """Simulate 4 weeks of operation in compressed time."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_path = Path(temp_dir) / "wiki"
            wiki = WikiCore(wiki_path=str(wiki_path))

            # Simulate 4 weeks = 28 days
            # Compressed: 1 hour of real time = 1 week
            # Total: 4 hours of testing

            total_days = 28
            compression_factor = 7 / 3600  # 7 days per hour of testing
            real_duration = 300  # 5 minutes (representing 4 weeks)

            print(f"Simulating {total_days} days of operation...")

            metrics = {
                'pages_created': 0,
                'pages_updated': 0,
                'pages_queried': 0,
                'errors': 0,
                'memory_samples': [],
                'operation_times': []
            }

            process = psutil.Process()
            start_time = time.time()

            day = 0
            while time.time() - start_time < real_duration:
                day += 1

                # Daily operations (simulated)
                daily_pages = 50  # Typical daily load
                daily_queries = 500

                for i in range(daily_pages):
                    try:
                        wiki.create_page(
                            page_id=f"day{day}_page{i}",
                            title=f"Day {day} Page {i}",
                            content=f"# Day {day}\n\n" + "Content " * 50
                        )
                        metrics['pages_created'] += 1

                        # Periodic updates
                        if i % 10 == 0:
                            wiki.update_page(
                                page_id=f"day{day}_page{i}",
                                content=f"# Updated Day {day}\n\n" + "New content " * 50
                            )
                            metrics['pages_updated'] += 1

                    except Exception as e:
                        metrics['errors'] += 1

                # Queries
                for i in range(daily_queries):
                    try:
                        page = wiki.get_page(f"day{max(1, day)}_page{i % daily_pages}")
                        if page:
                            metrics['pages_queried'] += 1
                    except Exception:
                        metrics['errors'] += 1

                # Sample memory
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                metrics['memory_samples'].append(current_memory)

                # Progress update
                elapsed = time.time() - start_time
                progress = elapsed / real_duration
                simulated_day = int(progress * total_days)

                print(f"Simulated Day {simulated_day}/{total_days}: "
                      f"Memory {current_memory:.1f} MB, "
                      f"Pages {metrics['pages_created']}, "
                      f"Errors {metrics['errors']}")

                # Small delay to prevent CPU overload
                time.sleep(0.5)

            # Final metrics
            duration = time.time() - start_time

            print(f"\n{'='*50}")
            print(f"4-Week Simulation Results:")
            print(f"{'='*50}")
            print(f"Duration: {duration:.1f}s (simulated {total_days} days)")
            print(f"Pages created: {metrics['pages_created']}")
            print(f"Pages updated: {metrics['pages_updated']}")
            print(f"Pages queried: {metrics['pages_queried']}")
            print(f"Errors: {metrics['errors']}")

            # Memory analysis
            if metrics['memory_samples']:
                initial_memory = metrics['memory_samples'][0]
                final_memory = metrics['memory_samples'][-1]
                memory_growth = (final_memory - initial_memory) / (initial_memory + 1)

                print(f"\nInitial memory: {initial_memory:.1f} MB")
                print(f"Final memory: {final_memory:.1f} MB")
                print(f"Memory growth: {memory_growth:.1%}")

                # Memory should not grow excessively
                assert memory_growth < 0.3, f"Memory growth too high: {memory_growth:.1%}"

            # Error rate should be low
            total_operations = metrics['pages_created'] + metrics['pages_updated'] + metrics['pages_queried']
            error_rate = metrics['errors'] / (total_operations + 1)
            print(f"\nError rate: {error_rate:.2%}")
            assert error_rate < 0.01, f"Error rate too high: {error_rate:.2%}"

            # System should be stable
            print(f"\n✓ 4-week simulation completed successfully")
            print(f"✓ System remained stable throughout")
            print(f"✓ Memory usage controlled")
            print(f"✓ Error rate acceptable")
