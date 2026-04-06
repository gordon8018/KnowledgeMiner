"""
End-to-end integration tests for knowledge discovery pipeline.

Tests the complete workflow from documents to insights, including:
- Complete discovery pipeline
- All component integration
- Edge cases and error handling
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import List
from src.discovery.engine import KnowledgeDiscoveryEngine
from src.discovery.interactive import InteractiveDiscovery
from src.discovery.config import DiscoveryConfig
from src.discovery.models.result import DiscoveryResult
from src.discovery.models.pattern import Pattern, PatternType
from src.discovery.models.gap import KnowledgeGap, GapType
from src.discovery.models.insight import Insight, InsightType
from src.core.document_model import EnhancedDocument, DocumentMetadata, SourceType
from src.core.concept_model import EnhancedConcept, ConceptType
from src.core.relation_model import Relation, RelationType


@pytest.fixture
def comprehensive_config():
    """Comprehensive configuration for all features."""
    return DiscoveryConfig(
        enable_explicit_mining=True,
        enable_implicit_mining=True,
        enable_statistical_mining=True,
        enable_semantic_mining=True,
        enable_pattern_detection=True,
        enable_gap_analysis=True,
        enable_insight_generation=True,
        max_insights=10,
        confidence_threshold=0.5
    )


@pytest.fixture
def sample_documents() -> List[EnhancedDocument]:
    """Create sample documents representing a financial knowledge domain."""
    return [
        EnhancedDocument(
            id="doc1",
            source_type=SourceType.MARKDOWN,
            content="利率上升会导致股市下跌。当央行提高利率时，企业融资成本增加，股票估值下降。",
            metadata=DocumentMetadata(
                title="利率与股市关系",
                file_path="finance1.md",
                created_at=datetime(2024, 1, 1)
            ),
            concepts=[],
            relations=[]
        ),
        EnhancedDocument(
            id="doc2",
            source_type=SourceType.MARKDOWN,
            content="通胀压力下，央行倾向于加息。通胀过高会降低购买力，需要通过货币政策控制。",
            metadata=DocumentMetadata(
                title="通胀与利率",
                file_path="finance2.md",
                created_at=datetime(2024, 1, 2)
            ),
            concepts=[],
            relations=[]
        ),
        EnhancedDocument(
            id="doc3",
            source_type=SourceType.MARKDOWN,
            content="经济增长放缓时，央行可能降息刺激经济。低利率环境有利于股市上涨。",
            metadata=DocumentMetadata(
                title="经济周期与利率",
                file_path="finance3.md",
                created_at=datetime(2024, 1, 3)
            ),
            concepts=[],
            relations=[]
        )
    ]


@pytest.fixture
def sample_concepts() -> List[EnhancedConcept]:
    """Create sample concepts."""
    return [
        EnhancedConcept(
            id="c1",
            name="利率",
            type=ConceptType.TERM,
            definition="资金价格",
            importance=0.9
        ),
        EnhancedConcept(
            id="c2",
            name="股市",
            type=ConceptType.TERM,
            definition="股票交易市场",
            importance=0.8
        ),
        EnhancedConcept(
            id="c3",
            name="通胀",
            type=ConceptType.TERM,
            definition="物价上涨",
            importance=0.7
        ),
        EnhancedConcept(
            id="c4",
            name="央行",
            type=ConceptType.THEORY,
            definition="中央银行",
            importance=0.85
        ),
        EnhancedConcept(
            id="c5",
            name="经济增长",
            type=ConceptType.THEORY,
            definition="经济总量增加",
            importance=0.75
        )
    ]


@pytest.fixture
def existing_relations() -> List[Relation]:
    """Create some existing relations."""
    return [
        Relation(
            id="r1",
            source_concept="利率",
            target_concept="股市",
            relation_type=RelationType.RELATED_TO,
            strength=0.7,
            confidence=0.8
        ),
        Relation(
            id="r2",
            source_concept="通胀",
            target_concept="利率",
            relation_type=RelationType.CAUSES,
            strength=0.8,
            confidence=0.85
        )
    ]


@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses for various discovery tasks."""
    return {
        'relation_extraction': [
            {
                "source": "利率",
                "target": "股市",
                "relation_type": "INFLUENCES",
                "confidence": 0.8,
                "evidence": "利率上升会导致股市下跌"
            },
            {
                "source": "通胀",
                "target": "利率",
                "relation_type": "CAUSES",
                "confidence": 0.85,
                "evidence": "通胀压力下，央行倾向于加息"
            }
        ],
        'pattern_detection': {
            "patterns": [
                {
                    "type": "TEMPORAL",
                    "description": "利率与股市的负相关关系",
                    "confidence": 0.75
                }
            ]
        },
        'gap_analysis': {
            "gaps": [
                {
                    "type": "MISSING_RELATION",
                    "description": "缺少经济增长对股市的直接影响研究",
                    "priority": 8
                }
            ]
        },
        'insight_generation': {
            "insights": [
                {
                    "type": "RELATIONSHIP",
                    "summary": "利率、通胀与股市形成三角关系",
                    "novelty": 0.8,
                    "impact": 0.9,
                    "actionability": 0.7
                }
            ]
        }
    }


class TestEndToEndDiscovery:
    """Test complete end-to-end discovery pipeline."""

    def test_complete_discovery_pipeline(self, comprehensive_config,
                                       sample_documents, sample_concepts):
        """Test complete discovery pipeline from documents to insights."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            # Setup mocks
            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            # Verify result structure
            assert isinstance(result, DiscoveryResult)
            assert hasattr(result, 'relations')
            assert hasattr(result, 'patterns')
            assert hasattr(result, 'gaps')
            assert hasattr(result, 'insights')
            assert hasattr(result, 'statistics')
            assert hasattr(result, 'generated_at')

            # Verify statistics
            assert 'total_relations' in result.statistics
            assert 'total_patterns' in result.statistics
            assert 'total_gaps' in result.statistics
            assert 'total_insights' in result.statistics
            assert 'avg_insight_significance' in result.statistics

            # Verify timestamps
            assert isinstance(result.generated_at, datetime)

    def test_discovery_with_existing_relations(self, comprehensive_config,
                                             sample_documents, sample_concepts,
                                             existing_relations):
        """Test discovery pipeline with pre-existing relations."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(
                sample_documents, sample_concepts, existing_relations
            )

            # Should include existing relations
            assert len(result.relations) >= len(existing_relations)

            # Verify existing relations are preserved
            relation_ids = [r.id for r in result.relations]
            assert existing_relations[0].id in relation_ids
            assert existing_relations[1].id in relation_ids

    def test_discovery_with_empty_inputs(self, comprehensive_config):
        """Test discovery with minimal inputs."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover([], [])

            # Should handle empty inputs gracefully
            assert isinstance(result, DiscoveryResult)
            assert len(result.relations) == 0
            assert len(result.patterns) == 0
            assert len(result.gaps) == 0
            assert len(result.insights) == 0

    def test_discovery_with_partial_configuration(self, sample_documents,
                                                 sample_concepts):
        """Test discovery with only some components enabled."""
        config = DiscoveryConfig(
            enable_explicit_mining=True,
            enable_implicit_mining=False,
            enable_statistical_mining=False,
            enable_semantic_mining=False,
            enable_pattern_detection=True,
            enable_gap_analysis=False,
            enable_insight_generation=True,
            max_insights=5
        )

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(config)
            result = engine.discover(sample_documents, sample_concepts)

            # Should only generate enabled components
            assert isinstance(result, DiscoveryResult)
            assert len(result.insights) <= config.max_insights


class TestComponentIntegration:
    """Test integration between components."""

    def test_relation_to_pattern_integration(self, comprehensive_config,
                                            sample_documents, sample_concepts):
        """Test that mined relations feed into pattern detection."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            # Patterns should be detected based on relations
            # (actual pattern detection logic is tested in unit tests)
            assert isinstance(result.patterns, list)

    def test_pattern_to_insight_integration(self, comprehensive_config,
                                          sample_documents, sample_concepts):
        """Test that detected patterns inform insight generation."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            # Insights should be generated based on patterns
            assert isinstance(result.insights, list)

    def test_gap_to_insight_integration(self, comprehensive_config,
                                      sample_documents, sample_concepts):
        """Test that identified gaps inform insight generation."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            # Insights should address gaps
            assert isinstance(result.gaps, list)
            assert isinstance(result.insights, list)


class TestErrorHandling:
    """Test error handling in edge cases."""

    def test_malformed_document_handling(self, comprehensive_config,
                                       sample_concepts):
        """Test handling of malformed documents."""
        malformed_docs = [
            EnhancedDocument(
                id="bad_doc",
                source_type=SourceType.MARKDOWN,
                content="",  # Empty content
                metadata=DocumentMetadata(title="Bad", file_path="bad.md"),
                concepts=[],
                relations=[]
            )
        ]

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)

            # Should not crash, handle gracefully
            result = engine.discover(malformed_docs, sample_concepts)
            assert isinstance(result, DiscoveryResult)

    def test_duplicate_relation_handling(self, comprehensive_config,
                                        sample_documents, sample_concepts,
                                        existing_relations):
        """Test handling of duplicate relations."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(
                sample_documents, sample_concepts, existing_relations
            )

            # Should handle duplicates (deduplication logic in components)
            assert isinstance(result.relations, list)

    def test_large_document_set_handling(self, comprehensive_config):
        """Test handling of large document sets."""
        # Create 100 documents
        large_doc_set = [
            EnhancedDocument(
                id=f"doc_{i}",
                source_type=SourceType.MARKDOWN,
                content=f"这是第{i}个文档的内容",
                metadata=DocumentMetadata(
                    title=f"Document {i}",
                    file_path=f"doc_{i}.md"
                ),
                concepts=[],
                relations=[]
            )
            for i in range(100)
        ]

        large_concept_set = [
            EnhancedConcept(
                id=f"c{i}",
                name=f"概念{i}",
                type=ConceptType.TERM,
                definition=f"定义{i}"
            )
            for i in range(50)
        ]

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)

            # Should handle large sets without crashing
            result = engine.discover(large_doc_set, large_concept_set)
            assert isinstance(result, DiscoveryResult)


class TestInteractiveAPI:
    """Test interactive discovery API."""

    def test_interactive_discovery_initialization(self, comprehensive_config,
                                                 sample_documents, sample_concepts):
        """Test InteractiveDiscovery initialization."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            interactive = InteractiveDiscovery(engine)

            assert hasattr(interactive, 'engine')
            assert interactive.engine == engine

    def test_explore_relations_method(self, comprehensive_config,
                                     sample_documents, sample_concepts):
        """Test explore_relations interactive method."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            interactive = InteractiveDiscovery(engine)
            interactive._last_result = result

            # Test relation exploration
            relations = interactive.explore_relations("利率")
            assert isinstance(relations, list)

    def test_find_patterns_method(self, comprehensive_config,
                                 sample_documents, sample_concepts):
        """Test find_patterns interactive method."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            interactive = InteractiveDiscovery(engine)
            interactive._last_result = result

            # Test pattern finding
            patterns = interactive.find_patterns("利率")
            assert isinstance(patterns, list)

    def test_get_top_insights_method(self, comprehensive_config,
                                    sample_documents, sample_concepts):
        """Test get_top_insights interactive method."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            interactive = InteractiveDiscovery(engine)
            interactive._last_result = result

            # Test top insights retrieval
            top_insights = interactive.get_top_insights(n=3)
            assert isinstance(top_insights, list)
            assert len(top_insights) <= 3

    def test_analyze_gaps_in_domain_method(self, comprehensive_config,
                                         sample_documents, sample_concepts):
        """Test analyze_gaps_in_domain interactive method."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            interactive = InteractiveDiscovery(engine)
            interactive._last_result = result

            # Test domain-specific gap analysis
            gaps = interactive.analyze_gaps_in_domain("finance")
            assert isinstance(gaps, list)


class TestResultValidation:
    """Test validation of discovery results."""

    def test_result_immutability(self, comprehensive_config,
                                sample_documents, sample_concepts):
        """Test that discovery results are immutable."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result1 = engine.discover(sample_documents, sample_concepts)
            result2 = engine.discover(sample_documents, sample_concepts)

            # Results should be independent
            assert result1 is not result2

    def test_statistics_accuracy(self, comprehensive_config,
                               sample_documents, sample_concepts):
        """Test accuracy of computed statistics."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)
            result = engine.discover(sample_documents, sample_concepts)

            # Verify statistics match actual counts
            assert result.statistics['total_relations'] == len(result.relations)
            assert result.statistics['total_patterns'] == len(result.patterns)
            assert result.statistics['total_gaps'] == len(result.gaps)
            assert result.statistics['total_insights'] == len(result.insights)

            # Verify average insight significance
            if result.insights:
                expected_avg = sum(i.significance for i in result.insights) / len(result.insights)
                assert abs(result.statistics['avg_insight_significance'] - expected_avg) < 0.01


class TestConfigurationOptions:
    """Test various configuration options."""

    def test_minimal_configuration(self, sample_documents, sample_concepts):
        """Test with minimal configuration (only essential features)."""
        config = DiscoveryConfig(
            enable_explicit_mining=True,
            max_insights=3
        )

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(config)
            result = engine.discover(sample_documents, sample_concepts)

            assert isinstance(result, DiscoveryResult)
            assert len(result.insights) <= 3

    def test_high_confidence_threshold(self, sample_documents, sample_concepts):
        """Test with high confidence threshold."""
        config = DiscoveryConfig(
            confidence_threshold=0.9,
            enable_explicit_mining=True
        )

        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(config)
            result = engine.discover(sample_documents, sample_concepts)

            # High threshold should filter out low-confidence results
            assert isinstance(result, DiscoveryResult)


class TestIncrementalDiscovery:
    """Test incremental discovery scenarios."""

    def test_incremental_document_addition(self, comprehensive_config,
                                         sample_documents, sample_concepts):
        """Test discovery when documents are added incrementally."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)

            # Initial discovery with subset
            initial_docs = sample_documents[:2]
            result1 = engine.discover(initial_docs, sample_concepts)

            # Incremental discovery with more documents
            result2 = engine.discover(sample_documents, sample_concepts)

            # More documents should potentially yield more insights
            assert isinstance(result1, DiscoveryResult)
            assert isinstance(result2, DiscoveryResult)

    def test_incremental_concept_addition(self, comprehensive_config,
                                        sample_documents, sample_concepts):
        """Test discovery when concepts are added incrementally."""
        with patch('src.discovery.engine.LLMProvider') as mock_llm, \
             patch('src.discovery.engine.EmbeddingGenerator') as mock_embedder:

            mock_llm.return_value = MagicMock()
            mock_embedder.return_value = MagicMock()

            engine = KnowledgeDiscoveryEngine(comprehensive_config)

            # Initial discovery with subset
            initial_concepts = sample_concepts[:3]
            result1 = engine.discover(sample_documents, initial_concepts)

            # Incremental discovery with more concepts
            result2 = engine.discover(sample_documents, sample_concepts)

            assert isinstance(result1, DiscoveryResult)
            assert isinstance(result2, DiscoveryResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])