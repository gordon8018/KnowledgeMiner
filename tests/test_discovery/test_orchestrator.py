"""
Tests for DiscoveryOrchestrator and WikiIntegrator components.

Tests the orchestration of the discovery pipeline and transaction-safe
integration with Wiki.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from src.discovery.engine import KnowledgeDiscoveryEngine
from src.discovery.models.result import DiscoveryResult
from src.discovery.models.pattern import Pattern, PatternType
from src.discovery.models.gap import KnowledgeGap, GapType
from src.discovery.models.insight import Insight, InsightType
from src.core.relation_model import Relation, RelationType
from src.core.concept_model import EnhancedConcept
from src.core.document_model import EnhancedDocument


@pytest.fixture
def mock_discovery_engine():
    """Create a mock KnowledgeDiscoveryEngine."""
    engine = Mock(spec=KnowledgeDiscoveryEngine)
    return engine


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    from src.core.base_models import SourceType
    from src.core.document_model import DocumentMetadata

    return [
        EnhancedDocument(
            id="doc1",
            source_type=SourceType.MARKDOWN,
            content="Content about machine learning and neural networks",
            metadata=DocumentMetadata(
                title="Test Document 1",
                file_path="test.md"
            )
        ),
        EnhancedDocument(
            id="doc2",
            source_type=SourceType.MARKDOWN,
            content="Content about deep learning and transformers",
            metadata=DocumentMetadata(
                title="Test Document 2",
                file_path="test2.md"
            )
        )
    ]


@pytest.fixture
def sample_concepts():
    """Create sample concepts for testing."""
    return [
        EnhancedConcept(
            id="concept1",
            name="Machine Learning",
            type="term",
            definition="A subset of AI",
            confidence=0.9
        ),
        EnhancedConcept(
            id="concept2",
            name="Neural Networks",
            type="term",
            definition="Computing systems inspired by biological neural networks",
            confidence=0.85
        )
    ]


@pytest.fixture
def sample_relations():
    """Create sample relations for testing."""
    return [
        Relation(
            id="rel1",
            source_concept="Machine Learning",
            target_concept="Neural Networks",
            relation_type=RelationType.CONTAINS,
            strength=0.8,
            confidence=0.9
        )
    ]


@pytest.fixture
def sample_patterns():
    """Create sample patterns for testing."""
    from src.discovery.models.pattern import Evidence

    return [
        Pattern(
            id="pattern1",
            pattern_type=PatternType.TEMPORAL,
            title="Seasonal Pattern",
            description="Recurring pattern in data",
            confidence=0.75,
            significance_score=0.8,
            related_concepts=["Machine Learning"],
            related_patterns=[],
            evidence=[Evidence(source_id="doc1", content="Pattern evidence", confidence=0.8)],
            metadata={},
            detected_at=datetime.now()
        )
    ]


@pytest.fixture
def sample_gaps():
    """Create sample knowledge gaps for testing."""
    return [
        KnowledgeGap(
            id="gap1",
            gap_type=GapType.MISSING_CONCEPT,
            description="Missing concept: Deep Learning",
            severity=0.7,
            affected_concepts=["Machine Learning"],
            affected_relations=[],
            suggested_actions=["Add Deep Learning concept"],
            priority=5,
            estimated_effort="low",
            metadata={},
            detected_at=datetime.now()
        )
    ]


@pytest.fixture
def sample_insights():
    """Create sample insights for testing."""
    return [
        Insight(
            id="insight1",
            insight_type=InsightType.PATTERN,
            title="Pattern Insight",
            description="Important pattern detected",
            significance=0.8,
            related_concepts=["Machine Learning"],
            related_patterns=[],
            related_gaps=[],
            evidence=[],
            actionable_suggestions=["Monitor this pattern"],
            generated_at=datetime.now(),
            metadata={}
        )
    ]


@pytest.fixture
def sample_discovery_result(sample_relations, sample_patterns, sample_gaps, sample_insights):
    """Create a complete DiscoveryResult for testing."""
    return DiscoveryResult(
        relations=sample_relations,
        patterns=sample_patterns,
        gaps=sample_gaps,
        insights=sample_insights,
        statistics={
            'total_relations': 1,
            'total_patterns': 1,
            'total_gaps': 1,
            'total_insights': 1
        },
        generated_at=datetime.now()
    )


class TestDiscoveryOrchestrator:
    """Test suite for DiscoveryOrchestrator."""

    def test_orchestrator_initialization(self, mock_discovery_engine):
        """Test that DiscoveryOrchestrator can be initialized."""
        from src.wiki.discovery.orchestrator import DiscoveryOrchestrator
        from src.discovery.config import DiscoveryConfig

        # Setup mock with config
        mock_discovery_engine.config = DiscoveryConfig()

        orchestrator = DiscoveryOrchestrator(
            discovery_engine=mock_discovery_engine
        )

        assert orchestrator.discovery_engine == mock_discovery_engine
        assert orchestrator.integrator is not None

    def test_orchestrate_discovery(
        self,
        mock_discovery_engine,
        sample_documents,
        sample_concepts,
        sample_discovery_result
    ):
        """Test full orchestration of discovery pipeline."""
        from src.wiki.discovery.orchestrator import DiscoveryOrchestrator
        from src.discovery.config import DiscoveryConfig

        # Setup mock
        mock_discovery_engine.config = DiscoveryConfig()
        mock_discovery_engine.discover.return_value = sample_discovery_result

        orchestrator = DiscoveryOrchestrator(
            discovery_engine=mock_discovery_engine
        )

        # Execute orchestration
        result = orchestrator.orchestrate(
            documents=sample_documents,
            concepts=sample_concepts,
            mode='full'
        )

        # Verify
        assert result is not None
        assert isinstance(result, DiscoveryResult)
        assert len(result.relations) == 1
        assert len(result.patterns) == 1
        assert len(result.gaps) == 1
        assert len(result.insights) == 1

        # Verify discovery engine was called correctly
        mock_discovery_engine.discover.assert_called_once()

    def test_orchestrate_with_incremental_mode(
        self,
        mock_discovery_engine,
        sample_documents,
        sample_concepts,
        sample_discovery_result
    ):
        """Test orchestration in incremental mode."""
        from src.wiki.discovery.orchestrator import DiscoveryOrchestrator
        from src.discovery.config import DiscoveryConfig

        # Setup mock
        mock_discovery_engine.config = DiscoveryConfig()
        mock_discovery_engine.discover.return_value = sample_discovery_result

        orchestrator = DiscoveryOrchestrator(
            discovery_engine=mock_discovery_engine
        )

        # Execute orchestration with incremental mode
        result = orchestrator.orchestrate(
            documents=sample_documents,
            concepts=sample_concepts,
            mode='incremental'
        )

        # Verify
        assert result is not None
        assert result.statistics['mode'] == 'incremental'

    def test_orchestrate_with_hybrid_mode(
        self,
        mock_discovery_engine,
        sample_documents,
        sample_concepts,
        sample_discovery_result
    ):
        """Test orchestration in hybrid mode."""
        from src.wiki.discovery.orchestrator import DiscoveryOrchestrator
        from src.discovery.config import DiscoveryConfig

        # Setup mock
        mock_discovery_engine.config = DiscoveryConfig()
        mock_discovery_engine.discover.return_value = sample_discovery_result

        orchestrator = DiscoveryOrchestrator(
            discovery_engine=mock_discovery_engine
        )

        # Execute orchestration with hybrid mode
        result = orchestrator.orchestrate(
            documents=sample_documents,
            concepts=sample_concepts,
            mode='hybrid'
        )

        # Verify
        assert result is not None
        assert result.statistics['mode'] == 'hybrid'


class TestWikiIntegrator:
    """Test suite for WikiIntegrator."""

    def test_integrator_initialization(self):
        """Test that WikiIntegrator can be initialized."""
        from src.wiki.discovery.integrator import WikiIntegrator
        from pathlib import Path

        integrator = WikiIntegrator(wiki_path="/tmp/test_wiki")

        assert integrator.wiki_path == Path("/tmp/test_wiki")
        assert integrator.pending_changes == []
        assert integrator.committed_changes == []

    def test_transaction_safe_integration(
        self,
        sample_relations,
        sample_patterns,
        sample_gaps,
        sample_insights,
        tmp_path
    ):
        """Test transaction-safe integration of discovery results."""
        from src.wiki.discovery.integrator import WikiIntegrator

        integrator = WikiIntegrator(wiki_path=str(tmp_path))

        # Execute integration
        result = integrator.integrate(
            relations=sample_relations,
            patterns=sample_patterns,
            gaps=sample_gaps,
            insights=sample_insights
        )

        # Verify success
        assert result['success'] is True
        assert result['changes_applied'] > 0
        assert len(integrator.committed_changes) > 0

    def test_integrator_error_handling(
        self,
        sample_relations,
        tmp_path
    ):
        """Test error handling in WikiIntegrator."""
        from src.wiki.discovery.integrator import WikiIntegrator

        integrator = WikiIntegrator(wiki_path=str(tmp_path))

        # Mock a failure scenario by providing invalid data
        with patch.object(integrator, '_prepare_relation_changes', side_effect=Exception("Test error")):
            result = integrator.integrate(
                relations=sample_relations,
                patterns=[],
                gaps=[],
                insights=[]
            )

            # Verify error was handled gracefully
            assert result['success'] is False
            assert 'error' in result
            assert len(integrator.committed_changes) == 0  # No changes committed

    def test_integrator_rollback_on_failure(
        self,
        sample_relations,
        sample_patterns,
        tmp_path
    ):
        """Test rollback mechanism when integration fails."""
        from src.wiki.discovery.integrator import WikiIntegrator

        integrator = WikiIntegrator(wiki_path=str(tmp_path))

        # Mock a failure during apply_changes
        def mock_apply_changes(changes):
            raise Exception("Simulated failure during apply")

        with patch.object(integrator, '_apply_changes', side_effect=mock_apply_changes):
            result = integrator.integrate(
                relations=sample_relations,
                patterns=sample_patterns,
                gaps=[],
                insights=[]
            )

            # Verify rollback occurred
            assert result['success'] is False
            assert 'error' in result
            assert 'Simulated failure' in result['error']

    def test_prepare_relation_changes(self, sample_relations, tmp_path):
        """Test preparing relation changes for integration."""
        from src.wiki.discovery.integrator import WikiIntegrator

        integrator = WikiIntegrator(wiki_path=str(tmp_path))

        changes = integrator._prepare_relation_changes(sample_relations)

        assert len(changes) == len(sample_relations)
        assert all('type' in change for change in changes)
        assert all('data' in change for change in changes)

    def test_prepare_pattern_changes(self, sample_patterns, tmp_path):
        """Test preparing pattern changes for integration."""
        from src.wiki.discovery.integrator import WikiIntegrator

        integrator = WikiIntegrator(wiki_path=str(tmp_path))

        changes = integrator._prepare_pattern_changes(sample_patterns)

        assert len(changes) == len(sample_patterns)
        assert all('type' in change for change in changes)

    def test_prepare_gap_changes(self, sample_gaps, tmp_path):
        """Test preparing gap changes for integration."""
        from src.wiki.discovery.integrator import WikiIntegrator

        integrator = WikiIntegrator(wiki_path=str(tmp_path))

        changes = integrator._prepare_gap_changes(sample_gaps)

        assert len(changes) == len(sample_gaps)
        assert all('type' in change for change in changes)

    def test_prepare_insight_changes(self, sample_insights, tmp_path):
        """Test preparing insight changes for integration."""
        from src.wiki.discovery.integrator import WikiIntegrator

        integrator = WikiIntegrator(wiki_path=str(tmp_path))

        changes = integrator._prepare_insight_changes(sample_insights)

        assert len(changes) == len(sample_insights)
        assert all('type' in change for change in changes)

    def test_atomic_change_application(self, tmp_path):
        """Test that changes are applied atomically."""
        from src.wiki.discovery.integrator import WikiIntegrator

        integrator = WikiIntegrator(wiki_path=str(tmp_path))

        changes = [
            {'type': 'create_page', 'path': 'test1.md', 'content': 'content1'},
            {'type': 'create_page', 'path': 'test2.md', 'content': 'content2'},
        ]

        # Apply changes
        result = integrator._apply_changes(changes)

        # Verify all changes were applied
        assert result['success'] is True
        assert result['changes_applied'] == 2

        # Verify files exist
        assert (tmp_path / 'test1.md').exists()
        assert (tmp_path / 'test2.md').exists()

    def test_statistics_tracking(
        self,
        sample_relations,
        sample_patterns,
        sample_gaps,
        sample_insights,
        tmp_path
    ):
        """Test that integration statistics are tracked correctly."""
        from src.wiki.discovery.integrator import WikiIntegrator

        integrator = WikiIntegrator(wiki_path=str(tmp_path))

        result = integrator.integrate(
            relations=sample_relations,
            patterns=sample_patterns,
            gaps=sample_gaps,
            insights=sample_insights
        )

        # Verify statistics
        assert 'statistics' in result
        stats = result['statistics']
        assert 'relations_added' in stats
        assert 'patterns_added' in stats
        assert 'gaps_added' in stats
        assert 'insights_added' in stats
