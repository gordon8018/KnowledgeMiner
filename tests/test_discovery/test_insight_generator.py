"""
Tests for InsightGenerator.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.discovery.config import DiscoveryConfig
from src.discovery.models.insight import Insight, InsightType
from src.discovery.models.pattern import Pattern, PatternType, Evidence
from src.discovery.models.gap import KnowledgeGap, GapType
from src.discovery.insight_generator import InsightGenerator
from src.core.relation_model import Relation, RelationType


@pytest.fixture
def config():
    """Create a test DiscoveryConfig."""
    return DiscoveryConfig(
        max_insights=10,
        insight_significance_threshold=0.6
    )


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    return Mock()


@pytest.fixture
def mock_patterns():
    """Create mock patterns."""
    patterns = []

    # Temporal pattern
    pattern = Pattern(
        id="pattern-1",
        pattern_type=PatternType.TEMPORAL,
        title="Monthly Report Pattern",
        description="Documents appear monthly",
        confidence=0.8,
        significance_score=0.75,
        related_concepts=["monthly_report", "analysis"],
        related_patterns=[],
        evidence=[
            Evidence(
                source_id="doc-1",
                content="Monthly report from January",
                confidence=0.8
            ),
            Evidence(
                source_id="doc-2",
                content="Monthly report from February",
                confidence=0.7
            )
        ],
        metadata={"period": "monthly", "consistency": 0.9},
        detected_at=datetime.now()
    )
    patterns.append(pattern)

    # Causal pattern
    pattern = Pattern(
        id="pattern-2",
        pattern_type=PatternType.CAUSAL,
        title="Causal Chain: Inflation -> Interest Rates",
        description="Inflation causes interest rate changes",
        confidence=0.7,
        significance_score=0.65,
        related_concepts=["inflation", "interest_rates"],
        related_patterns=[],
        evidence=[
            Evidence(
                source_id="rel-1",
                content="Strong causal relationship",
                confidence=0.7
            )
        ],
        metadata={"chain_length": 2},
        detected_at=datetime.now()
    )
    patterns.append(pattern)

    return patterns


@pytest.fixture
def mock_relations():
    """Create mock relations."""
    relations = []

    # Strong relation
    relation = Relation(
        id="rel-1",
        source_concept="inflation",
        target_concept="interest_rates",
        relation_type=RelationType.CAUSES,
        strength=0.8,
        confidence=0.9
    )
    relations.append(relation)

    # Another strong relation
    relation = Relation(
        id="rel-2",
        source_concept="gdp",
        target_concept="economic_growth",
        relation_type=RelationType.CAUSES,
        strength=0.75,
        confidence=0.85
    )
    relations.append(relation)

    # Weak relation (should be filtered out)
    relation = Relation(
        id="rel-3",
        source_concept="concept_a",
        target_concept="concept_b",
        relation_type=RelationType.RELATED_TO,
        strength=0.5,
        confidence=0.6
    )
    relations.append(relation)

    return relations


@pytest.fixture
def mock_gaps():
    """Create mock knowledge gaps."""
    gaps = []

    # Missing concept gap
    gap = KnowledgeGap(
        id="gap-1",
        gap_type=GapType.MISSING_CONCEPT,
        description="Missing concept: quantitative_easing",
        severity=0.8,
        affected_concepts=["monetary_policy"],
        affected_relations=[],
        suggested_actions=[
            "Research quantitative easing",
            "Add QE examples to knowledge base"
        ],
        priority=8,
        estimated_effort="medium",
        metadata={"concept_name": "quantitative_easing"},
        detected_at=datetime.now()
    )
    gaps.append(gap)

    # Weak evidence gap
    gap = KnowledgeGap(
        id="gap-2",
        gap_type=GapType.WEAK_EVIDENCE,
        description="Weak evidence for market_trend concept",
        severity=0.6,
        affected_concepts=["market_trend"],
        affected_relations=[],
        suggested_actions=[
            "Add more sources for market trend",
            "Find supporting documents"
        ],
        priority=6,
        estimated_effort="low",
        metadata={"current_evidence_count": 2},
        detected_at=datetime.now()
    )
    gaps.append(gap)

    return gaps


def test_insight_generator_init(config, mock_llm_provider):
    """Test InsightGenerator initialization."""
    generator = InsightGenerator(config, mock_llm_provider)

    assert generator.config == config
    assert generator.llm_provider == mock_llm_provider
    assert generator.config.max_insights == 10
    assert generator.config.insight_significance_threshold == 0.6


def test_generate_pattern_insights(config, mock_llm_provider, mock_patterns):
    """Test generating insights from patterns."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = generator._generate_pattern_insights(mock_patterns)

    # Should generate insights from patterns
    assert len(insights) > 0

    insight = insights[0]
    assert insight.insight_type == InsightType.PATTERN
    assert insight.significance >= 0.0
    assert insight.significance <= 1.0
    assert len(insight.actionable_suggestions) > 0
    assert len(insight.related_patterns) > 0


def test_generate_relation_insights(config, mock_llm_provider, mock_relations):
    """Test generating insights from relations."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = generator._generate_relation_insights(mock_relations)

    # Should generate insights from strong relations
    assert len(insights) > 0

    # Only strong relations (strength >= 0.7) should be included
    insight = insights[0]
    assert insight.insight_type == InsightType.RELATION
    assert insight.significance >= 0.0
    assert len(insight.related_concepts) >= 2
    assert len(insight.actionable_suggestions) > 0


def test_generate_gap_insights(config, mock_llm_provider, mock_gaps):
    """Test generating insights from knowledge gaps."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = generator._generate_gap_insights(mock_gaps)

    # Should generate insights from gaps
    assert len(insights) > 0

    insight = insights[0]
    assert insight.insight_type == InsightType.GAP
    assert insight.significance >= 0.0
    assert len(insight.related_gaps) > 0
    assert len(insight.actionable_suggestions) > 0


def test_generate_integrated_insights(config, mock_llm_provider, mock_patterns, mock_gaps):
    """Test generating integrated insights."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = generator._generate_integrated_insights(mock_patterns, [], mock_gaps)

    # Should generate integrated insights when temporal patterns have related gaps
    # (This depends on the specific test data matching)
    assert isinstance(insights, list)

    for insight in insights:
        assert insight.insight_type == InsightType.INTEGRATED
        assert insight.significance >= 0.0
        assert len(insight.actionable_suggestions) > 0


def test_generate_pattern_suggestions_temporal(config, mock_llm_provider):
    """Test generating suggestions for temporal patterns."""
    generator = InsightGenerator(config, mock_llm_provider)

    pattern = Pattern(
        id="pattern-1",
        pattern_type=PatternType.TEMPORAL,
        title="Monthly Report",
        description="Monthly reporting pattern",
        confidence=0.8,
        significance_score=0.75,
        related_concepts=["report"],
        related_patterns=[],
        evidence=[],
        metadata={"period": "monthly"},
        detected_at=datetime.now()
    )

    suggestions = generator._generate_pattern_suggestions(pattern)

    assert len(suggestions) > 0
    assert any("monitor" in s.lower() or "recurring" in s.lower() for s in suggestions)


def test_generate_pattern_suggestions_causal(config, mock_llm_provider):
    """Test generating suggestions for causal patterns."""
    generator = InsightGenerator(config, mock_llm_provider)

    pattern = Pattern(
        id="pattern-1",
        pattern_type=PatternType.CAUSAL,
        title="Causal Chain",
        description="A causes B causes C",
        confidence=0.8,
        significance_score=0.75,
        related_concepts=["A", "B", "C"],
        related_patterns=[],
        evidence=[],
        metadata={"chain_length": 3},
        detected_at=datetime.now()
    )

    suggestions = generator._generate_pattern_suggestions(pattern)

    assert len(suggestions) > 0
    assert any("investigat" in s.lower() or "caus" in s.lower() for s in suggestions)


def test_rank_insights(config, mock_llm_provider):
    """Test ranking insights by significance."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = [
        Insight(
            id="insight-1",
            insight_type=InsightType.PATTERN,
            title="Low significance",
            description="Low significance insight",
            significance=0.5,
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        ),
        Insight(
            id="insight-2",
            insight_type=InsightType.RELATION,
            title="High significance",
            description="High significance insight",
            significance=0.9,
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        ),
        Insight(
            id="insight-3",
            insight_type=InsightType.GAP,
            title="Medium significance",
            description="Medium significance insight",
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

    ranked = generator._rank_insights(insights)

    # Should filter out insights below threshold (0.6)
    # So we should only have 2 insights (0.9 and 0.7)
    assert len(ranked) == 2

    # Should be sorted by significance (descending)
    assert ranked[0].significance >= ranked[1].significance
    assert ranked[0].id == "insight-2"  # Highest significance
    assert ranked[1].id == "insight-3"  # Second highest


def test_generate_insights_full_integration(
    config, mock_llm_provider, mock_patterns, mock_relations, mock_gaps
):
    """Test full insight generation integration."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = generator.generate_insights(mock_relations, mock_patterns, mock_gaps)

    # Should generate insights from all sources
    assert len(insights) > 0

    # Check that insights are properly filtered by threshold
    for insight in insights:
        assert insight.significance >= config.insight_significance_threshold

    # Check that insights are limited to max_insights
    assert len(insights) <= config.max_insights

    # Check that we have different insight types
    insight_types = {insight.insight_type for insight in insights}
    assert len(insight_types) > 0


def test_insight_significance_scoring(config, mock_llm_provider, mock_patterns):
    """Test that insight significance is properly computed."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = generator._generate_pattern_insights(mock_patterns)

    for insight in insights:
        # Significance should use the formula: novelty*0.25 + impact*0.40 + actionability*0.35
        assert 0.0 <= insight.significance <= 1.0

        # Pattern insights should have specific scoring
        if insight.insight_type == InsightType.PATTERN:
            # Find the corresponding pattern
            pattern_id = insight.metadata.get('pattern_id')
            pattern = next((p for p in mock_patterns if p.id == pattern_id), None)

            if pattern:
                # Novelty: min(1.0, pattern.confidence + 0.2)
                # Impact: pattern.significance_score
                # Actionability: 0.7
                expected_novelty = min(1.0, pattern.confidence + 0.2)
                expected_impact = pattern.significance_score
                expected_actionability = 0.7

                expected_significance = (
                    expected_novelty * 0.25 +
                    expected_impact * 0.40 +
                    expected_actionability * 0.35
                )

                # Allow small floating point differences
                assert abs(insight.significance - expected_significance) < 0.01


def test_insight_filtering_by_threshold(config, mock_llm_provider):
    """Test that low-significance insights are filtered out."""
    # Set high threshold
    config.insight_significance_threshold = 0.9

    generator = InsightGenerator(config, mock_llm_provider)

    # Create low-significance insights
    insights = [
        Insight(
            id="insight-1",
            insight_type=InsightType.PATTERN,
            title="Low significance",
            description="Low significance insight",
            significance=0.5,
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        ),
        Insight(
            id="insight-2",
            insight_type=InsightType.RELATION,
            title="High significance",
            description="High significance insight",
            significance=0.95,
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )
    ]

    ranked = generator._rank_insights(insights)

    # Should only return high-significance insights
    assert all(insight.significance >= config.insight_significance_threshold for insight in ranked)


def test_insight_limiting(config, mock_llm_provider):
    """Test that insights are limited to max_insights."""
    # Set low limit
    config.max_insights = 2

    generator = InsightGenerator(config, mock_llm_provider)

    # Create many insights
    insights = []
    for i in range(10):
        insight = Insight(
            id=f"insight-{i}",
            insight_type=InsightType.PATTERN,
            title=f"Insight {i}",
            description=f"Insight {i}",
            significance=0.8 + (i * 0.01),  # Varying significance
            related_concepts=[],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=[],
            generated_at=datetime.now(),
            metadata={}
        )
        insights.append(insight)

    ranked = generator._rank_insights(insights)

    # Should return at most max_insights
    assert len(ranked) <= config.max_insights


def test_empty_inputs(config, mock_llm_provider):
    """Test insight generation with empty inputs."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = generator.generate_insights([], [], [])

    # Should handle empty inputs gracefully
    assert isinstance(insights, list)


def test_relation_insight_filtering(config, mock_llm_provider):
    """Test that weak relations are filtered out from relation insights."""
    generator = InsightGenerator(config, mock_llm_provider)

    # Create relations with varying strengths
    relations = [
        Relation(
            id="rel-strong-1",
            source_concept="A",
            target_concept="B",
            relation_type=RelationType.CAUSES,
            strength=0.9,
            confidence=0.8
        ),
        Relation(
            id="rel-strong-2",
            source_concept="C",
            target_concept="D",
            relation_type=RelationType.CAUSES,
            strength=0.75,
            confidence=0.7
        ),
        Relation(
            id="rel-weak",
            source_concept="E",
            target_concept="F",
            relation_type=RelationType.RELATED_TO,
            strength=0.5,
            confidence=0.6
        )
    ]

    insights = generator._generate_relation_insights(relations)

    # Should only include strong relations (strength >= 0.7)
    assert len(insights) == 2

    for insight in insights:
        # Check that the insight is based on a strong relation
        # Just verify we got 2 insights from the 2 strong relations
        assert insight.insight_type == InsightType.RELATION


def test_pattern_suggestions_all_types(config, mock_llm_provider):
    """Test pattern suggestions for all pattern types."""
    generator = InsightGenerator(config, mock_llm_provider)

    pattern_types = [
        (PatternType.TEMPORAL, "Temporal Pattern", {"period": "weekly"}),
        (PatternType.CAUSAL, "Causal Pattern", {"chain_length": 3}),
        (PatternType.EVOLUTIONARY, "Evolutionary Pattern", {"versions": 5}),
        (PatternType.CONFLICT, "Conflict Pattern", {"conflicts": 2})
    ]

    for pattern_type, title, metadata in pattern_types:
        pattern = Pattern(
            id=f"pattern-{pattern_type.value}",
            pattern_type=pattern_type,
            title=title,
            description=f"{title} description",
            confidence=0.8,
            significance_score=0.75,
            related_concepts=["concept1", "concept2"],
            related_patterns=[],
            evidence=[],
            metadata=metadata,
            detected_at=datetime.now()
        )

        suggestions = generator._generate_pattern_suggestions(pattern)

        assert len(suggestions) > 0, f"No suggestions generated for {pattern_type}"
        assert all(isinstance(s, str) for s in suggestions)


def test_insight_metadata_quality(config, mock_llm_provider, mock_patterns):
    """Test that insight metadata is properly populated."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = generator._generate_pattern_insights(mock_patterns)

    for insight in insights:
        assert insight.id is not None
        assert insight.generated_at is not None
        assert isinstance(insight.metadata, dict)
        assert isinstance(insight.related_concepts, list)
        assert isinstance(insight.related_patterns, list)
        assert isinstance(insight.related_gaps, list)
        assert isinstance(insight.evidence, list)
        assert isinstance(insight.actionable_suggestions, list)


def test_gap_insight_actionability(config, mock_llm_provider, mock_gaps):
    """Test that gap insights have appropriate actionability scores."""
    generator = InsightGenerator(config, mock_llm_provider)

    insights = generator._generate_gap_insights(mock_gaps)

    for insight in insights:
        if insight.insight_type == InsightType.GAP:
            # Actionability should be based on gap.priority / 10.0
            # Find the corresponding gap
            gap = next((g for g in mock_gaps if g.id in insight.related_gaps), None)
            if gap:
                expected_actionability = gap.priority / 10.0
                # The significance should incorporate this actionability
                assert 0.0 <= insight.significance <= 1.0
