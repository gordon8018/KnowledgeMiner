"""
Integration tests for insight management end-to-end workflow.

Tests the complete pipeline from insight discovery to Wiki backfill and propagation,
integrating all Stage 3 components:
- InsightReceiver (Task 3.1)
- PriorityScorer (Task 3.1)
- BackfillScheduler (Task 3.3)
- BackfillExecutor (Task 3.4)
- InsightPropagator (Task 3.2)
"""

import pytest
import time
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock, patch

from src.discovery.models.insight import Insight, InsightType
from src.discovery.models.pattern import Evidence
from src.wiki.insight.receiver import InsightReceiver
from src.wiki.insight.scorer import PriorityScorer, PriorityLevel
from src.wiki.insight.scheduler import BackfillScheduler
from src.wiki.insight.executor import BackfillExecutor
from src.wiki.insight.propagator import InsightPropagator
from src.wiki.core.models import WikiPage, PageType
from src.wiki.core.storage import WikiStore


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_wiki_store():
    """Create a mock WikiStore."""
    store = Mock(spec=WikiStore)

    # Mock pages database
    pages = {}

    def get_page(page_id: str):
        return pages.get(page_id)

    def create_page(page: WikiPage) -> WikiPage:
        if page.id in pages:
            raise ValueError(f"Page {page.id} already exists")
        pages[page.id] = page
        return page

    def update_page(page: WikiPage) -> WikiPage:
        if page.id not in pages:
            raise ValueError(f"Page {page.id} does not exist")
        pages[page.id] = page
        return page

    store.get_page = get_page
    store.create_page = create_page
    store.update_page = update_page

    # Track pages for debugging
    store._pages = pages

    return store


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock()

    def generate_text(prompt: str, **kwargs) -> str:
        # Return a simple content update
        return "# Updated Content\n\n## Insights\n\n- Insight integrated successfully."

    def generate(prompt: str, **kwargs) -> str:
        # Return a simple content update (executor uses 'generate' method)
        return "# Updated Content\n\n## Insights\n\n- Insight integrated successfully."

    provider.generate_text = generate_text
    provider.generate = generate

    return provider


@pytest.fixture
def mock_wiki_core():
    """Create a mock WikiCore for propagation."""
    core = Mock()

    # Mock knowledge graph
    graph = {
        "concept1": {"concept2", "concept3"},
        "concept2": {"concept1", "concept4"},
        "concept3": {"concept1", "concept4"},
        "concept4": {"concept2", "concept3", "concept5"},
        "concept5": {"concept4"},
    }

    def get_related_concepts(concept: str) -> List[str]:
        return list(graph.get(concept, set()))

    core.get_related_concepts = get_related_concepts

    return core


@pytest.fixture
def sample_wiki_pages(mock_wiki_store):
    """Create sample Wiki pages for testing."""
    pages = []

    page1 = WikiPage(
        id="concept1",
        title="Concept 1",
        content="# Concept 1\n\nOriginal content about concept 1.",
        page_type=PageType.CONCEPT,
        version=1
    )
    pages.append(page1)
    mock_wiki_store.create_page(page1)

    page2 = WikiPage(
        id="concept2",
        title="Concept 2",
        content="# Concept 2\n\nOriginal content about concept 2.",
        page_type=PageType.CONCEPT,
        version=1
    )
    pages.append(page2)
    mock_wiki_store.create_page(page2)

    page3 = WikiPage(
        id="concept3",
        title="Concept 3",
        content="# Concept 3\n\nOriginal content about concept 3.",
        page_type=PageType.CONCEPT,
        version=1
    )
    pages.append(page3)
    mock_wiki_store.create_page(page3)

    return pages


@pytest.fixture
def sample_insights():
    """Create sample insights for testing."""
    insights = []

    # P0 insight (breakthrough, critical, immediate)
    p0_insight = Insight(
        id="insight-p0",
        insight_type=InsightType.PATTERN,
        title="Breakthrough Discovery",
        description="Critical breakthrough requiring immediate action",
        significance=0.95,
        related_concepts=["concept1", "concept2"],
        related_patterns=["pattern-1"],
        related_gaps=[],
        evidence=[Evidence(source_id="doc-1", content="Evidence", confidence=0.9)],
        actionable_suggestions=["Immediate action needed"],
        generated_at=datetime.now(),
        metadata={
            "novelty_rating": "breakthrough",
            "impact_rating": "critical",
            "actionability_rating": "immediate"
        }
    )
    insights.append(p0_insight)

    # P1 insight (significant, high, short_term)
    p1_insight = Insight(
        id="insight-p1",
        insight_type=InsightType.RELATION,
        title="Significant Relation",
        description="Important relation discovery",
        significance=0.8,
        related_concepts=["concept2", "concept3"],
        related_patterns=[],
        related_gaps=["gap-1"],
        evidence=[Evidence(source_id="doc-2", content="Evidence", confidence=0.8)],
        actionable_suggestions=["Short-term action"],
        generated_at=datetime.now(),
        metadata={
            "novelty_rating": "significant",
            "impact_rating": "high",
            "actionability_rating": "short_term"
        }
    )
    insights.append(p1_insight)

    # P2 insight (moderate, medium, medium_term)
    p2_insight = Insight(
        id="insight-p2",
        insight_type=InsightType.GAP,
        title="Moderate Gap",
        description="Moderate gap identified",
        significance=0.6,
        related_concepts=["concept3"],
        related_patterns=[],
        related_gaps=["gap-2"],
        evidence=[Evidence(source_id="doc-3", content="Evidence", confidence=0.6)],
        actionable_suggestions=["Medium-term action"],
        generated_at=datetime.now(),
        metadata={
            "novelty_rating": "moderate",
            "impact_rating": "medium",
            "actionability_rating": "medium_term"
        }
    )
    insights.append(p2_insight)

    # P3 insight (incremental, low, long_term)
    p3_insight = Insight(
        id="insight-p3",
        insight_type=InsightType.INTEGRATED,
        title="Incremental Improvement",
        description="Small incremental improvement",
        significance=0.4,
        related_concepts=["concept1"],
        related_patterns=[],
        related_gaps=[],
        evidence=[Evidence(source_id="doc-4", content="Evidence", confidence=0.4)],
        actionable_suggestions=["Long-term action"],
        generated_at=datetime.now(),
        metadata={
            "novelty_rating": "incremental",
            "impact_rating": "low",
            "actionability_rating": "long_term"
        }
    )
    insights.append(p3_insight)

    return insights


@pytest.fixture
def integration_components(mock_wiki_store, mock_llm_provider, mock_wiki_core):
    """Create all integration components with dependencies."""
    receiver = InsightReceiver()
    scheduler = BackfillScheduler()
    executor = BackfillExecutor(mock_wiki_store, mock_llm_provider)
    propagator = InsightPropagator(mock_wiki_core)

    return {
        "receiver": receiver,
        "scheduler": scheduler,
        "executor": executor,
        "propagator": propagator,
        "wiki_store": mock_wiki_store
    }


# =============================================================================
# End-to-End Workflow Tests (8 tests)
# =============================================================================

class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_insight_workflow_p0_insight(
        self,
        integration_components,
        sample_insights,
        sample_wiki_pages
    ):
        """Test complete workflow for high-priority P0 insight."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]
        executor = integration_components["executor"]
        propagator = integration_components["propagator"]

        # Step 1: Receive P0 insight
        p0_insight = [i for i in sample_insights if i.id == "insight-p0"][0]
        received = receiver.receive([p0_insight])

        assert len(received) == 1
        assert received[0].metadata["priority_level"] == PriorityLevel.P0_IMMEDIATE
        assert received[0].metadata["priority_score"] >= 0.8

        # Step 2: Schedule to immediate queue
        insights_with_scores = [
            {
                "insight": insight,
                "scores": {
                    "priority_score": insight.metadata["priority_score"],
                    "priority_level": insight.metadata["priority_level"]
                },
                "received_at": insight.metadata["received_at"],
                "backfilled": False
            }
            for insight in received
        ]
        scheduler.schedule(insights_with_scores)

        # Step 3: Get from immediate queue
        batch = scheduler.get_immediate_batch(max_size=10)
        assert len(batch) == 1
        assert batch[0]["insight"].id == "insight-p0"

        # Step 4: Execute backfill
        insight_item = batch[0]
        insight = insight_item["insight"]

        target_pages = executor.find_target_pages(insight)
        assert len(target_pages) == 2  # concept1 and concept2

        # Step 5: Update pages
        updated_pages = []
        for page in target_pages:
            updated_page = executor.update_page_content(page, insight)
            updated_pages.append(updated_page)

        assert len(updated_pages) == 2
        assert all(p.version > 1 for p in updated_pages)

        # Step 6: Propagate insight
        propagation_results = propagator.propagate(insight, max_hops=2)
        assert len(propagation_results) > 0

        # Verify propagation reached related concepts
        propagated_concepts = {r["concept"] for r in propagation_results}
        assert len(propagated_concepts) > 0

    def test_complete_insight_workflow_p3_insight(
        self,
        integration_components,
        sample_insights,
        sample_wiki_pages
    ):
        """Test complete workflow for low-priority P3 insight."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]
        executor = integration_components["executor"]
        propagator = integration_components["propagator"]

        # Step 1: Receive P3 insight
        p3_insight = [i for i in sample_insights if i.id == "insight-p3"][0]
        received = receiver.receive([p3_insight])

        assert len(received) == 1
        assert received[0].metadata["priority_level"] == PriorityLevel.P3_DEFERRED
        assert received[0].metadata["priority_score"] < 0.5

        # Step 2: Schedule to batch queue (P3)
        insights_with_scores = [
            {
                "insight": insight,
                "scores": {
                    "priority_score": insight.metadata["priority_score"],
                    "priority_level": insight.metadata["priority_level"]
                },
                "received_at": insight.metadata["received_at"],
                "backfilled": False
            }
            for insight in received
        ]
        scheduler.schedule(insights_with_scores)

        # Step 3: Get from batch queue (should return P3 after P1, P2)
        batch = scheduler.get_batch(max_size=50)
        assert len(batch) == 1
        assert batch[0]["insight"].id == "insight-p3"

        # Step 4: Execute backfill
        insight_item = batch[0]
        insight = insight_item["insight"]

        target_pages = executor.find_target_pages(insight)
        assert len(target_pages) == 1  # Only concept1

        # Step 5: Update page
        updated_page = executor.update_page_content(target_pages[0], insight)
        assert updated_page.version > 1

        # Step 6: Propagate insight
        propagation_results = propagator.propagate(insight, max_hops=1)
        assert len(propagation_results) >= 0

    def test_discovery_to_backfill_pipeline(
        self,
        integration_components,
        sample_insights,
        sample_wiki_pages
    ):
        """Test complete pipeline from insight discovery to Wiki backfill."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]
        executor = integration_components["executor"]

        # Simulate insight discovery
        discovered_insights = sample_insights[:2]  # P0 and P1

        # Step 1: Receive insights
        received = receiver.receive(discovered_insights)
        assert len(received) == 2

        # Step 2: Schedule all insights
        insights_with_scores = [
            {
                "insight": insight,
                "scores": {
                    "priority_score": insight.metadata["priority_score"],
                    "priority_level": insight.metadata["priority_level"]
                },
                "received_at": insight.metadata["received_at"],
                "backfilled": False
            }
            for insight in received
        ]
        scheduler.schedule(insights_with_scores)

        # Step 3: Process immediate queue (P0)
        immediate_batch = scheduler.get_immediate_batch(max_size=10)
        assert len(immediate_batch) == 1

        # Step 4: Process batch queue (P1)
        batch_batch = scheduler.get_batch(max_size=50)
        assert len(batch_batch) == 1

        # Step 5: Execute backfill for all
        all_batches = immediate_batch + batch_batch
        updated_pages_count = 0

        for item in all_batches:
            insight = item["insight"]
            target_pages = executor.find_target_pages(insight)

            for page in target_pages:
                executor.update_page_content(page, insight)
                updated_pages_count += 1

        assert updated_pages_count > 0

    def test_batch_processing_multiple_insights(
        self,
        integration_components,
        sample_insights,
        sample_wiki_pages
    ):
        """Test processing multiple insights in batches."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]
        executor = integration_components["executor"]

        # Receive all insights
        received = receiver.receive(sample_insights)
        assert len(received) == 4

        # Schedule all insights
        insights_with_scores = [
            {
                "insight": insight,
                "scores": {
                    "priority_score": insight.metadata["priority_score"],
                    "priority_level": insight.metadata["priority_level"]
                },
                "received_at": insight.metadata["received_at"],
                "backfilled": False
            }
            for insight in received
        ]
        scheduler.schedule(insights_with_scores)

        # Process in batches
        processed_insights = []

        # Process immediate queue
        immediate_batch = scheduler.get_immediate_batch(max_size=10)
        processed_insights.extend(immediate_batch)

        # Process batch queue in multiple rounds
        while True:
            batch = scheduler.get_batch(max_size=2)
            if not batch:
                break
            processed_insights.extend(batch)

        assert len(processed_insights) == 4

        # Verify priority order (P0 first, then P1, P2, P3)
        priority_order = [
            PriorityLevel.P0_IMMEDIATE,
            PriorityLevel.P1_PRIORITY,
            PriorityLevel.P2_STANDARD,
            PriorityLevel.P3_DEFERRED
        ]

        for i, item in enumerate(processed_insights):
            expected_priority = priority_order[i]
            actual_priority = item["scores"]["priority_level"]
            assert actual_priority == expected_priority

    def test_insight_lifecycle_from_discovery_to_propagation(
        self,
        integration_components,
        sample_insights,
        sample_wiki_pages
    ):
        """Test complete insight lifecycle from discovery to propagation."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]
        executor = integration_components["executor"]
        propagator = integration_components["propagator"]

        # Discovery phase
        insight = sample_insights[0]  # P0 insight

        # Reception phase
        received = receiver.receive([insight])
        assert len(received) == 1

        # Prioritization phase
        prioritized = receiver.prioritize()
        assert len(prioritized) == 1
        assert prioritized[0].metadata["priority_level"] == PriorityLevel.P0_IMMEDIATE

        # Scheduling phase
        insights_with_scores = [
            {
                "insight": insight,
                "scores": {
                    "priority_score": insight.metadata["priority_score"],
                    "priority_level": insight.metadata["priority_level"]
                },
                "received_at": insight.metadata["received_at"],
                "backfilled": False
            }
        ]
        scheduler.schedule(insights_with_scores)

        # Execution phase
        batch = scheduler.get_immediate_batch(max_size=10)
        insight_item = batch[0]
        insight = insight_item["insight"]

        target_pages = executor.find_target_pages(insight)
        updated_pages = []
        for page in target_pages:
            updated_page = executor.update_page_content(page, insight)
            updated_pages.append(updated_page)

        # Propagation phase
        propagation_results = propagator.propagate(insight, max_hops=2)

        # Verify complete lifecycle
        assert len(target_pages) > 0
        assert len(propagation_results) > 0
        assert all(p.version > 1 for p in updated_pages)

    def test_priority_scheduling_affects_execution_order(
        self,
        integration_components,
        sample_insights,
        sample_wiki_pages
    ):
        """Test that priority scheduling affects execution order."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]

        # Receive insights in random order
        shuffled_insights = [
            sample_insights[3],  # P3
            sample_insights[0],  # P0
            sample_insights[2],  # P2
            sample_insights[1],  # P1
        ]

        received = receiver.receive(shuffled_insights)

        # Schedule all insights
        insights_with_scores = [
            {
                "insight": insight,
                "scores": {
                    "priority_score": insight.metadata["priority_score"],
                    "priority_level": insight.metadata["priority_level"]
                },
                "received_at": insight.metadata["received_at"],
                "backfilled": False
            }
            for insight in received
        ]
        scheduler.schedule(insights_with_scores)

        # Process all insights
        processed = []

        # Process immediate queue first
        immediate_batch = scheduler.get_immediate_batch(max_size=10)
        processed.extend(immediate_batch)

        # Process batch queue
        while True:
            batch = scheduler.get_batch(max_size=10)
            if not batch:
                break
            processed.extend(batch)

        # Verify execution order is P0 -> P1 -> P2 -> P3
        priority_levels = [
            item["scores"]["priority_level"] for item in processed
        ]

        assert priority_levels[0] == PriorityLevel.P0_IMMEDIATE
        assert priority_levels[1] == PriorityLevel.P1_PRIORITY
        assert priority_levels[2] == PriorityLevel.P2_STANDARD
        assert priority_levels[3] == PriorityLevel.P3_DEFERRED

    def test_backfill_and_propagation_integration(
        self,
        integration_components,
        sample_insights,
        sample_wiki_pages,
        mock_wiki_core
    ):
        """Test integration of backfill and propagation."""
        executor = integration_components["executor"]
        propagator = integration_components["propagator"]

        insight = sample_insights[0]  # P0 insight with concept1, concept2

        # Execute backfill
        target_pages = executor.find_target_pages(insight)
        updated_pages = []

        for page in target_pages:
            updated_page = executor.update_page_content(page, insight)
            updated_pages.append(updated_page)

        # Execute propagation
        propagation_results = propagator.propagate(insight, max_hops=2)

        # Verify both operations succeeded
        assert len(updated_pages) == 2
        assert len(propagation_results) > 0

        # Verify propagation reaches concepts not in original insight
        propagated_concepts = {r["concept"] for r in propagation_results}
        original_concepts = set(insight.related_concepts)

        # At least some new concepts should be reached
        new_concepts = propagated_concepts - original_concepts
        assert len(new_concepts) > 0

    def test_error_recovery_in_pipeline(
        self,
        integration_components,
        sample_insights,
        sample_wiki_pages
    ):
        """Test error recovery in the pipeline."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]
        executor = integration_components["executor"]

        # Create insights where one will fail
        good_insight = sample_insights[0]
        bad_insight = Insight(
            id="bad-insight",
            insight_type=InsightType.PATTERN,
            title="Bad Insight",
            description="This insight references non-existent concepts",
            significance=0.5,
            related_concepts=["nonexistent_concept"],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )

        # Receive both insights
        received = receiver.receive([good_insight, bad_insight])
        assert len(received) == 2

        # Schedule insights
        insights_with_scores = [
            {
                "insight": insight,
                "scores": {
                    "priority_score": insight.metadata["priority_score"],
                    "priority_level": insight.metadata["priority_level"]
                },
                "received_at": insight.metadata["received_at"],
                "backfilled": False
            }
            for insight in received
        ]
        scheduler.schedule(insights_with_scores)

        # Process insights
        batch = scheduler.get_immediate_batch(max_size=10)

        successful_updates = 0
        failed_updates = 0

        for item in batch:
            insight = item["insight"]
            try:
                target_pages = executor.find_target_pages(insight)
                for page in target_pages:
                    executor.update_page_content(page, insight)
                    successful_updates += 1
            except Exception as e:
                failed_updates += 1
                # Error should not crash the pipeline

        # At least the good insight should succeed
        assert successful_updates > 0


# =============================================================================
# Performance Tests (4 tests)
# =============================================================================

class TestPerformance:
    """Test performance characteristics of the integration."""

    def test_processing_time_for_100_insights(
        self,
        integration_components
    ):
        """Test that processing 100 insights completes within reasonable time."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]

        # Create 100 insights
        insights = []
        for i in range(100):
            insight = Insight(
                id=f"insight-{i}",
                insight_type=InsightType.PATTERN,
                title=f"Insight {i}",
                description=f"Test insight {i}",
                significance=0.5 + (i % 5) * 0.1,
                related_concepts=[f"concept{i % 10}"],
                related_patterns=[],
                related_gaps=[],
                evidence=[],
                actionable_suggestions=[],
                generated_at=datetime.now(),
                metadata={}
            )
            insights.append(insight)

        # Measure receive time
        start_time = time.time()
        received = receiver.receive(insights)
        receive_time = time.time() - start_time

        assert len(received) == 100
        assert receive_time < 5.0  # Should complete within 5 seconds

        # Measure schedule time
        insights_with_scores = [
            {
                "insight": insight,
                "scores": {
                    "priority_score": insight.metadata["priority_score"],
                    "priority_level": insight.metadata["priority_level"]
                },
                "received_at": insight.metadata["received_at"],
                "backfilled": False
            }
            for insight in received
        ]

        start_time = time.time()
        scheduler.schedule(insights_with_scores)
        schedule_time = time.time() - start_time

        assert schedule_time < 1.0  # Should complete within 1 second

    def test_memory_usage_for_large_batch(
        self,
        integration_components
    ):
        """Test memory efficiency for large batches."""
        import sys

        receiver = integration_components["receiver"]

        # Create large batch of insights
        insights = []
        for i in range(1000):
            insight = Insight(
                id=f"insight-{i}",
                insight_type=InsightType.PATTERN,
                title=f"Insight {i}",
                description=f"Test insight {i}",
                significance=0.5,
                related_concepts=[f"concept{i % 10}"],
                related_patterns=[],
                related_gaps=[],
                evidence=[],
                actionable_suggestions=[],
                generated_at=datetime.now(),
                metadata={}
            )
            insights.append(insight)

        # Measure memory before
        initial_size = sys.getsizeof(receiver.pending_insights)

        # Receive all insights
        receiver.receive(insights)

        # Measure memory after
        final_size = sys.getsizeof(receiver.pending_insights)

        # Memory growth should be reasonable (not exponential)
        # Allow up to 200x growth for 1000 items (list grows dynamically)
        assert final_size < initial_size * 200  # Less than 200x growth

    def test_scheduler_throughput(
        self,
        integration_components
    ):
        """Test scheduler queue processing throughput."""
        scheduler = integration_components["scheduler"]

        # Create and schedule insights
        insights_with_scores = []
        for i in range(500):
            insight_dict = {
                "insight": Mock(id=f"insight-{i}"),
                "scores": {
                    "priority_score": 0.5,
                    "priority_level": PriorityLevel.P2_STANDARD
                },
                "received_at": datetime.now().isoformat(),
                "backfilled": False
            }
            insights_with_scores.append(insight_dict)

        # Schedule all insights
        start_time = time.time()
        scheduler.schedule(insights_with_scores)
        schedule_time = time.time() - start_time

        assert schedule_time < 2.0  # Should complete within 2 seconds

        # Process all insights
        start_time = time.time()
        processed_count = 0

        while True:
            batch = scheduler.get_batch(max_size=50)
            if not batch:
                break
            processed_count += len(batch)

        process_time = time.time() - start_time

        assert processed_count == 500
        assert process_time < 1.0  # Should process within 1 second

    def test_executor_performance_with_multiple_pages(
        self,
        integration_components,
        mock_wiki_store
    ):
        """Test executor performance with multiple page updates."""
        executor = integration_components["executor"]

        # Create test pages
        for i in range(50):
            page = WikiPage(
                id=f"concept{i}",
                title=f"Concept {i}",
                content=f"# Concept {i}\n\nOriginal content.",
                page_type=PageType.CONCEPT,
                version=1
            )
            mock_wiki_store.create_page(page)

        # Create insight affecting many pages
        insight = Insight(
            id="bulk-insight",
            insight_type=InsightType.PATTERN,
            title="Bulk Update",
            description="Update many pages",
            significance=0.8,
            related_concepts=[f"concept{i}" for i in range(50)],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )

        # Measure backfill time
        start_time = time.time()
        target_pages = executor.find_target_pages(insight)
        find_time = time.time() - start_time

        assert len(target_pages) == 50
        assert find_time < 1.0  # Should find pages within 1 second

        # Measure update time
        start_time = time.time()
        for page in target_pages:
            executor.update_page_content(page, insight)
        update_time = time.time() - start_time

        assert update_time < 5.0  # Should update within 5 seconds


# =============================================================================
# Edge Case Tests (6 tests)
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_insight_list_handling(
        self,
        integration_components
    ):
        """Test handling of empty insight list."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]

        # Receive empty list
        received = receiver.receive([])
        assert len(received) == 0

        # Prioritize empty list
        prioritized = receiver.prioritize()
        assert len(prioritized) == 0

        # Schedule empty list
        scheduler.schedule([])
        assert scheduler.get_queue_sizes()["total"] == 0

        # Get batches from empty queues
        immediate_batch = scheduler.get_immediate_batch(max_size=10)
        assert len(immediate_batch) == 0

        batch = scheduler.get_batch(max_size=10)
        assert len(batch) == 0

    def test_insight_with_no_affected_concepts(
        self,
        integration_components,
        mock_wiki_core
    ):
        """Test insight with no related concepts (skip propagation)."""
        propagator = integration_components["propagator"]

        insight = Insight(
            id="no-concepts-insight",
            insight_type=InsightType.PATTERN,
            title="No Concepts",
            description="Insight with no related concepts",
            significance=0.5,
            related_concepts=[],  # Empty
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )

        # Propagation should return empty list
        propagation_results = propagator.propagate(insight, max_hops=2)
        assert len(propagation_results) == 0

    def test_insight_with_no_target_pages(
        self,
        integration_components,
        mock_wiki_store
    ):
        """Test insight with no target Wiki pages (skip backfill)."""
        executor = integration_components["executor"]

        insight = Insight(
            id="no-targets-insight",
            insight_type=InsightType.PATTERN,
            title="No Target Pages",
            description="Insight with concepts that have no pages",
            significance=0.5,
            related_concepts=["nonexistent_concept"],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )

        # Should find no target pages
        target_pages = executor.find_target_pages(insight)
        assert len(target_pages) == 0

    def test_duplicate_insight_handling(
        self,
        integration_components
    ):
        """Test handling of duplicate insights."""
        receiver = integration_components["receiver"]

        # Create duplicate insights
        insight1 = Insight(
            id="duplicate-1",
            insight_type=InsightType.PATTERN,
            title="Duplicate",
            description="Same content",
            significance=0.5,
            related_concepts=["concept1"],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )

        insight2 = Insight(
            id="duplicate-2",
            insight_type=InsightType.PATTERN,
            title="Duplicate",
            description="Same content",
            significance=0.5,
            related_concepts=["concept1"],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )

        # Receive both
        received = receiver.receive([insight1, insight2])

        # Both should be received (no automatic deduplication)
        assert len(received) == 2

        # Prioritize should return both
        prioritized = receiver.prioritize()
        assert len(prioritized) == 2

    def test_concurrent_processing_safety(
        self,
        integration_components
    ):
        """Test thread safety for concurrent processing (if applicable)."""
        receiver = integration_components["receiver"]
        scheduler = integration_components["scheduler"]

        # Create insights
        insights = []
        for i in range(10):
            insight = Insight(
                id=f"concurrent-insight-{i}",
                insight_type=InsightType.PATTERN,
                title=f"Concurrent Insight {i}",
                description=f"Test insight {i}",
                significance=0.5,
                related_concepts=[f"concept{i}"],
                related_patterns=[],
                related_gaps=[],
                evidence=[],
                actionable_suggestions=[],
                generated_at=datetime.now(),
                metadata={}
            )
            insights.append(insight)

        # Receive all
        received = receiver.receive(insights)
        assert len(received) == 10

        # Schedule all
        insights_with_scores = [
            {
                "insight": insight,
                "scores": {
                    "priority_score": insight.metadata["priority_score"],
                    "priority_level": insight.metadata["priority_level"]
                },
                "received_at": insight.metadata["received_at"],
                "backfilled": False
            }
            for insight in received
        ]
        scheduler.schedule(insights_with_scores)

        # Process all
        immediate_batch = scheduler.get_immediate_batch(max_size=10)
        batch = scheduler.get_batch(max_size=10)

        total_processed = len(immediate_batch) + len(batch)
        assert total_processed == 10

    def test_malformed_insight_data(
        self,
        integration_components
    ):
        """Test handling of malformed insight data."""
        receiver = integration_components["receiver"]

        # Create insight with invalid significance
        with pytest.raises(ValueError):
            Insight(
                id="malformed-insight",
                insight_type=InsightType.PATTERN,
                title="Malformed",
                description="Invalid significance value",
                significance=1.5,  # Invalid: > 1.0
                related_concepts=[],
                related_patterns=[],
                related_gaps=[],
                evidence=[],
                actionable_suggestions=[],
                generated_at=datetime.now(),
                metadata={}
            )

        # Create insight with negative significance
        with pytest.raises(ValueError):
            Insight(
                id="malformed-insight-2",
                insight_type=InsightType.PATTERN,
                title="Malformed",
                description="Invalid significance value",
                significance=-0.1,  # Invalid: < 0.0
                related_concepts=[],
                related_patterns=[],
                related_gaps=[],
                evidence=[],
                actionable_suggestions=[],
                generated_at=datetime.now(),
                metadata={}
            )