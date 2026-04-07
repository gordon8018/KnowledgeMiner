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

def test_discovery_result_empty_summary_validation():
    """Test that empty summary is rejected"""
    with pytest.raises(ValueError, match="summary must not be empty"):
        DiscoveryResult(
            result_type=DiscoveryType.PATTERN,
            summary="   "
        )

def test_discovery_result_whitespace_only_summary():
    """Test that whitespace-only summary is rejected"""
    with pytest.raises(ValueError, match="summary must not be empty"):
        DiscoveryResult(
            result_type=DiscoveryType.PATTERN,
            summary=""
        )

def test_discovery_result_score_bounds():
    """Test score validation at boundaries"""
    result = DiscoveryResult(
        result_type=DiscoveryType.PATTERN,
        summary="Test",
        significance_score=0.0,
        confidence=1.0
    )
    assert result.significance_score == 0.0
    assert result.confidence == 1.0

def test_discovery_result_add_evidence():
    """Test adding evidence via helper method"""
    result = DiscoveryResult(
        result_type=DiscoveryType.PATTERN,
        summary="Test discovery"
    )
    result.add_evidence("doc1.md", "Evidence quote")

    assert len(result.evidence) == 1
    assert result.evidence[0]["source"] == "doc1.md"
    assert "added_at" in result.evidence[0]

def test_discovery_result_add_evidence_validation():
    """Test add_evidence rejects empty values"""
    result = DiscoveryResult(
        result_type=DiscoveryType.PATTERN,
        summary="Test"
    )

    with pytest.raises(ValueError, match="Source cannot be empty"):
        result.add_evidence("", "Quote")

    with pytest.raises(ValueError, match="Quote cannot be empty"):
        result.add_evidence("doc.md", "")

def test_discovery_result_add_affected_concept():
    """Test adding affected concepts with duplicate prevention"""
    result = DiscoveryResult(
        result_type=DiscoveryType.PATTERN,
        summary="Test"
    )

    result.add_affected_concept("concept1")
    result.add_affected_concept("concept2")
    result.add_affected_concept("concept1")  # Duplicate

    assert len(result.affected_concepts) == 2
    assert "concept1" in result.affected_concepts

def test_discovery_result_add_source_document():
    """Test adding source documents with duplicate prevention"""
    result = DiscoveryResult(
        result_type=DiscoveryType.PATTERN,
        summary="Test"
    )

    result.add_source_document("doc1.md")
    result.add_source_document("doc2.md")
    result.add_source_document("doc1.md")  # Duplicate

    assert len(result.source_documents) == 2
    assert "doc1.md" in result.source_documents
