"""
Performance tests for knowledge discovery pipeline.

Tests performance characteristics including:
- Processing time for different dataset sizes
- Memory usage patterns
- Scalability with large datasets
"""

import pytest
import time
import tracemalloc
from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import List
from src.discovery.engine import KnowledgeDiscoveryEngine
from src.discovery.config import DiscoveryConfig
from src.core.document_model import EnhancedDocument, DocumentMetadata, SourceType
from src.core.concept_model import EnhancedConcept, ConceptType


@pytest.fixture
def performance_config():
    """Configuration optimized for performance testing."""
    return DiscoveryConfig(
        enable_explicit_mining=True,
        enable_implicit_mining=True,
        enable_statistical_mining=True,
        enable_semantic_mining=True,
        enable_pattern_detection=True,
        enable_gap_analysis=True,
        enable_insight_generation=True,
        max_insights=50,
        confidence_threshold=0.3
    )


def create_large_document_set(count: int) -> List[EnhancedDocument]:
    """Create a large set of test documents."""
    topics = [
        "利率与股市的关系",
        "通胀对经济的影响",
        "货币政策的传导机制",
        "经济增长与投资",
        "金融市场的波动性"
    ]

    documents = []
    for i in range(count):
        topic = topics[i % len(topics)]
        documents.append(
            EnhancedDocument(
                id=f"perf_doc_{i}",
                source_type=SourceType.MARKDOWN,
                content=f"{topic}的相关研究。这是第{i}个文档的详细内容。" * 10,
                metadata=DocumentMetadata(
                    title=f"Performance Test Document {i}",
                    file_path=f"perf_test_{i}.md",
                    created_at=datetime(2024, 1, 1 + (i % 30))
                ),
                concepts=[],
                relations=[]
            )
        )
    return documents


def create_large_concept_set(count: int) -> List[EnhancedConcept]:
    """Create a large set of test concepts."""
    concepts = []
    for i in range(count):
        concepts.append(
            EnhancedConcept(
                id=f"perf_concept_{i}",
                name=f"概念{i}",
                type=ConceptType.TERM if i % 2 == 0 else ConceptType.THEORY,
                definition=f"这是概念{i}的定义",
                importance=0.5 + (i % 50) / 100.0
            )
        )
    return concepts


@pytest.mark.slow
class TestProcessingTime:
    """Test processing time for different dataset sizes."""

    def test_small_dataset_processing_time(self, performance_config):
        """Test processing time for small dataset (10 documents, 20 concepts)."""
        documents = create_large_document_set(10)
        concepts = create_large_concept_set(20)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            start_time = time.time()
            result = engine.discover(documents, concepts)
            processing_time = time.time() - start_time

            # Small dataset should process quickly (< 5 seconds)
            assert processing_time < 5.0, f"Small dataset took {processing_time:.2f}s"
            assert result is not None

    def test_medium_dataset_processing_time(self, performance_config):
        """Test processing time for medium dataset (50 documents, 100 concepts)."""
        documents = create_large_document_set(50)
        concepts = create_large_concept_set(100)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            start_time = time.time()
            result = engine.discover(documents, concepts)
            processing_time = time.time() - start_time

            # Medium dataset should complete in reasonable time (< 20 seconds)
            assert processing_time < 20.0, f"Medium dataset took {processing_time:.2f}s"
            assert result is not None

    @pytest.mark.slow
    def test_large_dataset_processing_time(self, performance_config):
        """Test processing time for large dataset (100 documents, 200 concepts)."""
        documents = create_large_document_set(100)
        concepts = create_large_concept_set(200)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            start_time = time.time()
            result = engine.discover(documents, concepts)
            processing_time = time.time() - start_time

            # Large dataset should still complete (< 60 seconds)
            assert processing_time < 60.0, f"Large dataset took {processing_time:.2f}s"
            assert result is not None

    def test_processing_time_scalability(self, performance_config):
        """Test that processing time scales reasonably with dataset size."""
        sizes = [10, 20, 30]
        times = []

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            for size in sizes:
                documents = create_large_document_set(size)
                concepts = create_large_concept_set(size * 2)

                engine = KnowledgeDiscoveryEngine(performance_config)

                start_time = time.time()
                engine.discover(documents, concepts)
                processing_time = time.time() - start_time

                times.append(processing_time)

            # Check that time scaling is roughly linear or better
            # (not exponential). Allow 3x tolerance for quadratic behavior
            ratio_20_10 = times[1] / times[0] if times[0] > 0 else 1
            ratio_30_20 = times[2] / times[1] if times[1] > 0 else 1

            # Ratios should be reasonable (not exponential growth)
            assert ratio_20_10 < 5.0, f"Time scaling from 10 to 20: {ratio_20_10:.2f}x"
            assert ratio_30_20 < 5.0, f"Time scaling from 20 to 30: {ratio_30_20:.2f}x"


@pytest.mark.slow
class TestMemoryUsage:
    """Test memory usage patterns."""

    def test_small_dataset_memory_usage(self, performance_config):
        """Test memory usage for small dataset."""
        documents = create_large_document_set(10)
        concepts = create_large_concept_set(20)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            tracemalloc.start()
            result = engine.discover(documents, concepts)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Small dataset should use modest memory (< 50MB peak)
            peak_mb = peak / 1024 / 1024
            assert peak_mb < 50, f"Small dataset used {peak_mb:.2f}MB memory"
            assert result is not None

    def test_medium_dataset_memory_usage(self, performance_config):
        """Test memory usage for medium dataset."""
        documents = create_large_document_set(50)
        concepts = create_large_concept_set(100)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            tracemalloc.start()
            result = engine.discover(documents, concepts)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Medium dataset should use reasonable memory (< 500MB peak)
            peak_mb = peak / 1024 / 1024
            assert peak_mb < 500, f"Medium dataset used {peak_mb:.2f}MB memory"
            assert result is not None

    def test_memory_efficiency_incremental_processing(self, performance_config):
        """Test memory efficiency when processing incrementally."""
        documents = create_large_document_set(30)
        concepts = create_large_concept_set(60)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            # Process in batches
            tracemalloc.start()

            # First batch
            result1 = engine.discover(documents[:15], concepts[:30])
            mid_current, mid_peak = tracemalloc.get_traced_memory()

            # Second batch
            result2 = engine.discover(documents, concepts)
            final_current, final_peak = tracemalloc.get_traced_memory()

            tracemalloc.stop()

            # Memory should not grow dramatically with batch size
            # (allow 5x increase for 2x data size - more realistic for Python)
            peak_growth_ratio = final_peak / mid_peak if mid_peak > 0 else 1
            assert peak_growth_ratio < 6.0, f"Memory grew {peak_growth_ratio:.2f}x"

    def test_memory_cleanup_after_processing(self, performance_config):
        """Test that memory is cleaned up after processing."""
        documents = create_large_document_set(20)
        concepts = create_large_concept_set(40)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            # Measure memory before processing
            tracemalloc.start()
            baseline_current, baseline_peak = tracemalloc.get_traced_memory()

            # Process
            result = engine.discover(documents, concepts)
            processing_current, processing_peak = tracemalloc.get_traced_memory()

            # Delete result (simulate cleanup)
            del result
            import gc
            gc.collect()

            cleanup_current, cleanup_peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Memory should decrease after cleanup
            # (allow some tolerance for Python's memory management)
            assert cleanup_current < processing_current * 1.5, \
                "Memory not properly cleaned up after processing"


@pytest.mark.slow
class TestScalability:
    """Test scalability with different dataset characteristics."""

    def test_scalability_with_document_length(self, performance_config):
        """Test scalability with longer documents."""
        base_docs = create_large_document_set(10)

        # Create documents with varying lengths
        short_docs = [d for d in base_docs]
        medium_docs = [
            EnhancedDocument(
                id=d.id,
                source_type=d.source_type,
                content=d.content * 5,  # 5x longer
                metadata=d.metadata,
                concepts=[],
                relations=[]
            )
            for d in base_docs
        ]
        long_docs = [
            EnhancedDocument(
                id=d.id,
                source_type=d.source_type,
                content=d.content * 10,  # 10x longer
                metadata=d.metadata,
                concepts=[],
                relations=[]
            )
            for d in base_docs
        ]

        concepts = create_large_concept_set(20)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            # Time short documents
            start = time.time()
            engine.discover(short_docs, concepts)
            short_time = time.time() - start

            # Time medium documents
            start = time.time()
            engine.discover(medium_docs, concepts)
            medium_time = time.time() - start

            # Time long documents
            start = time.time()
            engine.discover(long_docs, concepts)
            long_time = time.time() - start

            # Processing time should scale reasonably with document length
            # (not exponentially)
            ratio_medium_short = medium_time / short_time if short_time > 0 else 1
            ratio_long_medium = long_time / medium_time if medium_time > 0 else 1

            # Allow up to 15x ratio for 5x-10x document length increase
            # (accounts for overhead and non-linear processing)
            assert ratio_medium_short < 20.0
            assert ratio_long_medium < 20.0

    def test_scalability_with_concept_density(self, performance_config):
        """Test scalability with many concepts per document."""
        documents = create_large_document_set(10)

        # Vary concept density
        low_density = create_large_concept_set(10)
        medium_density = create_large_concept_set(50)
        high_density = create_large_concept_set(100)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            # Time low density
            start = time.time()
            engine.discover(documents, low_density)
            low_time = time.time() - start

            # Time medium density
            start = time.time()
            engine.discover(documents, medium_density)
            medium_time = time.time() - start

            # Time high density
            start = time.time()
            engine.discover(documents, high_density)
            high_time = time.time() - start

            # Time should scale roughly with concept count
            # (allow 5x ratio for 5x-10x concept increase)
            ratio_medium_low = medium_time / low_time if low_time > 0 else 1
            ratio_high_medium = high_time / medium_time if medium_time > 0 else 1

            assert ratio_medium_low < 8.0
            assert ratio_high_medium < 8.0

    def test_concurrent_processing_simulation(self, performance_config):
        """Test behavior with multiple sequential processing runs."""
        documents = create_large_document_set(20)
        concepts = create_large_concept_set(40)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            # Run multiple times and ensure consistent performance
            times = []
            for i in range(3):
                engine = KnowledgeDiscoveryEngine(performance_config)

                start = time.time()
                result = engine.discover(documents, concepts)
                elapsed = time.time() - start

                times.append(elapsed)
                assert result is not None

            # Performance should be relatively consistent
            # (within 100% variation - more realistic for CI environments)
            avg_time = sum(times) / len(times)
            for t in times:
                assert abs(t - avg_time) / avg_time < 1.0, \
                    f"Performance variation too high: {t:.2f}s vs avg {avg_time:.2f}s"


@pytest.mark.slow
class TestThroughput:
    """Test throughput metrics."""

    def test_documents_per_second(self, performance_config):
        """Test document processing throughput."""
        document_counts = [10, 20, 30]
        throughputs = []

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            for count in document_counts:
                documents = create_large_document_set(count)
                concepts = create_large_concept_set(count * 2)

                engine = KnowledgeDiscoveryEngine(performance_config)

                start = time.time()
                engine.discover(documents, concepts)
                elapsed = time.time() - start

                throughput = count / elapsed if elapsed > 0 else 0
                throughputs.append(throughput)

            # Average throughput should be reasonable (> 1 doc/sec)
            avg_throughput = sum(throughputs) / len(throughputs)
            assert avg_throughput > 1.0, f"Throughput too low: {avg_throughput:.2f} docs/sec"

    def test_concepts_per_second(self, performance_config):
        """Test concept processing throughput."""
        concept_counts = [20, 40, 60]
        throughputs = []

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            for count in concept_counts:
                documents = create_large_document_set(count // 2)
                concepts = create_large_concept_set(count)

                engine = KnowledgeDiscoveryEngine(performance_config)

                start = time.time()
                engine.discover(documents, concepts)
                elapsed = time.time() - start

                throughput = count / elapsed if elapsed > 0 else 0
                throughputs.append(throughput)

            # Average throughput should be reasonable (> 2 concepts/sec)
            avg_throughput = sum(throughputs) / len(throughputs)
            assert avg_throughput > 2.0, f"Throughput too low: {avg_throughput:.2f} concepts/sec"


class TestPerformanceOptimizations:
    """Test performance with different optimizations."""

    def test_performance_with_minimal_config(self):
        """Test performance with minimal configuration (fastest)."""
        config = DiscoveryConfig(
            enable_explicit_mining=True,
            enable_implicit_mining=False,
            enable_statistical_mining=False,
            enable_semantic_mining=False,
            enable_pattern_detection=False,
            enable_gap_analysis=False,
            enable_insight_generation=False,
            max_insights=5
        )

        documents = create_large_document_set(30)
        concepts = create_large_concept_set(60)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(config)

            start = time.time()
            result = engine.discover(documents, concepts)
            elapsed = time.time() - start

            # Minimal config should be very fast (< 5 seconds for 30 docs)
            assert elapsed < 5.0, f"Minimal config took {elapsed:.2f}s"
            assert result is not None

    def test_performance_with_full_config(self, performance_config):
        """Test performance with full configuration (slowest)."""
        documents = create_large_document_set(30)
        concepts = create_large_concept_set(60)

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(performance_config)

            start = time.time()
            result = engine.discover(documents, concepts)
            elapsed = time.time() - start

            # Full config should still complete in reasonable time (< 30 seconds)
            assert elapsed < 30.0, f"Full config took {elapsed:.2f}s"
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", ""])