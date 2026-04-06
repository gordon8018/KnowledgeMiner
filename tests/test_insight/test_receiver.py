"""
Tests for InsightReceiver and PriorityScorer.
"""

import pytest
from datetime import datetime
from src.discovery.models.insight import Insight, InsightType
from src.discovery.models.pattern import Evidence
from src.wiki.insight.scorer import PriorityScorer, PriorityLevel
from src.wiki.insight.receiver import InsightReceiver


@pytest.fixture
def sample_insights():
    """Create sample insights for testing."""
    insights = []

    # High priority insight (breakthrough, critical, immediate)
    insight1 = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Breakthrough Pattern",
        description="A breakthrough pattern discovery",
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
    insights.append(insight1)

    # Medium priority insight (significant, high, short_term)
    insight2 = Insight(
        id="insight-2",
        insight_type=InsightType.RELATION,
        title="Significant Relation",
        description="A significant relation discovery",
        significance=0.65,
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
    insights.append(insight2)

    # Low priority insight (incremental, low, long_term)
    insight3 = Insight(
        id="insight-3",
        insight_type=InsightType.GAP,
        title="Incremental Gap",
        description="An incremental gap discovery",
        significance=0.35,
        related_concepts=["concept5"],
        related_patterns=[],
        related_gaps=["gap-1"],
        evidence=[
            Evidence(
                source_id="doc-3",
                content="Limited evidence",
                confidence=0.4
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
    insights.append(insight3)

    return insights


def test_receive_insights(sample_insights):
    """Test InsightReceiver.receive() method."""
    receiver = InsightReceiver()

    # Receive insights
    received = receiver.receive(sample_insights)

    # Should receive all insights
    assert len(received) == len(sample_insights)

    # Check that insights are stored with metadata
    for insight, original in zip(received, sample_insights):
        assert insight.id == original.id
        assert insight.title == original.title
        # Should have scoring metadata
        assert "priority_score" in insight.metadata
        assert "priority_level" in insight.metadata
        assert "received_at" in insight.metadata
        assert "backfilled" in insight.metadata


def test_prioritize_insights(sample_insights):
    """Test InsightReceiver.prioritize() method."""
    receiver = InsightReceiver()

    # Receive insights
    receiver.receive(sample_insights)

    # Get prioritized insights
    prioritized = receiver.prioritize()

    # Should return all insights sorted by priority_score descending
    assert len(prioritized) == len(sample_insights)

    # Check sorting (highest priority first)
    if len(prioritized) >= 2:
        assert prioritized[0].metadata["priority_score"] >= prioritized[1].metadata["priority_score"]

    # Check that P0 insights come first
    p0_insights = [i for i in prioritized if i.metadata["priority_level"] == PriorityLevel.P0_IMMEDIATE]
    p1_insights = [i for i in prioritized if i.metadata["priority_level"] == PriorityLevel.P1_PRIORITY]

    # If we have P0 and P1 insights, P0 should come before P1
    if p0_insights and p1_insights:
        p0_index = prioritized.index(p0_insights[0])
        p1_index = prioritized.index(p1_insights[0])
        assert p0_index < p1_index


def test_enhanced_scoring_rubrics():
    """Test PriorityScorer with enhanced rubrics."""
    scorer = PriorityScorer()

    # Test breakthrough novelty (0.9-1.0)
    breakthrough_score = scorer._score_novelty("breakthrough")
    assert 0.9 <= breakthrough_score <= 1.0

    # Test critical impact (0.8-1.0)
    critical_score = scorer._score_impact("critical")
    assert 0.8 <= critical_score <= 1.0

    # Test immediate actionability (0.8-1.0)
    immediate_score = scorer._score_actionability("immediate")
    assert 0.8 <= immediate_score <= 1.0

    # Test incremental novelty (0.3-0.5)
    incremental_score = scorer._score_novelty("incremental")
    assert 0.3 <= incremental_score <= 0.5

    # Test low impact (0.2-0.4)
    low_score = scorer._score_impact("low")
    assert 0.2 <= low_score <= 0.4

    # Test long_term actionability (0.2-0.4)
    long_term_score = scorer._score_actionability("long_term")
    assert 0.2 <= long_term_score <= 0.4


def test_priority_level_classification():
    """Test priority level classification based on scores."""
    scorer = PriorityScorer()

    # Test P0_IMMEDIATE (score >= 0.8)
    result_p0 = scorer.score(
        novelty_rating="breakthrough",
        impact_rating="critical",
        actionability_rating="immediate"
    )
    assert result_p0["priority_level"] == PriorityLevel.P0_IMMEDIATE
    assert result_p0["priority_score"] >= 0.8

    # Test P1_PRIORITY (0.6 <= score < 0.8)
    result_p1 = scorer.score(
        novelty_rating="significant",
        impact_rating="high",
        actionability_rating="short_term"
    )
    assert result_p1["priority_level"] == PriorityLevel.P1_PRIORITY
    assert 0.6 <= result_p1["priority_score"] < 0.8

    # Test P2_STANDARD (0.4 <= score < 0.6)
    result_p2 = scorer.score(
        novelty_rating="moderate",
        impact_rating="medium",
        actionability_rating="medium_term"
    )
    assert result_p2["priority_level"] == PriorityLevel.P2_STANDARD
    assert 0.4 <= result_p2["priority_score"] < 0.6

    # Test P3_DEFERRED (score < 0.4)
    result_p3 = scorer.score(
        novelty_rating="incremental",
        impact_rating="low",
        actionability_rating="long_term"
    )
    assert result_p3["priority_level"] == PriorityLevel.P3_DEFERRED
    assert result_p3["priority_score"] < 0.4


def test_queue_management():
    """Test queue management in InsightReceiver."""
    receiver = InsightReceiver()

    # Initially, pending_insights should be empty
    assert len(receiver.pending_insights) == 0

    # Receive insights
    insights = [
        Insight(
            id=f"insight-{i}",
            insight_type=InsightType.PATTERN,
            title=f"Insight {i}",
            description=f"Test insight {i}",
            significance=0.5 + (i * 0.1),
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )
        for i in range(3)
    ]

    received = receiver.receive(insights)

    # Check that insights are in pending_insights
    assert len(receiver.pending_insights) == len(insights)

    # Check that all received insights are in pending_insights
    received_ids = {i.id for i in received}
    pending_ids = {i.id for i in receiver.pending_insights}
    assert received_ids == pending_ids

    # Prioritize should return insights from pending_insights
    prioritized = receiver.prioritize()
    assert len(prioritized) == len(receiver.pending_insights)


def test_scoring_formula():
    """Test that the scoring formula is correct: novelty*0.25 + impact*0.40 + actionability*0.35"""
    scorer = PriorityScorer()

    # Test with specific values
    result = scorer.score(
        novelty_rating="breakthrough",  # ~0.95
        impact_rating="critical",       # ~0.9
        actionability_rating="immediate"  # ~0.9
    )

    novelty_score = scorer._score_novelty("breakthrough")
    impact_score = scorer._score_impact("critical")
    actionability_score = scorer._score_actionability("immediate")

    expected_score = (novelty_score * 0.25) + (impact_score * 0.40) + (actionability_score * 0.35)

    # Allow small floating point differences
    assert abs(result["priority_score"] - expected_score) < 0.01


def test_novelty_rubric_weights():
    """Test that all novelty rubrics have correct scores."""
    scorer = PriorityScorer()

    rubrics = {
        "breakthrough": (0.9, 1.0),
        "significant": (0.7, 0.9),
        "moderate": (0.5, 0.7),
        "incremental": (0.3, 0.5),
        "minimal": (0.0, 0.3)
    }

    for rubric, (min_score, max_score) in rubrics.items():
        score = scorer._score_novelty(rubric)
        assert min_score <= score <= max_score, f"Novelty rubric '{rubric}' score {score} not in range [{min_score}, {max_score}]"


def test_impact_rubric_weights():
    """Test that all impact rubrics have correct scores."""
    scorer = PriorityScorer()

    rubrics = {
        "critical": (0.8, 1.0),
        "high": (0.6, 0.8),
        "medium": (0.4, 0.6),
        "low": (0.2, 0.4),
        "minimal": (0.0, 0.2)
    }

    for rubric, (min_score, max_score) in rubrics.items():
        score = scorer._score_impact(rubric)
        assert min_score <= score <= max_score, f"Impact rubric '{rubric}' score {score} not in range [{min_score}, {max_score}]"


def test_actionability_rubric_weights():
    """Test that all actionability rubrics have correct scores."""
    scorer = PriorityScorer()

    rubrics = {
        "immediate": (0.8, 1.0),
        "short_term": (0.6, 0.8),
        "medium_term": (0.4, 0.6),
        "long_term": (0.2, 0.4),
        "unclear": (0.0, 0.2)
    }

    for rubric, (min_score, max_score) in rubrics.items():
        score = scorer._score_actionability(rubric)
        assert min_score <= score <= max_score, f"Actionability rubric '{rubric}' score {score} not in range [{min_score}, {max_score}]"


def test_backfilled_flag():
    """Test that insights are marked with backfilled flag."""
    receiver = InsightReceiver()

    insights = [
        Insight(
            id="insight-1",
            insight_type=InsightType.PATTERN,
            title="Test Insight",
            description="Test",
            significance=0.7,
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )
    ]

    received = receiver.receive(insights, backfilled=True)

    # Check backfilled flag
    assert all(i.metadata["backfilled"] for i in received)


def test_empty_receive():
    """Test receiving empty list of insights."""
    receiver = InsightReceiver()

    received = receiver.receive([])

    assert len(received) == 0
    assert len(receiver.pending_insights) == 0


def test_prioritize_with_empty_queue():
    """Test prioritize with empty queue."""
    receiver = InsightReceiver()

    prioritized = receiver.prioritize()

    assert len(prioritized) == 0
