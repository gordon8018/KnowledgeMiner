"""
Tests for PatternDetector.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.discovery.config import DiscoveryConfig
from src.discovery.models.pattern import Pattern, PatternType, Evidence
from src.discovery.pattern_detector import PatternDetector
from src.core.document_model import EnhancedDocument, DocumentMetadata
from src.core.concept_model import EnhancedConcept, ConceptType, TemporalInfo
from src.core.relation_model import Relation, RelationType


@pytest.fixture
def config():
    """Create a test DiscoveryConfig."""
    return DiscoveryConfig(
        enable_temporal_detection=True,
        enable_causal_detection=True,
        enable_evolutionary_detection=True,
        enable_conflict_detection=True,
        min_pattern_confidence=0.6,
        min_pattern_significance=0.5
    )


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    return Mock()


@pytest.fixture
def mock_documents():
    """Create mock documents with temporal references."""
    now = datetime.now()

    # Create documents with monthly pattern
    docs = []
    for i in range(5):
        date = now - timedelta(days=30 * i)
        doc = EnhancedDocument(
            id=f"doc-{i}",
            source_type="text",
            content=f"Document content from {date.strftime('%Y-%m-%d')}",
            metadata=DocumentMetadata(
                title=f"Document {i}",
                date=date
            )
        )
        docs.append(doc)

    # Add documents with weekly pattern
    for i in range(4):
        date = now - timedelta(days=7 * i)
        doc = EnhancedDocument(
            id=f"weekly-doc-{i}",
            source_type="text",
            content=f"Weekly report from {date.strftime('%Y-%m-%d')}",
            metadata=DocumentMetadata(
                title=f"Weekly Report {i}",
                date=date
            )
        )
        docs.append(doc)

    return docs


@pytest.fixture
def mock_concepts():
    """Create mock concepts including evolutionary versions."""
    concepts = []

    # Concept with multiple versions
    for i in range(3):
        concept = EnhancedConcept(
            id=f"strategy-v{i}",
            name="tradingstrategy",
            type=ConceptType.STRATEGY,
            definition=f"Trading strategy version {i}" if i > 0 else "Original trading strategy",
            confidence=0.8,
            temporal_info=TemporalInfo(
                created=datetime.now() - timedelta(days=30 * (3 - i))
            )
        )
        concepts.append(concept)

    # Regular concept
    concept = EnhancedConcept(
        id="concept-1",
        name="market_trend",
        type=ConceptType.THEORY,
        definition="Market trend analysis",
        confidence=0.7
    )
    concepts.append(concept)

    # High confidence concept for conflict testing
    concept1 = EnhancedConcept(
        id="bullish-view",
        name="bullish_view",
        type=ConceptType.THEORY,
        definition="Market will go up",
        confidence=0.9
    )
    concepts.append(concept1)

    concept2 = EnhancedConcept(
        id="bearish-view",
        name="bearish_view",
        type=ConceptType.THEORY,
        definition="Market will go down",
        confidence=0.8
    )
    concepts.append(concept2)

    return concepts


@pytest.fixture
def mock_relations():
    """Create mock relations including causal chains."""
    relations = []

    # Create causal chain: A -> B -> C -> D
    causal_chain = [
        ("concept-a", "concept-b", RelationType.CAUSES),
        ("concept-b", "concept-c", RelationType.CAUSES),
        ("concept-c", "concept-d", RelationType.CAUSES),
    ]

    for source, target, rel_type in causal_chain:
        relation = Relation(
            id=f"rel-{source}-{target}",
            source_concept=source,
            target_concept=target,
            relation_type=rel_type,
            strength=0.8,
            confidence=0.7
        )
        relations.append(relation)

    # Create conflict relation
    conflict_relation = Relation(
        id="rel-bullish-bearish",
        source_concept="bullish-view",
        target_concept="bearish-view",
        relation_type=RelationType.OPPOSES,
        strength=0.9,
        confidence=0.8
    )
    relations.append(conflict_relation)

    # Create non-causal relation (should be ignored)
    other_relation = Relation(
        id="rel-related",
        source_concept="concept-x",
        target_concept="concept-y",
        relation_type=RelationType.RELATED_TO,
        strength=0.5,
        confidence=0.6
    )
    relations.append(other_relation)

    return relations


def test_pattern_detector_init(config, mock_llm_provider):
    """Test PatternDetector initialization."""
    detector = PatternDetector(config, mock_llm_provider)

    assert detector.config == config
    assert detector.llm_provider == mock_llm_provider
    assert detector.config.enable_temporal_detection is True
    assert detector.config.enable_causal_detection is True


def test_detect_temporal_patterns(config, mock_llm_provider, mock_documents):
    """Test temporal pattern detection."""
    detector = PatternDetector(config, mock_llm_provider)

    patterns = detector._detect_temporal_patterns(mock_documents)

    # Should detect at least one temporal pattern
    assert len(patterns) >= 1

    # Check that patterns have correct type and structure
    pattern = patterns[0]
    assert pattern.pattern_type == PatternType.TEMPORAL
    assert pattern.confidence >= 0.0
    assert len(pattern.evidence) > 0
    assert pattern.metadata.get("period") in ["weekly", "monthly", "quarterly", "yearly"]


def test_detect_causal_patterns(config, mock_llm_provider, mock_relations):
    """Test causal pattern detection."""
    detector = PatternDetector(config, mock_llm_provider)

    patterns = detector._detect_causal_patterns(mock_relations)

    # Should detect causal chains
    assert len(patterns) > 0

    causal_pattern = patterns[0]
    assert causal_pattern.pattern_type == PatternType.CAUSAL
    assert causal_pattern.confidence >= 0.0
    assert len(causal_pattern.related_concepts) >= 3
    assert "concept-a" in causal_pattern.related_concepts
    # Should include at least 3 concepts in the chain


def test_detect_evolutionary_patterns(config, mock_llm_provider, mock_concepts):
    """Test evolutionary pattern detection."""
    detector = PatternDetector(config, mock_llm_provider)

    patterns = detector._detect_evolutionary_patterns(mock_concepts)

    # Should detect evolution of trading_strategy
    assert len(patterns) > 0

    evo_pattern = patterns[0]
    assert evo_pattern.pattern_type == PatternType.EVOLUTIONARY
    assert "trading" in evo_pattern.title.lower()
    assert evo_pattern.confidence >= 0.0
    assert len(evo_pattern.related_concepts) >= 2


def test_detect_conflict_patterns(config, mock_llm_provider, mock_concepts, mock_relations):
    """Test conflict pattern detection."""
    detector = PatternDetector(config, mock_llm_provider)

    patterns = detector._detect_conflict_patterns(mock_concepts, mock_relations)

    # Should detect conflict between bullish and bearish views
    assert len(patterns) > 0

    conflict_pattern = patterns[0]
    assert conflict_pattern.pattern_type == PatternType.CONFLICT
    assert "bullish" in conflict_pattern.title.lower() or "conflict" in conflict_pattern.title.lower()
    assert conflict_pattern.confidence >= 0.0
    assert len(conflict_pattern.related_concepts) >= 2


def test_detect_patterns_integration(
    config, mock_llm_provider, mock_documents, mock_concepts, mock_relations
):
    """Test full pattern detection integration."""
    detector = PatternDetector(config, mock_llm_provider)

    patterns = detector.detect_patterns(mock_documents, mock_concepts, mock_relations)

    # Should detect multiple pattern types
    assert len(patterns) > 0

    pattern_types = {p.pattern_type for p in patterns}
    assert PatternType.TEMPORAL in pattern_types
    assert PatternType.CAUSAL in pattern_types
    assert PatternType.EVOLUTIONARY in pattern_types
    assert PatternType.CONFLICT in pattern_types


def test_compute_path_strength(config, mock_llm_provider, mock_relations):
    """Test causal path strength computation."""
    detector = PatternDetector(config, mock_llm_provider)

    # Build a simple graph
    import networkx as nx
    graph = nx.DiGraph()

    for rel in mock_relations:
        if rel.relation_type in [RelationType.CAUSES, RelationType.CAUSED_BY]:
            graph.add_edge(
                rel.source_concept,
                rel.target_concept,
                weight=rel.strength
            )

    # Test path strength
    path = ["concept-a", "concept-b", "concept-c"]
    strength = detector._compute_path_strength(graph, path)

    assert strength > 0.0
    assert strength <= 1.0


def test_pattern_detector_disabled_detections(config, mock_llm_provider, mock_documents):
    """Test PatternDetector with specific detections disabled."""
    # Disable all but temporal
    config.enable_causal_detection = False
    config.enable_evolutionary_detection = False
    config.enable_conflict_detection = False

    detector = PatternDetector(config, mock_llm_provider)

    patterns = detector.detect_patterns(mock_documents, [], [])

    # Should only have temporal patterns
    assert len(patterns) > 0
    for pattern in patterns:
        assert pattern.pattern_type == PatternType.TEMPORAL


def test_pattern_detector_empty_inputs(config, mock_llm_provider):
    """Test PatternDetector with empty inputs."""
    detector = PatternDetector(config, mock_llm_provider)

    patterns = detector.detect_patterns([], [], [])

    # Should handle empty inputs gracefully
    assert isinstance(patterns, list)
    # May have some patterns from metadata, but should not crash


def test_pattern_confidence_filtering(config, mock_llm_provider, mock_documents):
    """Test that low-confidence patterns are filtered."""
    # Set high minimum confidence
    config.min_pattern_confidence = 0.95

    detector = PatternDetector(config, mock_llm_provider)

    patterns = detector.detect_patterns(mock_documents, [], [])

    # All patterns should meet the minimum confidence threshold
    for pattern in patterns:
        assert pattern.confidence >= config.min_pattern_confidence


def test_pattern_metadata_quality(config, mock_llm_provider, mock_documents, mock_concepts, mock_relations):
    """Test that pattern metadata is properly populated."""
    detector = PatternDetector(config, mock_llm_provider)

    patterns = detector.detect_patterns(mock_documents, mock_concepts, mock_relations)

    # Check that patterns have proper metadata
    for pattern in patterns:
        assert pattern.id is not None
        assert pattern.detected_at is not None
        assert isinstance(pattern.metadata, dict)
        assert pattern.significance_score >= 0.0
        assert pattern.significance_score <= 1.0
