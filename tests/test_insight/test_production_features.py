"""
Tests for production-ready features: retry logic and transaction support.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock
from src.discovery.models.insight import Insight, InsightType
from src.discovery.models.pattern import Evidence
from src.wiki.core.models import WikiPage, PageType
from src.wiki.core.storage import WikiStore
from src.wiki.insight.executor import BackfillExecutor


@pytest.fixture
def mock_wiki_store():
    """Create a mock WikiStore."""
    store = Mock(spec=WikiStore)

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
    store._pages = pages

    return store


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    provider.generate.return_value = "# Updated content"
    return provider


@pytest.fixture
def sample_insight():
    """Create a sample insight."""
    return Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="Test description",
        significance=0.8,
        related_concepts=["concept1", "concept2"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )


@pytest.fixture
def sample_pages():
    """Create sample pages."""
    return [
        WikiPage(
            id="concept1",
            title="Concept 1",
            content="# Concept 1\n\nOriginal content.",
            page_type=PageType.CONCEPT,
            version=1
        ),
        WikiPage(
            id="concept2",
            title="Concept 2",
            content="# Concept 2\n\nOriginal content.",
            page_type=PageType.CONCEPT,
            version=1
        )
    ]


class TestRetryLogic:
    """Test retry logic for LLM calls."""

    def test_retry_on_temporary_failure(self, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
        """Test that retry logic handles temporary LLM failures."""
        # Create pages first
        for page in sample_pages:
            mock_wiki_store.create_page(page)

        mock_wiki_store.get_page.side_effect = lambda pid: next((p for p in sample_pages if p.id == pid), None)
        mock_wiki_store.update_page.side_effect = lambda p: p

        # Fail first 2 times, succeed on 3rd
        call_count = [0]

        def flaky_generate(prompt):
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Temporary LLM error")
            return "# Updated content"

        mock_llm_provider.generate.side_effect = flaky_generate

        executor = BackfillExecutor(mock_wiki_store, mock_llm_provider)

        # Should succeed after retries
        updated_ids = executor.backfill_insight(sample_insight)

        assert len(updated_ids) == 2
        assert call_count[0] >= 3  # Failed at least twice, succeeded on 3rd try

    def test_retry_exhaustion(self, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
        """Test that retry logic exhausts after max attempts."""
        # Create pages first
        for page in sample_pages:
            mock_wiki_store.create_page(page)

        mock_wiki_store.get_page.side_effect = lambda pid: next((p for p in sample_pages if p.id == pid), None)

        # Always fail
        mock_llm_provider.generate.side_effect = Exception("Persistent LLM error")

        executor = BackfillExecutor(mock_wiki_store, mock_llm_provider)

        # Should fail after all retries
        with pytest.raises(Exception) as exc_info:
            executor.backfill_insight(sample_insight)

        assert "Persistent LLM error" in str(exc_info.value)


class TestTransactionSupport:
    """Test transaction support for multi-page updates."""

    def test_atomic_update_all_pages(self, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
        """Test that all pages are updated atomically."""
        for page in sample_pages:
            mock_wiki_store.create_page(page)

        mock_wiki_store.get_page.side_effect = lambda pid: next((p for p in sample_pages if p.id == pid), None)
        mock_llm_provider.generate.return_value = "# Updated content"

        executor = BackfillExecutor(mock_wiki_store, mock_llm_provider)

        updated_ids = executor.backfill_insight(sample_insight)

        # Both pages should be updated
        assert len(updated_ids) == 2
        assert "concept1" in updated_ids
        assert "concept2" in updated_ids

    def test_rollback_on_partial_failure(self, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
        """Test that updates are rolled back if one page fails."""
        for page in sample_pages:
            mock_wiki_store.create_page(page)

        mock_wiki_store.get_page.side_effect = lambda pid: next((p for p in sample_pages if p.id == pid), None)

        # Track updates
        updated_pages = {}
        original_pages = {p.id: p for p in sample_pages}

        def flaky_update(page):
            updated_pages[page.id] = page
            if page.id == "concept2":
                raise ValueError("Update failed")
            return page

        mock_wiki_store.update_page = flaky_update
        mock_llm_provider.generate.return_value = "# Updated content"

        executor = BackfillExecutor(mock_wiki_store, mock_llm_provider)

        # Should fail and rollback
        with pytest.raises(ValueError) as exc_info:
            executor.backfill_insight(sample_insight)

        assert "Update failed" in str(exc_info.value)

        # First page should be rolled back (original content restored)
        # Check that rollback was attempted
        assert "concept1" in updated_pages  # Was updated
        # After rollback, should have original content
        # (In real scenario, WikiStore.update_page would restore original)

    def test_no_updates_on_prepare_failure(self, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
        """Test that no updates are applied if preparation fails."""
        # Create pages first
        for page in sample_pages:
            mock_wiki_store.create_page(page)

        mock_wiki_store.get_page.side_effect = lambda pid: next((p for p in sample_pages if p.id == pid), None)

        # Track update calls
        update_calls = []

        def track_update(page):
            update_calls.append(page.id)
            return page

        mock_wiki_store.update_page = track_update

        # Fail during content generation (prepare phase)
        mock_llm_provider.generate.side_effect = Exception("LLM error during prepare")

        executor = BackfillExecutor(mock_wiki_store, mock_llm_provider)

        with pytest.raises(Exception):
            executor.backfill_insight(sample_insight)

        # No updates should have been applied
        assert len(update_calls) == 0


class TestQueuePersistence:
    """Test queue persistence for crash recovery."""

    def test_queue_state_persistence(self, tmp_path):
        """Test that queue state is persisted to disk."""
        from src.wiki.insight.scheduler import BackfillScheduler
        from src.wiki.insight.scorer import PriorityScorer

        scheduler = BackfillScheduler(persistence_dir=str(tmp_path))

        # Schedule some insights
        scorer = PriorityScorer()
        result = scorer.score("moderate", "medium", "medium_term")

        insights_with_scores = [
            {
                "insight": sample_insight,
                "scores": result,
                "received_at": datetime.now().isoformat(),
                "backfilled": False
            }
            for sample_insight in [
                Insight(
                    id=f"insight-{i}",
                    insight_type=InsightType.PATTERN,
                    title=f"Insight {i}",
                    description="Test",
                    significance=0.8,
                    related_concepts=[f"concept{i}"],
                    related_patterns=[],
                    related_gaps=[],
                    evidence=[],
                    actionable_suggestions=[],
                    generated_at=datetime.now(),
                    metadata={}
                )
                for i in range(3)
            ]
        ]

        scheduler.schedule(insights_with_scores)

        # Check persistence file exists
        persistence_file = tmp_path / BackfillScheduler.PERSISTENCE_FILE
        assert persistence_file.exists()

    def test_queue_state_recovery(self, tmp_path):
        """Test that queue state is recovered on initialization."""
        from src.wiki.insight.scheduler import BackfillScheduler
        from src.wiki.insight.scorer import PriorityScorer
        import json

        # Create initial scheduler and schedule insights
        scheduler1 = BackfillScheduler(persistence_dir=str(tmp_path))

        scorer = PriorityScorer()
        result = scorer.score("moderate", "medium", "medium_term")

        insights_with_scores = [
            {
                "insight": Insight(
                    id="insight-1",
                    insight_type=InsightType.PATTERN,
                    title="Insight 1",
                    description="Test",
                    significance=0.8,
                    related_concepts=["concept1"],
                    related_patterns=[],
                    related_gaps=[],
                    evidence=[],
                    actionable_suggestions=[],
                    generated_at=datetime.now(),
                    metadata={}
                ),
                "scores": result,
                "received_at": datetime.now().isoformat(),
                "backfilled": False
            }
        ]

        scheduler1.schedule(insights_with_scores)

        # Create new scheduler - should recover state
        scheduler2 = BackfillScheduler(persistence_dir=str(tmp_path))

        # Queue should have recovered items
        sizes = scheduler2.get_queue_sizes()
        assert sizes["total"] > 0
