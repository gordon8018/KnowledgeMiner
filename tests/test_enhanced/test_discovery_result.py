import pytest
from datetime import datetime
from src.enhanced.models import DiscoveryResult, DiscoveryType

def test_discovery_result_creation():
    """Test creating a DiscoveryResult"""
    result = DiscoveryResult(
        result_type=DiscoveryType.PATTERN,
        summary="Found a recurring pattern in the data",
        significance_score=0.8,
        confidence=0.75
    )

    assert result.result_type == DiscoveryType.PATTERN
    assert result.significance_score == 0.8
    assert result.confidence == 0.75
    assert result.affected_concepts == []
    assert isinstance(result.discovered_at, datetime)

def test_discovery_result_with_evidence():
    """Test DiscoveryResult with evidence"""
    result = DiscoveryResult(
        result_type=DiscoveryType.INSIGHT,
        summary="New insight discovered",
        significance_score=0.9,
        confidence=0.85,
        affected_concepts=["concept1", "concept2"],
        evidence=[
            {"source": "doc1.md", "quote": "Evidence here"}
        ]
    )

    assert len(result.affected_concepts) == 2
    assert len(result.evidence) == 1
    assert result.evidence[0]["source"] == "doc1.md"
