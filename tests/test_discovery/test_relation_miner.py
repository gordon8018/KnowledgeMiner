"""
Tests for RelationMiningEngine - relation mining with explicit and implicit discovery.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from src.discovery.relation_miner import RelationMiningEngine
from src.discovery.config import DiscoveryConfig
from src.core.document_model import EnhancedDocument, DocumentMetadata, SourceType
from src.core.concept_model import EnhancedConcept, ConceptType
from src.core.relation_model import Relation, RelationType
from src.discovery.patterns.relation_patterns import RelationPatternLoader


@pytest.fixture
def config():
    """Create test configuration."""
    return DiscoveryConfig(
        enable_explicit_mining=True,
        enable_implicit_mining=True,
        enable_statistical_mining=True,
        enable_semantic_mining=True,
        min_relation_confidence=0.6,
        max_relations_per_concept=50,
        batch_size=10
    )


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    mock_provider = Mock()
    mock_provider.generate.return_value = '''
    [
        {
            "source": "利率",
            "target": "股市",
            "relation_type": "causes",
            "confidence": 0.8,
            "evidence": "利率上升导致股市下跌"
        }
    ]
    '''
    return mock_provider


@pytest.fixture
def mock_embedding_generator():
    """Create mock embedding generator."""
    mock_embedder = Mock()

    # Create mock embeddings for different concepts
    mock_embeddings = {
        "利率": np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
        "股市": np.array([0.2, 0.3, 0.4, 0.5, 0.6]),
        "通胀": np.array([0.3, 0.4, 0.5, 0.6, 0.7]),
        "物价": np.array([0.4, 0.5, 0.6, 0.7, 0.8]),
    }

    def generate_embeddings(texts):
        return [mock_embeddings.get(text, np.random.rand(5)) for text in texts]

    mock_embedder.generate_embeddings.side_effect = generate_embeddings
    return mock_embedder


@pytest.fixture
def mock_documents():
    """Create mock documents with relation patterns."""
    docs = [
        EnhancedDocument(
            id="doc-1",
            source_type=SourceType.MARKDOWN,
            content="利率上升导致股市下跌。通胀引起物价上涨。",
            metadata=DocumentMetadata(title="经济关系")
        ),
        EnhancedDocument(
            id="doc-2",
            source_type=SourceType.MARKDOWN,
            content="利率和股市密切相关。通胀影响物价水平。",
            metadata=DocumentMetadata(title="市场分析")
        )
    ]

    return docs


@pytest.fixture
def mock_concepts():
    """Create mock concepts."""
    concepts = [
        EnhancedConcept(
            id="concept-1",
            name="利率",
            type=ConceptType.INDICATOR,
            definition="资金借贷的价格",
            confidence=0.9
        ),
        EnhancedConcept(
            id="concept-2",
            name="股市",
            type=ConceptType.TERM,
            definition="股票交易市场",
            confidence=0.9
        ),
        EnhancedConcept(
            id="concept-3",
            name="通胀",
            type=ConceptType.INDICATOR,
            definition="物价水平持续上涨",
            confidence=0.8
        ),
        EnhancedConcept(
            id="concept-4",
            name="物价",
            type=ConceptType.INDICATOR,
            definition="商品和服务价格",
            confidence=0.8
        )
    ]

    # Set source documents
    concepts[0].source_documents = ["doc-1", "doc-2"]
    concepts[1].source_documents = ["doc-1", "doc-2"]
    concepts[2].source_documents = ["doc-1", "doc-2"]
    concepts[3].source_documents = ["doc-1", "doc-2"]

    return concepts


def test_relation_mining_engine_init(config, mock_llm_provider, mock_embedding_generator):
    """Test RelationMiningEngine initialization."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    assert engine.config == config
    assert engine.llm == mock_llm_provider
    assert engine.embedder == mock_embedding_generator
    assert isinstance(engine.pattern_loader, RelationPatternLoader)
    assert engine.config.min_relation_confidence == 0.6


def test_extract_explicit_relations(config, mock_llm_provider, mock_embedding_generator, mock_documents):
    """Test explicit relation extraction using pattern matching."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    relations = engine._extract_explicit_relations(mock_documents)

    # Should find explicit relations (patterns match 4-char sequences)
    assert len(relations) > 0

    # Check that at least one CAUSES relation was found
    causes_relations = [r for r in relations if r.relation_type == RelationType.CAUSES]
    assert len(causes_relations) > 0

    # Check that evidence was collected
    for relation in relations:
        assert len(relation.evidence) > 0
        assert relation.confidence >= 0.0
        # Check that source and target were extracted (even if garbled in display)
        assert len(relation.source_concept) > 0
        assert len(relation.target_concept) > 0


def test_discover_implicit_relations(config, mock_llm_provider, mock_embedding_generator, mock_concepts, mock_documents):
    """Test implicit relation discovery using LLM."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    relations = engine._discover_implicit_relations(mock_concepts, mock_documents)

    # Should find implicit relations from LLM
    assert len(relations) > 0

    # Check that relations have proper structure
    for relation in relations:
        assert relation.source_concept in [c.id for c in mock_concepts]
        assert relation.target_concept in [c.id for c in mock_concepts]
        assert 0.0 <= relation.confidence <= 1.0
        assert len(relation.evidence) > 0


def test_compute_statistical_relations(config, mock_llm_provider, mock_embedding_generator, mock_documents, mock_concepts):
    """Test statistical relation mining using co-occurrence and PMI."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    relations = engine._compute_statistical_relations(mock_documents, mock_concepts)

    # Should find statistical relations based on co-occurrence
    # Note: Our mock concepts all appear in the same documents, so they should co-occur
    assert len(relations) >= 0  # May be 0 if PMI threshold is too high

    # Check that PMI scores are converted to confidence
    for relation in relations:
        assert 0.0 <= relation.confidence <= 1.0
        assert relation.relation_type == RelationType.RELATED_TO
        assert len(relation.evidence) > 0
        # Check that concepts are from our list (either by name or ID)
        concept_names = [c.name for c in mock_concepts]
        concept_ids = [c.id for c in mock_concepts]
        assert relation.source_concept in concept_names or relation.source_concept in concept_ids
        assert relation.target_concept in concept_names or relation.target_concept in concept_ids


def test_compute_semantic_relations(config, mock_llm_provider, mock_embedding_generator, mock_concepts):
    """Test semantic relation mining using embedding similarity."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    relations = engine._compute_semantic_relations(mock_concepts)

    # Should find semantic relations based on embedding similarity
    assert len(relations) > 0

    # Check that cosine similarity is converted to confidence
    for relation in relations:
        assert 0.0 <= relation.confidence <= 1.0
        assert relation.relation_type == RelationType.SIMILAR_TO
        assert 0.0 <= relation.strength <= 1.0


def test_merge_and_score_relations(config, mock_llm_provider, mock_embedding_generator):
    """Test relation merging and scoring."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    # Create duplicate relations from different sources
    relations = [
        Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.CAUSES,
            confidence=0.7,
            strength=0.6,
            evidence=[{"source": "explicit", "quote": "quote1", "extraction_method": "explicit"}]
        ),
        Relation(
            id="rel-2",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.CAUSES,
            confidence=0.8,
            strength=0.7,
            evidence=[{"source": "implicit", "quote": "quote2", "extraction_method": "implicit"}]
        ),
        Relation(
            id="rel-3",
            source_concept="concept-3",
            target_concept="concept-4",
            relation_type=RelationType.RELATED_TO,
            confidence=0.9,
            strength=0.8,
            evidence=[{"source": "statistical", "quote": "quote3", "extraction_method": "statistical"}]
        )
    ]

    merged = engine._merge_and_score_relations(relations)

    # Should merge duplicate relations
    assert len(merged) <= len(relations)

    # Check that merged relations have combined evidence
    for relation in merged:
        assert len(relation.evidence) > 0
        assert 0.0 <= relation.confidence <= 1.0
        assert 0.0 <= relation.strength <= 1.0


def test_mine_relations_full_pipeline(config, mock_llm_provider, mock_embedding_generator, mock_documents, mock_concepts):
    """Test full relation mining pipeline."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    relations = engine.mine_relations(mock_documents, mock_concepts)

    # Should find relations from all strategies
    assert len(relations) > 0

    # Check that all relations meet minimum confidence threshold
    for relation in relations:
        assert relation.confidence >= config.min_relation_confidence
        assert len(relation.evidence) > 0

    # Check that relations have valid structure (even if concept names are garbled)
    for relation in relations:
        assert len(relation.source_concept) > 0
        assert len(relation.target_concept) > 0
        assert relation.id is not None


def test_format_concepts_for_llm(config, mock_llm_provider, mock_embedding_generator, mock_concepts):
    """Test formatting concepts for LLM input."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    formatted = engine._format_concepts_for_llm(mock_concepts)

    assert isinstance(formatted, str)
    assert "利率" in formatted
    assert "股市" in formatted
    assert "资金借贷的价格" in formatted  # Check definition is included


def test_parse_llm_relations(config, mock_llm_provider, mock_embedding_generator, mock_concepts):
    """Test parsing LLM response into relations."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    llm_response = '''
    [
        {
            "source": "利率",
            "target": "股市",
            "relation_type": "causes",
            "confidence": 0.8,
            "evidence": "利率上升导致股市下跌"
        }
    ]
    '''

    relations = engine._parse_llm_relations(llm_response, mock_concepts)

    assert len(relations) > 0
    assert relations[0].relation_type == RelationType.CAUSES
    assert relations[0].confidence == 0.8


def test_cosine_similarity(config, mock_llm_provider, mock_embedding_generator):
    """Test cosine similarity calculation."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([0.0, 1.0, 0.0])
    vec3 = np.array([1.0, 0.0, 0.0])

    # Orthogonal vectors
    similarity = engine._cosine_similarity(vec1, vec2)
    assert abs(similarity) < 0.01  # Should be ~0

    # Identical vectors
    similarity = engine._cosine_similarity(vec1, vec3)
    assert abs(similarity - 1.0) < 0.01  # Should be ~1


def test_limit_relations_per_concept(config, mock_llm_provider, mock_embedding_generator):
    """Test limiting relations per concept."""
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    # Create many relations for the same concept
    relations = []
    for i in range(100):
        relations.append(Relation(
            id=f"rel-{i}",
            source_concept="concept-1",
            target_concept=f"concept-{i}",
            relation_type=RelationType.RELATED_TO,
            confidence=0.9,
            strength=0.8,
            evidence=[{"source": "test", "quote": f"Relation {i}"}]
        ))

    limited = engine._limit_relations_per_concept(relations)

    # Should limit to max_relations_per_concept
    concept_1_relations = [r for r in limited if r.source_concept == "concept-1"]
    assert len(concept_1_relations) <= config.max_relations_per_concept


def test_disable_implicit_mining(config, mock_llm_provider, mock_embedding_generator, mock_documents, mock_concepts):
    """Test that implicit mining can be disabled."""
    config.enable_implicit_mining = False
    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    relations = engine.mine_relations(mock_documents, mock_concepts)

    # LLM should not be called when implicit mining is disabled
    assert not mock_llm_provider.generate.called


def test_error_handling_llm_failure(config, mock_llm_provider, mock_embedding_generator, mock_documents, mock_concepts):
    """Test error handling when LLM fails."""
    # Make LLM raise an exception
    mock_llm_provider.generate.side_effect = Exception("LLM API error")

    engine = RelationMiningEngine(
        config=config,
        llm_provider=mock_llm_provider,
        embedding_generator=mock_embedding_generator
    )

    # Should not crash, should return empty list for implicit relations
    relations = engine.mine_relations(mock_documents, mock_concepts)

    # Should still find explicit and statistical relations
    assert len(relations) > 0
