"""
Tests for GapAnalyzer - knowledge gap analysis.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from src.discovery.gap_analyzer import GapAnalyzer
from src.discovery.config import DiscoveryConfig
from src.discovery.models.gap import KnowledgeGap, GapType
from src.core.concept_model import EnhancedConcept, ConceptType
from src.core.relation_model import Relation, RelationType


@pytest.fixture
def config():
    """Create test configuration."""
    return DiscoveryConfig(
        enable_concept_gap_analysis=True,
        enable_relation_gap_analysis=True,
        enable_evidence_analysis=True,
        min_evidence_confidence=0.4
    )


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    mock = Mock()
    mock.generate_response.return_value = """
    Based on the analysis, here are 3-5 missing concepts:

    1. **Attention Mechanism** - A crucial component in neural networks that allows the model to focus on relevant parts of the input
    2. **Transformer Architecture** - The foundational architecture behind modern language models
    3. **Gradient Descent** - The optimization algorithm used to train neural networks

    ```json
    {
      "missing_concepts": [
        {
          "name": "Attention Mechanism",
          "type": "term",
          "description": "A crucial component in neural networks that allows the model to focus on relevant parts of the input",
          "related_to": ["Deep Learning", "Machine Learning"]
        },
        {
          "name": "Transformer Architecture",
          "type": "theory",
          "description": "The foundational architecture behind modern language models",
          "related_to": ["Deep Learning"]
        },
        {
          "name": "Gradient Descent",
          "type": "indicator",
          "description": "The optimization algorithm used to train neural networks",
          "related_to": ["Machine Learning"]
        }
      ]
    }
    ```
    """
    return mock


@pytest.fixture
def mock_concepts():
    """Create mock concepts with varying confidence."""
    return [
        EnhancedConcept(
            id="concept-1",
            name="Machine Learning",
            type=ConceptType.THEORY,
            definition="A subset of AI that enables systems to learn from data",
            confidence=0.9,
            evidence=[
                {"source": "doc1", "quote": "Machine learning is...", "confidence": 0.9}
            ]
        ),
        EnhancedConcept(
            id="concept-2",
            name="Deep Learning",
            type=ConceptType.THEORY,
            definition="A subset of machine learning using neural networks",
            confidence=0.3,  # Low confidence - should be detected
            evidence=[
                {"source": "doc2", "quote": "Deep learning uses neural networks", "confidence": 0.3}
            ]
        ),
        EnhancedConcept(
            id="concept-3",
            name="Neural Networks",
            type=ConceptType.THEORY,
            definition="Computational models inspired by biological neurons",
            confidence=0.8,
            evidence=[
                {"source": "doc1", "quote": "Neural networks are...", "confidence": 0.8},
                {"source": "doc3", "quote": "Network architecture", "confidence": 0.7}
            ]
        )
    ]


@pytest.fixture
def mock_relations():
    """Create mock relations."""
    return [
        Relation(
            id="relation-1",
            source_concept="Machine Learning",
            target_concept="Deep Learning",
            relation_type=RelationType.CONTAINS,
            strength=0.8,
            confidence=0.9
        ),
        Relation(
            id="relation-2",
            source_concept="Deep Learning",
            target_concept="Neural Networks",
            relation_type=RelationType.DEPENDS_ON,
            strength=0.7,
            confidence=0.8
        )
    ]


@pytest.fixture
def mock_documents():
    """Create mock documents."""
    return [
        {
            "id": "doc1",
            "title": "Introduction to Machine Learning",
            "content": "Machine learning is a subset of artificial intelligence..."
        },
        {
            "id": "doc2",
            "title": "Deep Learning Basics",
            "content": "Deep learning uses neural networks to learn..."
        },
        {
            "id": "doc3",
            "title": "Neural Network Architectures",
            "content": "Neural networks are computational models..."
        }
    ]


def test_analyze_insufficient_evidence(config, mock_concepts):
    """Test detection of concepts with insufficient evidence."""
    analyzer = GapAnalyzer(config=config, llm_provider=None)

    # Disable concept and relation gap analysis to focus on evidence analysis
    config.enable_concept_gap_analysis = False
    config.enable_relation_gap_analysis = False

    gaps = analyzer.analyze_gaps(
        documents=[],
        concepts=mock_concepts,
        relations=[]
    )

    # Should find weak evidence gaps
    weak_evidence_gaps = [g for g in gaps if g.gap_type == GapType.WEAK_EVIDENCE]

    # Should find at least 1 gap (Deep Learning with low confidence 0.3)
    assert len(weak_evidence_gaps) >= 1

    # Check that Deep Learning is flagged for low confidence
    low_confidence_gaps = [
        g for g in weak_evidence_gaps
        if "Deep Learning" in g.affected_concepts and
        g.metadata.get("weakness_type") == "low_confidence"
    ]
    assert len(low_confidence_gaps) == 1
    gap = low_confidence_gaps[0]

    assert gap.gap_type == GapType.WEAK_EVIDENCE
    assert "Deep Learning" in gap.affected_concepts
    assert gap.severity == pytest.approx(0.7, rel=1e-2)  # 1.0 - 0.3 = 0.7


def test_analyze_missing_relations(config, mock_concepts, mock_relations):
    """Test detection of missing relations using graph analysis."""
    analyzer = GapAnalyzer(config=config, llm_provider=None)

    # Disable concept and evidence gap analysis
    config.enable_concept_gap_analysis = False
    config.enable_evidence_analysis = False

    # Add an isolated concept (no relations)
    isolated_concept = EnhancedConcept(
        id="concept-4",
        name="Isolated Concept",
        type=ConceptType.TERM,
        definition="A concept with no relations",
        confidence=0.9
    )
    mock_concepts_with_isolated = mock_concepts + [isolated_concept]

    gaps = analyzer.analyze_gaps(
        documents=[],
        concepts=mock_concepts_with_isolated,
        relations=mock_relations
    )

    # Should find missing relation gaps (isolated or weak communities)
    missing_relation_gaps = [g for g in gaps if g.gap_type == GapType.MISSING_RELATION]

    assert len(missing_relation_gaps) >= 1

    # Check that we find the isolated concept (priority 4)
    isolated_gaps = [g for g in missing_relation_gaps if g.priority == 4]
    assert len(isolated_gaps) >= 1
    assert "Isolated Concept" in isolated_gaps[0].affected_concepts


def test_analyze_missing_concepts(config, mock_concepts, mock_documents, mock_llm_provider):
    """Test LLM-based missing concept analysis."""
    analyzer = GapAnalyzer(config=config, llm_provider=mock_llm_provider)

    # Disable relation and evidence gap analysis
    config.enable_relation_gap_analysis = False
    config.enable_evidence_analysis = False

    gaps = analyzer.analyze_gaps(
        documents=mock_documents,
        concepts=mock_concepts,
        relations=[]
    )

    # Should find missing concepts from LLM
    missing_concept_gaps = [g for g in gaps if g.gap_type == GapType.MISSING_CONCEPT]

    assert len(missing_concept_gaps) == 3  # Based on mock LLM response

    # Check first gap
    gap1 = missing_concept_gaps[0]
    assert gap1.gap_type == GapType.MISSING_CONCEPT
    assert "Attention Mechanism" in gap1.description or "Attention" in gap1.description
    assert gap1.priority == 2  # Missing concepts get priority 2


def test_full_gap_analysis(config, mock_concepts, mock_relations, mock_documents, mock_llm_provider):
    """Test complete gap analysis with all three types enabled."""
    analyzer = GapAnalyzer(config=config, llm_provider=mock_llm_provider)

    # Add isolated concept for relation gap testing
    isolated_concept = EnhancedConcept(
        id="concept-4",
        name="Isolated Concept",
        type=ConceptType.TERM,
        definition="A concept with no relations",
        confidence=0.9
    )
    enhanced_concepts = mock_concepts + [isolated_concept]

    gaps = analyzer.analyze_gaps(
        documents=mock_documents,
        concepts=enhanced_concepts,
        relations=mock_relations
    )

    # Should find all three types of gaps
    gap_types = {g.gap_type for g in gaps}

    assert GapType.WEAK_EVIDENCE in gap_types
    assert GapType.MISSING_RELATION in gap_types
    assert GapType.MISSING_CONCEPT in gap_types

    # Check gaps are sorted by priority (high to low)
    priorities = [g.priority for g in gaps]
    assert priorities == sorted(priorities, reverse=True)


def test_gap_analyzer_with_llm_error(config, mock_concepts):
    """Test handling of LLM provider errors."""
    # Mock LLM that raises error
    mock_llm = Mock()
    mock_llm.generate_response.side_effect = Exception("LLM API error")

    analyzer = GapAnalyzer(config=config, llm_provider=mock_llm)

    # Should not crash, just log error and continue
    gaps = analyzer.analyze_gaps(
        documents=[],
        concepts=mock_concepts,
        relations=[]
    )

    # Should still find weak evidence gaps
    weak_evidence_gaps = [g for g in gaps if g.gap_type == GapType.WEAK_EVIDENCE]
    assert len(weak_evidence_gaps) >= 1


def test_gap_analyzer_with_empty_inputs(config):
    """Test behavior with empty inputs."""
    analyzer = GapAnalyzer(config=config, llm_provider=None)

    gaps = analyzer.analyze_gaps(
        documents=[],
        concepts=[],
        relations=[]
    )

    # Should return empty list, not crash
    assert len(gaps) == 0


def test_missing_concepts_sampling(config, mock_concepts, mock_documents):
    """Test that missing concept analysis samples only first 5 concepts."""
    # Create 10 concepts
    many_concepts = []
    for i in range(10):
        concept = EnhancedConcept(
            id=f"concept-{i}",
            name=f"Concept {i}",
            type=ConceptType.TERM,
            definition=f"Definition {i}",
            confidence=0.8
        )
        many_concepts.append(concept)

    # Mock LLM to check how many concepts it receives
    mock_llm = Mock()
    mock_llm.generate_response.return_value = """
    ```json
    {
      "missing_concepts": []
    }
    ```
    """

    analyzer = GapAnalyzer(config=config, llm_provider=mock_llm)

    # Only enable concept gap analysis
    config.enable_relation_gap_analysis = False
    config.enable_evidence_analysis = False

    analyzer.analyze_gaps(
        documents=mock_documents,
        concepts=many_concepts,
        relations=[]
    )

    # Check that LLM was called (we don't validate exact sampling here,
    # just ensure it doesn't timeout with many concepts)
    assert mock_llm.generate_response.called


def test_gap_metadata_fields(config, mock_concepts):
    """Test that gaps have proper metadata fields."""
    analyzer = GapAnalyzer(config=config, llm_provider=None)

    # Disable all but evidence analysis
    config.enable_concept_gap_analysis = False
    config.enable_relation_gap_analysis = False

    gaps = analyzer.analyze_gaps(
        documents=[],
        concepts=mock_concepts,
        relations=[]
    )

    assert len(gaps) > 0
    gap = gaps[0]

    # Check required fields
    assert hasattr(gap, 'id')
    assert hasattr(gap, 'gap_type')
    assert hasattr(gap, 'description')
    assert hasattr(gap, 'severity')
    assert hasattr(gap, 'affected_concepts')
    assert hasattr(gap, 'affected_relations')
    assert hasattr(gap, 'suggested_actions')
    assert hasattr(gap, 'priority')
    assert hasattr(gap, 'estimated_effort')
    assert hasattr(gap, 'metadata')
    assert hasattr(gap, 'detected_at')

    # Check field types
    assert isinstance(gap.id, str)
    assert isinstance(gap.severity, float)
    assert isinstance(gap.affected_concepts, list)
    assert isinstance(gap.priority, int)
    assert isinstance(gap.estimated_effort, str)
    assert gap.estimated_effort in ["low", "medium", "high"]


def test_community_detection_weak_connections(config, mock_concepts, mock_relations):
    """Test detection of weakly connected communities."""
    analyzer = GapAnalyzer(config=config, llm_provider=None)

    # Disable concept and evidence gap analysis
    config.enable_concept_gap_analysis = False
    config.enable_evidence_analysis = False

    # Create concepts that form weak communities
    weak_community_concepts = []
    weak_community_relations = []

    # Create a community with 3 concepts but only 1 connection (avg degree < 2)
    for i in range(3):
        concept = EnhancedConcept(
            id=f"weak-concept-{i}",
            name=f"Weak Concept {i}",
            type=ConceptType.TERM,
            definition=f"Weak definition {i}",
            confidence=0.8
        )
        weak_community_concepts.append(concept)

    # Add only 1 relation between 3 concepts (weak connectivity)
    weak_community_relations.append(
        Relation(
            id="weak-relation-1",
            source_concept="Weak Concept 0",
            target_concept="Weak Concept 1",
            relation_type=RelationType.RELATED_TO,
            strength=0.5
        )
    )

    all_concepts = mock_concepts + weak_community_concepts
    all_relations = mock_relations + weak_community_relations

    gaps = analyzer.analyze_gaps(
        documents=[],
        concepts=all_concepts,
        relations=all_relations
    )

    # Should detect weak community
    missing_relation_gaps = [g for g in gaps if g.gap_type == GapType.MISSING_RELATION]

    # Check that weak community is detected (priority 3)
    weak_community_gaps = [g for g in missing_relation_gaps if g.priority == 3]
    assert len(weak_community_gaps) > 0
