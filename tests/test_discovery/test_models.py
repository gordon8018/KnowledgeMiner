"""
Tests for discovery models and configuration.
"""

import pytest
from datetime import datetime

from src.discovery.config import DiscoveryConfig
from src.discovery.models.pattern import Pattern, PatternType, Evidence
from src.discovery.models.gap import KnowledgeGap, GapType
from src.discovery.models.insight import Insight, InsightType


def test_discovery_config_defaults():
    """Test DiscoveryConfig default values."""
    config = DiscoveryConfig()

    assert config.enable_explicit_mining is True
    assert config.min_relation_confidence == 0.6
    assert config.max_insights == 100


def test_discovery_config_validation():
    """Test DiscoveryConfig validation."""
    # Valid config
    config = DiscoveryConfig(min_relation_confidence=0.8)
    assert config.min_relation_confidence == 0.8

    # Invalid config - should raise validation error
    with pytest.raises(Exception):
        DiscoveryConfig(min_relation_confidence=1.5)  # > 1.0


def test_discovery_config_env_prefix():
    """Test environment variable prefix."""
    config = DiscoveryConfig()
    # Check that the model_config has the correct env_prefix
    assert config.model_config.get('env_prefix') == "KC_DISCOVERY_"


def test_pattern_creation():
    """Test Pattern model creation and validation."""
    pattern = Pattern(
        id="pattern-1",
        pattern_type=PatternType.TEMPORAL,
        title="Test Pattern",
        description="A test temporal pattern",
        confidence=0.8,
        evidence=[],
        related_concepts=["concept1"],
        related_patterns=[],
        metadata={},
        significance_score=0.75,
        detected_at=datetime.now()
    )

    assert pattern.pattern_type == PatternType.TEMPORAL
    assert pattern.confidence == 0.8


def test_pattern_validation():
    """Test Pattern validation."""
    with pytest.raises(ValueError):
        Pattern(
            id="pattern-1",
            pattern_type=PatternType.TEMPORAL,
            title="Test",
            description="Test",
            confidence=1.5,  # Invalid: > 1.0
            evidence=[],
            related_concepts=[],
            related_patterns=[],
            metadata={},
            significance_score=0.5,
            detected_at=datetime.now()
        )


def test_knowledge_gap_creation():
    """Test KnowledgeGap model creation."""
    gap = KnowledgeGap(
        id="gap-1",
        gap_type=GapType.MISSING_CONCEPT,
        description="Missing concept X",
        severity=0.7,
        affected_concepts=["concept1"],
        affected_relations=[],
        suggested_actions=["Add concept X"],
        priority=5,
        estimated_effort="medium",
        metadata={},
        detected_at=datetime.now()
    )

    assert gap.gap_type == GapType.MISSING_CONCEPT
    assert gap.priority == 5


def test_insight_creation():
    """Test Insight model creation."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="A test insight",
        significance=0.85,
        related_concepts=["concept1"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=["Action 1"],
        generated_at=datetime.now(),
        metadata={}
    )

    assert insight.insight_type == InsightType.PATTERN
    assert insight.significance == 0.85
