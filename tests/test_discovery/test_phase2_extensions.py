"""
Tests for Phase 2 incremental mode extensions.

Tests the mode parameter (full/incremental/hybrid) for:
- RelationMiningEngine
- PatternDetector
- GapAnalyzer
- InsightGenerator
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.discovery.relation_miner import RelationMiningEngine
from src.discovery.pattern_detector import PatternDetector
from src.discovery.gap_analyzer import GapAnalyzer
from src.discovery.insight_generator import InsightGenerator
from src.discovery.config import DiscoveryConfig
from src.core.document_model import EnhancedDocument, DocumentMetadata, SourceType
from src.core.concept_model import EnhancedConcept, ConceptType
from src.core.relation_model import Relation, RelationType
from src.discovery.models.pattern import Pattern, PatternType, Evidence
from src.discovery.models.gap import KnowledgeGap, GapType


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
        batch_size=10,
        enable_temporal_detection=True,
        enable_causal_detection=True,
        enable_evolutionary_detection=True,
        enable_conflict_detection=True,
        min_pattern_confidence=0.7,
        enable_concept_gap_analysis=True,
        enable_relation_gap_analysis=True,
        enable_evidence_analysis=True,
        min_evidence_confidence=0.7,
        insight_significance_threshold=0.5,
        max_insights=20
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
    mock_provider.generate_response.return_value = '''
    {
        "missing_concepts": [
            {
                "name": "Test Concept",
                "type": "term",
                "description": "A test concept",
                "related_to": ["利率"]
            }
        ]
    }
    '''
    return mock_provider


@pytest.fixture
def mock_embedding_generator():
    """Create mock embedding generator."""
    mock_embedder = Mock()
    mock_embedder.generate_embeddings.return_value = [
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.2, 0.3, 0.4, 0.5, 0.6]
    ]
    return mock_embedder


@pytest.fixture
def sample_documents():
    """Create sample documents."""
    return [
        EnhancedDocument(
            id="doc-1",
            source_type=SourceType.MARKDOWN,
            content="利率上升导致股市下跌。",
            metadata=DocumentMetadata(title="经济关系")
        ),
        EnhancedDocument(
            id="doc-2",
            source_type=SourceType.MARKDOWN,
            content="通胀引起物价上涨。",
            metadata=DocumentMetadata(title="市场分析")
        )
    ]


@pytest.fixture
def sample_concepts():
    """Create sample concepts."""
    return [
        EnhancedConcept(
            id="concept-1",
            name="利率",
            type=ConceptType.INDICATOR,
            definition="资金借贷的价格",
            confidence=0.9,
            source_documents=["doc-1"]
        ),
        EnhancedConcept(
            id="concept-2",
            name="股市",
            type=ConceptType.INDICATOR,
            definition="股票交易市场",
            confidence=0.8,
            source_documents=["doc-1"]
        ),
        EnhancedConcept(
            id="concept-3",
            name="通胀",
            type=ConceptType.INDICATOR,
            definition="物价水平持续上涨",
            confidence=0.7,
            source_documents=["doc-2"]
        )
    ]


@pytest.fixture
def sample_relations():
    """Create sample relations."""
    return [
        Relation(
            id="rel-1",
            source_concept="concept-1",
            target_concept="concept-2",
            relation_type=RelationType.CAUSES,
            confidence=0.8,
            strength=0.7,
            evidence=[{
                "source": "doc-1",
                "quote": "利率上升导致股市下跌"
            }]
        )
    ]


@pytest.fixture
def sample_patterns():
    """Create sample patterns."""
    return [
        Pattern(
            id="pattern-1",
            pattern_type=PatternType.TEMPORAL,
            title="Test Pattern",
            description="A test pattern",
            confidence=0.8,
            evidence=[],
            related_concepts=["concept-1"],
            related_patterns=[],
            metadata={},
            significance_score=0.7,
            detected_at=datetime.now()
        )
    ]


@pytest.fixture
def sample_gaps():
    """Create sample gaps."""
    return [
        KnowledgeGap(
            id="gap-1",
            gap_type=GapType.MISSING_CONCEPT,
            description="Missing test concept",
            severity=0.7,
            affected_concepts=["concept-1"],
            affected_relations=[],
            suggested_actions=["Add concept"],
            priority=2,
            estimated_effort="medium",
            metadata={},
            detected_at=datetime.now()
        )
    ]


class TestRelationMiningEngineModes:
    """Tests for RelationMiningEngine mode parameter."""

    def test_full_mode_default(self, config, mock_llm_provider, mock_embedding_generator,
                               sample_documents, sample_concepts):
        """Test that full mode is the default behavior."""
        engine = RelationMiningEngine(config, mock_llm_provider, mock_embedding_generator)

        # Call without mode parameter (should default to 'full')
        relations = engine.mine_relations(sample_documents, sample_concepts)

        # Should return relations
        assert isinstance(relations, list)

    def test_full_mode_explicit(self, config, mock_llm_provider, mock_embedding_generator,
                                sample_documents, sample_concepts):
        """Test explicit full mode."""
        engine = RelationMiningEngine(config, mock_llm_provider, mock_embedding_generator)

        relations = engine.mine_relations(sample_documents, sample_concepts, mode='full')

        # Should return relations
        assert isinstance(relations, list)

    def test_incremental_mode(self, config, mock_llm_provider, mock_embedding_generator,
                             sample_documents, sample_concepts):
        """Test incremental mode with changed documents."""
        engine = RelationMiningEngine(config, mock_llm_provider, mock_embedding_generator)

        relations = engine.mine_relations(sample_documents, sample_concepts, mode='incremental')

        # Should return relations (possibly fewer in incremental mode)
        assert isinstance(relations, list)

    def test_hybrid_mode_small_batch(self, config, mock_llm_provider, mock_embedding_generator,
                                    sample_documents, sample_concepts):
        """Test hybrid mode with small batch (< 10 documents)."""
        engine = RelationMiningEngine(config, mock_llm_provider, mock_embedding_generator)

        relations = engine.mine_relations(sample_documents, sample_concepts, mode='hybrid')

        # Should return relations
        assert isinstance(relations, list)

    def test_invalid_mode(self, config, mock_llm_provider, mock_embedding_generator,
                         sample_documents, sample_concepts):
        """Test that invalid mode raises ValueError."""
        engine = RelationMiningEngine(config, mock_llm_provider, mock_embedding_generator)

        with pytest.raises(ValueError, match="Unknown mode"):
            engine.mine_relations(sample_documents, sample_concepts, mode='invalid')


class TestPatternDetectorModes:
    """Tests for PatternDetector mode parameter."""

    def test_full_mode_default(self, config, sample_documents, sample_concepts, sample_relations):
        """Test that full mode is the default behavior."""
        detector = PatternDetector(config, Mock())

        # Call without mode parameter (should default to 'full')
        patterns = detector.detect_patterns(sample_documents, sample_concepts, sample_relations)

        # Should return patterns
        assert isinstance(patterns, list)

    def test_full_mode_explicit(self, config, sample_documents, sample_concepts, sample_relations):
        """Test explicit full mode."""
        detector = PatternDetector(config, Mock())

        patterns = detector.detect_patterns(
            sample_documents, sample_concepts, sample_relations, mode='full'
        )

        # Should return patterns
        assert isinstance(patterns, list)

    def test_incremental_mode(self, config, sample_documents, sample_concepts, sample_relations):
        """Test incremental mode."""
        detector = PatternDetector(config, Mock())

        patterns = detector.detect_patterns(
            sample_documents, sample_concepts, sample_relations, mode='incremental'
        )

        # Should return patterns
        assert isinstance(patterns, list)

    def test_hybrid_mode_small_batch(self, config, sample_documents, sample_concepts, sample_relations):
        """Test hybrid mode with small batch."""
        detector = PatternDetector(config, Mock())

        patterns = detector.detect_patterns(
            sample_documents, sample_concepts, sample_relations, mode='hybrid'
        )

        # Should return patterns
        assert isinstance(patterns, list)

    def test_invalid_mode(self, config, sample_documents, sample_concepts, sample_relations):
        """Test that invalid mode raises ValueError."""
        detector = PatternDetector(config, Mock())

        with pytest.raises(ValueError, match="Unknown mode"):
            detector.detect_patterns(
                sample_documents, sample_concepts, sample_relations, mode='invalid'
            )


class TestGapAnalyzerModes:
    """Tests for GapAnalyzer mode parameter."""

    def test_full_mode_default(self, config, mock_llm_provider, sample_documents, sample_concepts,
                               sample_relations):
        """Test that full mode is the default behavior."""
        analyzer = GapAnalyzer(config, mock_llm_provider)

        # Convert documents to dict format
        doc_dicts = [{"id": d.id, "title": d.metadata.title, "content": d.content}
                     for d in sample_documents]

        # Call without mode parameter (should default to 'full')
        gaps = analyzer.analyze_gaps(doc_dicts, sample_concepts, sample_relations)

        # Should return gaps
        assert isinstance(gaps, list)

    def test_full_mode_explicit(self, config, mock_llm_provider, sample_documents, sample_concepts,
                                sample_relations):
        """Test explicit full mode."""
        analyzer = GapAnalyzer(config, mock_llm_provider)

        doc_dicts = [{"id": d.id, "title": d.metadata.title, "content": d.content}
                     for d in sample_documents]

        gaps = analyzer.analyze_gaps(doc_dicts, sample_concepts, sample_relations, mode='full')

        # Should return gaps
        assert isinstance(gaps, list)

    def test_incremental_mode(self, config, mock_llm_provider, sample_documents, sample_concepts,
                             sample_relations):
        """Test incremental mode."""
        analyzer = GapAnalyzer(config, mock_llm_provider)

        doc_dicts = [{"id": d.id, "title": d.metadata.title, "content": d.content}
                     for d in sample_documents]

        gaps = analyzer.analyze_gaps(doc_dicts, sample_concepts, sample_relations, mode='incremental')

        # Should return gaps
        assert isinstance(gaps, list)

    def test_hybrid_mode_small_batch(self, config, mock_llm_provider, sample_documents, sample_concepts,
                                    sample_relations):
        """Test hybrid mode with small batch."""
        analyzer = GapAnalyzer(config, mock_llm_provider)

        doc_dicts = [{"id": d.id, "title": d.metadata.title, "content": d.content}
                     for d in sample_documents]

        gaps = analyzer.analyze_gaps(doc_dicts, sample_concepts, sample_relations, mode='hybrid')

        # Should return gaps
        assert isinstance(gaps, list)

    def test_invalid_mode(self, config, mock_llm_provider, sample_documents, sample_concepts,
                         sample_relations):
        """Test that invalid mode raises ValueError."""
        analyzer = GapAnalyzer(config, mock_llm_provider)

        doc_dicts = [{"id": d.id, "title": d.metadata.title, "content": d.content}
                     for d in sample_documents]

        with pytest.raises(ValueError, match="Unknown mode"):
            analyzer.analyze_gaps(doc_dicts, sample_concepts, sample_relations, mode='invalid')


class TestInsightGeneratorModes:
    """Tests for InsightGenerator mode parameter."""

    def test_full_mode_default(self, config, sample_relations, sample_patterns, sample_gaps):
        """Test that full mode is the default behavior."""
        generator = InsightGenerator(config, Mock())

        # Call without mode parameter (should default to 'full')
        insights = generator.generate_insights(sample_relations, sample_patterns, sample_gaps)

        # Should return insights
        assert isinstance(insights, list)

    def test_full_mode_explicit(self, config, sample_relations, sample_patterns, sample_gaps):
        """Test explicit full mode."""
        generator = InsightGenerator(config, Mock())

        insights = generator.generate_insights(
            sample_relations, sample_patterns, sample_gaps, mode='full'
        )

        # Should return insights
        assert isinstance(insights, list)

    def test_incremental_mode(self, config, sample_relations, sample_patterns, sample_gaps):
        """Test incremental mode."""
        generator = InsightGenerator(config, Mock())

        insights = generator.generate_insights(
            sample_relations, sample_patterns, sample_gaps, mode='incremental'
        )

        # Should return insights
        assert isinstance(insights, list)

    def test_hybrid_mode_small_batch(self, config, sample_relations, sample_patterns, sample_gaps):
        """Test hybrid mode with small batch."""
        generator = InsightGenerator(config, Mock())

        insights = generator.generate_insights(
            sample_relations, sample_patterns, sample_gaps, mode='hybrid'
        )

        # Should return insights
        assert isinstance(insights, list)

    def test_invalid_mode(self, config, sample_relations, sample_patterns, sample_gaps):
        """Test that invalid mode raises ValueError."""
        generator = InsightGenerator(config, Mock())

        with pytest.raises(ValueError, match="Unknown mode"):
            generator.generate_insights(
                sample_relations, sample_patterns, sample_gaps, mode='invalid'
            )
