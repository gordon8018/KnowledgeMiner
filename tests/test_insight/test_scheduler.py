"""
Tests for BackfillScheduler.
"""

import pytest
from datetime import datetime
from src.discovery.models.insight import Insight, InsightType
from src.discovery.models.pattern import Evidence
from src.wiki.insight.scorer import PriorityScorer, PriorityLevel
from src.wiki.insight.scheduler import BackfillScheduler


@pytest.fixture
def sample_insights():
    """Create sample insights for testing."""
    insights = []

    # P0_IMMEDIATE insight (score >= 0.8)
    p0_insight = Insight(
        id="insight-p0",
        insight_type=InsightType.PATTERN,
        title="P0 Immediate Insight",
        description="A P0 priority insight",
        significance=0.95,
        related_concepts=["concept1", "concept2"],
        related_patterns=["pattern-1"],
        related_gaps=[],
        evidence=[
            Evidence(
                source_id="doc-1",
                content="Strong evidence",
                confidence=0.95
            )
        ],
        actionable_suggestions=["Immediate action required"],
        generated_at=datetime.now(),
        metadata={
            "novelty_rating": "breakthrough",
            "impact_rating": "critical",
            "actionability_rating": "immediate"
        }
    )
    insights.append(p0_insight)

    # P1_PRIORITY insight (0.6 <= score < 0.8)
    p1_insight = Insight(
        id="insight-p1",
        insight_type=InsightType.RELATION,
        title="P1 Priority Insight",
        description="A P1 priority insight",
        significance=0.7,
        related_concepts=["concept3", "concept4"],
        related_patterns=[],
        related_gaps=[],
        evidence=[
            Evidence(
                source_id="doc-2",
                content="Good evidence",
                confidence=0.7
            )
        ],
        actionable_suggestions=["Short-term action recommended"],
        generated_at=datetime.now(),
        metadata={
            "novelty_rating": "significant",
            "impact_rating": "high",
            "actionability_rating": "short_term"
        }
    )
    insights.append(p1_insight)

    # P2_STANDARD insight (0.4 <= score < 0.6)
    p2_insight = Insight(
        id="insight-p2",
        insight_type=InsightType.GAP,
        title="P2 Standard Insight",
        description="A P2 priority insight",
        significance=0.5,
        related_concepts=["concept5"],
        related_patterns=[],
        related_gaps=["gap-1"],
        evidence=[
            Evidence(
                source_id="doc-3",
                content="Moderate evidence",
                confidence=0.5
            )
        ],
        actionable_suggestions=["Medium-term consideration"],
        generated_at=datetime.now(),
        metadata={
            "novelty_rating": "moderate",
            "impact_rating": "medium",
            "actionability_rating": "medium_term"
        }
    )
    insights.append(p2_insight)

    # P3_DEFERRED insight (score < 0.4)
    p3_insight = Insight(
        id="insight-p3",
        insight_type=InsightType.INTEGRATED,
        title="P3 Deferred Insight",
        description="A P3 priority insight",
        significance=0.3,
        related_concepts=["concept6"],
        related_patterns=[],
        related_gaps=[],
        evidence=[
            Evidence(
                source_id="doc-4",
                content="Limited evidence",
                confidence=0.3
            )
        ],
        actionable_suggestions=["Long-term consideration"],
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
def scored_insights(sample_insights):
    """Create scored insights for testing."""
    scorer = PriorityScorer()
    scored = []

    for insight in sample_insights:
        # Score the insight
        scoring_result = scorer.score(
            novelty_rating=insight.metadata["novelty_rating"],
            impact_rating=insight.metadata["impact_rating"],
            actionability_rating=insight.metadata["actionability_rating"]
        )

        # Create scored insight entry
        scored.append({
            "insight": insight,
            "scores": scoring_result,
            "received_at": datetime.now().isoformat(),
            "backfilled": False
        })

    return scored


def test_schedule_p0_to_immediate_queue(scored_insights):
    """Test that P0 insights are scheduled to immediate queue."""
    scheduler = BackfillScheduler()

    # Schedule all insights
    scheduler.schedule(scored_insights)

    # Get queue sizes
    queue_sizes = scheduler.get_queue_sizes()

    # P0 should be in immediate queue
    assert queue_sizes["immediate_queue"] == 1
    assert queue_sizes["batch_queue_p1"] == 1
    assert queue_sizes["batch_queue_p2"] == 1
    assert queue_sizes["batch_queue_p3"] == 1


def test_schedule_p1_p2_p3_to_batch_queue(scored_insights):
    """Test that P1, P2, P3 insights are scheduled to batch queue."""
    scheduler = BackfillScheduler()

    # Filter only P1, P2, P3 insights
    non_p0_insights = [
        item for item in scored_insights
        if item["scores"]["priority_level"] != PriorityLevel.P0_IMMEDIATE
    ]

    scheduler.schedule(non_p0_insights)

    # Get queue sizes
    queue_sizes = scheduler.get_queue_sizes()

    # P1, P2, P3 should be in batch queues, not immediate
    assert queue_sizes["immediate_queue"] == 0
    assert queue_sizes["batch_queue_p1"] == 1
    assert queue_sizes["batch_queue_p2"] == 1
    assert queue_sizes["batch_queue_p3"] == 1


def test_get_immediate_batch_returns_p0_only(scored_insights):
    """Test that get_immediate_batch returns only P0 insights."""
    scheduler = BackfillScheduler()
    scheduler.schedule(scored_insights)

    # Get immediate batch
    batch = scheduler.get_immediate_batch(max_size=10)

    # Should return only P0 insight
    assert len(batch) == 1
    assert batch[0]["scores"]["priority_level"] == PriorityLevel.P0_IMMEDIATE


def test_get_batch_prioritizes_p1_over_p2_over_p3(scored_insights):
    """Test that get_batch prioritizes P1 > P2 > P3."""
    scheduler = BackfillScheduler()

    # Filter only P1, P2, P3 insights
    non_p0_insights = [
        item for item in scored_insights
        if item["scores"]["priority_level"] != PriorityLevel.P0_IMMEDIATE
    ]

    scheduler.schedule(non_p0_insights)

    # Get batch with max_size=2 (should get P1 first, then P2)
    batch = scheduler.get_batch(max_size=2)

    # Should return P1 first, then P2
    assert len(batch) == 2
    assert batch[0]["scores"]["priority_level"] == PriorityLevel.P1_PRIORITY
    assert batch[1]["scores"]["priority_level"] == PriorityLevel.P2_STANDARD


def test_get_batch_respects_max_size(scored_insights):
    """Test that get_batch respects max_size parameter."""
    scheduler = BackfillScheduler()

    # Filter only P1, P2, P3 insights
    non_p0_insights = [
        item for item in scored_insights
        if item["scores"]["priority_level"] != PriorityLevel.P0_IMMEDIATE
    ]

    scheduler.schedule(non_p0_insights)

    # Request batch smaller than available
    batch = scheduler.get_batch(max_size=1)

    # Should return only 1 insight
    assert len(batch) == 1


def test_get_immediate_batch_respects_max_size(scored_insights):
    """Test that get_immediate_batch respects max_size parameter."""
    scheduler = BackfillScheduler()

    # Create multiple P0 insights
    p0_insights = [item for item in scored_insights if item["scores"]["priority_level"] == PriorityLevel.P0_IMMEDIATE]

    # Duplicate to create 3 P0 insights
    p0_insights_extended = p0_insights * 3

    scheduler.schedule(p0_insights_extended)

    # Request batch smaller than available
    batch = scheduler.get_immediate_batch(max_size=2)

    # Should return only 2 insights
    assert len(batch) == 2


def test_queue_empty_after_clear(scored_insights):
    """Test that queues are empty after clear_all."""
    scheduler = BackfillScheduler()
    scheduler.schedule(scored_insights)

    # Clear all queues
    scheduler.clear_all()

    # Check queues are empty
    queue_sizes = scheduler.get_queue_sizes()
    assert queue_sizes["immediate_queue"] == 0
    assert queue_sizes["batch_queue_p1"] == 0
    assert queue_sizes["batch_queue_p2"] == 0
    assert queue_sizes["batch_queue_p3"] == 0


def test_get_queue_sizes_returns_correct_counts(scored_insights):
    """Test that get_queue_sizes returns correct counts."""
    scheduler = BackfillScheduler()
    scheduler.schedule(scored_insights)

    # Get queue sizes
    queue_sizes = scheduler.get_queue_sizes()

    # Verify counts
    assert queue_sizes["immediate_queue"] == 1
    assert queue_sizes["batch_queue_p1"] == 1
    assert queue_sizes["batch_queue_p2"] == 1
    assert queue_sizes["batch_queue_p3"] == 1
    assert queue_sizes["total"] == 4


def test_scheduled_insights_preserve_metadata(scored_insights):
    """Test that scheduled insights preserve their metadata."""
    scheduler = BackfillScheduler()
    scheduler.schedule(scored_insights)

    # Get batch
    batch = scheduler.get_batch(max_size=10)

    # Check metadata is preserved
    for item in batch:
        assert "insight" in item
        assert "scores" in item
        assert "received_at" in item
        assert "backfilled" in item
        assert "priority_score" in item["scores"]
        assert "priority_level" in item["scores"]


def test_multiple_schedule_calls_accumulate(scored_insights):
    """Test that multiple schedule calls accumulate insights."""
    scheduler = BackfillScheduler()

    # Schedule insights twice
    scheduler.schedule(scored_insights)
    scheduler.schedule(scored_insights)

    # Get queue sizes
    queue_sizes = scheduler.get_queue_sizes()

    # Should have double the insights
    assert queue_sizes["immediate_queue"] == 2  # 1 P0 * 2
    assert queue_sizes["batch_queue_p1"] == 2   # 1 P1 * 2
    assert queue_sizes["batch_queue_p2"] == 2   # 1 P2 * 2
    assert queue_sizes["batch_queue_p3"] == 2   # 1 P3 * 2
    assert queue_sizes["total"] == 8            # 4 total * 2


def test_empty_queues_return_empty_lists():
    """Test that empty queues return empty lists."""
    scheduler = BackfillScheduler()

    # Get batches from empty queues
    immediate_batch = scheduler.get_immediate_batch()
    batch = scheduler.get_batch()

    # Should return empty lists
    assert len(immediate_batch) == 0
    assert len(batch) == 0


def test_batch_processing_maintains_priority_order(scored_insights):
    """Test that batch processing maintains priority order (P1 > P2 > P3)."""
    scheduler = BackfillScheduler()

    # Filter only P1, P2, P3 insights
    non_p0_insights = [
        item for item in scored_insights
        if item["scores"]["priority_level"] != PriorityLevel.P0_IMMEDIATE
    ]

    scheduler.schedule(non_p0_insights)

    # Get all insights from batch queue
    batch = scheduler.get_batch(max_size=10)

    # Verify priority order: P1, then P2, then P3
    priority_levels = [item["scores"]["priority_level"] for item in batch]

    # P1 should come before P2
    p1_index = priority_levels.index(PriorityLevel.P1_PRIORITY)
    p2_index = priority_levels.index(PriorityLevel.P2_STANDARD)
    p3_index = priority_levels.index(PriorityLevel.P3_DEFERRED)

    assert p1_index < p2_index < p3_index


def test_immediate_queue_fifo_ordering():
    """Test that immediate queue maintains FIFO ordering."""
    scheduler = BackfillScheduler()

    # Create multiple P0 insights with different IDs
    p0_insights = []
    for i in range(3):
        insight = Insight(
            id=f"insight-p0-{i}",
            insight_type=InsightType.PATTERN,
            title=f"P0 Insight {i}",
            description=f"P0 insight {i}",
            significance=0.9,
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={
                "novelty_rating": "breakthrough",
                "impact_rating": "critical",
                "actionability_rating": "immediate"
            }
        )

        scorer = PriorityScorer()
        scoring_result = scorer.score(
            novelty_rating="breakthrough",
            impact_rating="critical",
            actionability_rating="immediate"
        )

        p0_insights.append({
            "insight": insight,
            "scores": scoring_result,
            "received_at": datetime.now().isoformat(),
            "backfilled": False
        })

    scheduler.schedule(p0_insights)

    # Get all immediate insights
    batch = scheduler.get_immediate_batch(max_size=10)

    # Verify FIFO order (first scheduled, first out)
    assert len(batch) == 3
    assert batch[0]["insight"].id == "insight-p0-0"
    assert batch[1]["insight"].id == "insight-p0-1"
    assert batch[2]["insight"].id == "insight-p0-2"


def test_statistics_tracking():
    """Test that scheduler tracks statistics correctly."""
    scheduler = BackfillScheduler()

    # Initially, all queues should be empty
    initial_stats = scheduler.get_queue_sizes()
    assert initial_stats["total"] == 0

    # Schedule some insights
    scorer = PriorityScorer()
    insights = []

    # Create 2 P0 insights
    for i in range(2):
        insight = Insight(
            id=f"insight-p0-{i}",
            insight_type=InsightType.PATTERN,
            title=f"P0 Insight {i}",
            description=f"P0 insight {i}",
            significance=0.9,
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={
                "novelty_rating": "breakthrough",
                "impact_rating": "critical",
                "actionability_rating": "immediate"
            }
        )

        scoring_result = scorer.score(
            novelty_rating="breakthrough",
            impact_rating="critical",
            actionability_rating="immediate"
        )

        insights.append({
            "insight": insight,
            "scores": scoring_result,
            "received_at": datetime.now().isoformat(),
            "backfilled": False
        })

    scheduler.schedule(insights)

    # Check statistics after scheduling
    stats_after_schedule = scheduler.get_queue_sizes()
    assert stats_after_schedule["immediate_queue"] == 2
    assert stats_after_schedule["total"] == 2

    # Get a batch
    batch = scheduler.get_immediate_batch(max_size=1)

    # Check statistics after getting batch
    stats_after_batch = scheduler.get_queue_sizes()
    assert stats_after_batch["immediate_queue"] == 1  # 2 - 1 = 1
    assert stats_after_batch["total"] == 1


def test_clear_all_removes_all_insights(scored_insights):
    """Test that clear_all removes all insights from all queues."""
    scheduler = BackfillScheduler()
    scheduler.schedule(scored_insights)

    # Verify insights are scheduled
    stats_before = scheduler.get_queue_sizes()
    assert stats_before["total"] == 4

    # Clear all
    scheduler.clear_all()

    # Verify all queues are empty
    stats_after = scheduler.get_queue_sizes()
    assert stats_after["total"] == 0
    assert stats_after["immediate_queue"] == 0
    assert stats_after["batch_queue_p1"] == 0
    assert stats_after["batch_queue_p2"] == 0
    assert stats_after["batch_queue_p3"] == 0


def test_schedule_empty_list():
    """Test scheduling an empty list of insights."""
    scheduler = BackfillScheduler()

    # Schedule empty list
    scheduler.schedule([])

    # Verify queues remain empty
    stats = scheduler.get_queue_sizes()
    assert stats["total"] == 0


def test_get_batch_with_empty_queue():
    """Test get_batch when batch queue is empty."""
    scheduler = BackfillScheduler()

    # Only schedule P0 insights (batch queue remains empty)
    scorer = PriorityScorer()
    insights = []

    for i in range(2):
        insight = Insight(
            id=f"insight-p0-{i}",
            insight_type=InsightType.PATTERN,
            title=f"P0 Insight {i}",
            description=f"P0 insight {i}",
            significance=0.9,
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={
                "novelty_rating": "breakthrough",
                "impact_rating": "critical",
                "actionability_rating": "immediate"
            }
        )

        scoring_result = scorer.score(
            novelty_rating="breakthrough",
            impact_rating="critical",
            actionability_rating="immediate"
        )

        insights.append({
            "insight": insight,
            "scores": scoring_result,
            "received_at": datetime.now().isoformat(),
            "backfilled": False
        })

    scheduler.schedule(insights)

    # Get batch from empty batch queue
    batch = scheduler.get_batch(max_size=10)

    # Should return empty list
    assert len(batch) == 0


def test_get_immediate_batch_with_empty_queue():
    """Test get_immediate_batch when immediate queue is empty."""
    scheduler = BackfillScheduler()

    # Only schedule P1 insights (immediate queue remains empty)
    scorer = PriorityScorer()
    insights = []

    for i in range(2):
        insight = Insight(
            id=f"insight-p1-{i}",
            insight_type=InsightType.PATTERN,
            title=f"P1 Insight {i}",
            description=f"P1 insight {i}",
            significance=0.7,
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={
                "novelty_rating": "significant",
                "impact_rating": "high",
                "actionability_rating": "short_term"
            }
        )

        scoring_result = scorer.score(
            novelty_rating="significant",
            impact_rating="high",
            actionability_rating="short_term"
        )

        insights.append({
            "insight": insight,
            "scores": scoring_result,
            "received_at": datetime.now().isoformat(),
            "backfilled": False
        })

    scheduler.schedule(insights)

    # Get immediate batch from empty immediate queue
    batch = scheduler.get_immediate_batch(max_size=10)

    # Should return empty list
    assert len(batch) == 0
