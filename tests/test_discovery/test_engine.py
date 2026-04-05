import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.discovery.engine import KnowledgeDiscoveryEngine
from src.discovery.config import DiscoveryConfig
from src.discovery.models.result import DiscoveryResult
from src.core.document_model import EnhancedDocument, DocumentMetadata, SourceType
from src.core.concept_model import EnhancedConcept, ConceptType


@pytest.fixture
def config():
    return DiscoveryConfig(
        enable_explicit_mining=True,
        enable_implicit_mining=False,
        max_insights=5
    )


@pytest.fixture
def mock_documents():
    return [
        EnhancedDocument(
            id="doc1",
            source_type=SourceType.MARKDOWN,
            content="利率上升导致股市下跌",
            metadata=DocumentMetadata(
                title="Test",
                file_path="test.md"
            ),
            concepts=[],
            relations=[]
        )
    ]


@pytest.fixture
def mock_concepts():
    return [
        EnhancedConcept(
            id="c1",
            name="利率",
            type=ConceptType.TERM,
            definition="资金价格"
        )
    ]


def test_knowledge_discovery_engine_discover(config, mock_documents, mock_concepts):
    with patch('src.discovery.engine.LLMProvider'), \
         patch('src.discovery.engine.EmbeddingGenerator'):

        engine = KnowledgeDiscoveryEngine(config)
        result = engine.discover(mock_documents, mock_concepts)

        assert isinstance(result, DiscoveryResult)
        assert len(result.relations) >= 0
        assert len(result.insights) <= config.max_insights
        assert result.statistics['total_relations'] >= 0


def test_knowledge_discovery_engine_statistics_computation(config, mock_documents, mock_concepts):
    with patch('src.discovery.engine.LLMProvider'), \
         patch('src.discovery.engine.EmbeddingGenerator'):

        engine = KnowledgeDiscoveryEngine(config)
        result = engine.discover(mock_documents, mock_concepts)

        assert 'total_relations' in result.statistics
        assert 'total_patterns' in result.statistics
        assert 'total_gaps' in result.statistics
        assert 'total_insights' in result.statistics
        assert 'avg_insight_significance' in result.statistics


def test_knowledge_discovery_engine_with_existing_relations(config, mock_documents, mock_concepts):
    from src.core.relation_model import Relation, RelationType

    with patch('src.discovery.engine.LLMProvider'), \
         patch('src.discovery.engine.EmbeddingGenerator'):

        existing_relation = Relation(
            id="r1",
            source_concept="利率",
            target_concept="通胀",
            relation_type=RelationType.CAUSES,
            strength=0.8,
            confidence=0.9
        )

        engine = KnowledgeDiscoveryEngine(config)
        result = engine.discover(mock_documents, mock_concepts, [existing_relation])

        assert len(result.relations) >= 1  # 至少包含已有关系
