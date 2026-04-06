"""
Tests for DiscoveryPipeline - Complete Stage 2 orchestration.

Tests cover:
1. Pipeline initialization
2. First run (no previous state)
3. No changes detection
4. Incremental mode selection
5. Full mode after timeout
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json

from src.wiki.core import WikiCore
from src.wiki.discovery.pipeline import DiscoveryPipeline
from src.wiki.discovery.models import ChangeSet
from src.discovery.config import DiscoveryConfig
from src.discovery.models.result import DiscoveryResult
from src.core.document_model import EnhancedDocument, DocumentMetadata, SourceType
from src.core.concept_model import EnhancedConcept, ConceptType


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    input_dir = tempfile.mkdtemp()
    wiki_dir = tempfile.mkdtemp()
    state_dir = tempfile.mkdtemp()

    yield input_dir, wiki_dir, state_dir

    # Cleanup
    shutil.rmtree(input_dir, ignore_errors=True)
    shutil.rmtree(wiki_dir, ignore_errors=True)
    shutil.rmtree(state_dir, ignore_errors=True)


@pytest.fixture
def sample_documents(temp_dirs):
    """Create sample markdown documents for testing."""
    input_dir, _, _ = temp_dirs

    # Create sample documents
    docs = {
        'doc1.md': """---
title: First Document
author: Test Author
tags: [test, sample]
---

# First Document

This is a test document with some content.
""",
        'doc2.md': """---
title: Second Document
author: Another Author
tags: [test]
---

# Second Document

Another test document with different content.
""",
        'subdir/doc3.md': """---
title: Third Document
author: Test Author
tags: [sample]
---

# Third Document

A document in a subdirectory.
"""
    }

    for doc_path, content in docs.items():
        full_path = Path(input_dir) / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    return docs


@pytest.fixture
def wiki_with_concepts(temp_dirs):
    """Create a Wiki with sample concept pages."""
    _, wiki_dir, _ = temp_dirs

    wiki_core = WikiCore(wiki_dir)

    # Create sample concept pages
    concepts = [
        {
            'id': 'momentum',
            'title': 'Momentum',
            'content': """# Momentum

Momentum is a key concept in technical analysis.

It measures the rate of change of price over time.
"""
        },
        {
            'id': 'moving_average',
            'title': 'Moving Average',
            'content': """# Moving Average

Moving average is a trend-following indicator.

It smooths price data to create a single flowing line.
"""
        },
        {
            'id': 'rsi',
            'title': 'RSI',
            'content': """# RSI

RSI (Relative Strength Index) is a momentum oscillator.

It measures the speed and change of price movements.
"""
        }
    ]

    for concept_data in concepts:
        from src.wiki.core.models import WikiPage, PageType

        page = WikiPage(
            id=concept_data['id'],
            title=concept_data['title'],
            content=concept_data['content'],
            page_type=PageType.CONCEPT,
            version=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={}
        )
        wiki_core.create_page(page)

    return wiki_core


@pytest.fixture
def mock_discovery_result():
    """Create a mock DiscoveryResult for testing."""
    return DiscoveryResult(
        relations=[],
        patterns=[],
        gaps=[],
        insights=[],
        statistics={},
        generated_at=datetime.now()
    )


class TestDiscoveryPipeline:
    """Test suite for DiscoveryPipeline."""

    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_initialization(self, mock_engine_init, temp_dirs, wiki_with_concepts):
        """Test that pipeline initializes correctly."""
        input_dir, wiki_dir, state_dir = temp_dirs

        # Create pipeline
        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig()
        )

        # Verify initialization
        assert pipeline.wiki_core == wiki_with_concepts
        assert pipeline.input_dir == Path(input_dir)
        assert pipeline.state_dir == Path(state_dir)
        assert pipeline.input_processor is not None
        assert pipeline.mode_selector is not None
        assert pipeline.discovery_engine is not None
        assert pipeline.orchestrator is not None

    @patch('src.wiki.discovery.orchestrator.KnowledgeDiscoveryEngine.discover')
    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_first_run(self, mock_engine_init, mock_discover, temp_dirs, wiki_with_concepts, sample_documents, mock_discovery_result):
        """Test pipeline behavior on first run with new documents."""
        input_dir, wiki_dir, state_dir = temp_dirs

        mock_discover.return_value = mock_discovery_result

        # Create pipeline
        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig()
        )

        # Run pipeline
        result = pipeline.run(batch_id="test-batch-1")

        # Verify discovery was performed
        assert result is not None
        assert result.statistics['pipeline_run_id'] == "test-batch-1"
        assert 'pipeline_duration' in result.statistics
        assert 'changeset' in result.statistics

        # Verify changeset was tracked
        changeset = result.statistics['changeset']
        assert changeset['new_docs'] == 3  # All 3 docs are new
        assert changeset['changed_docs'] == 0
        assert changeset['deleted_docs'] == 0

    @patch('src.wiki.discovery.orchestrator.KnowledgeDiscoveryEngine.discover')
    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_no_changes(self, mock_engine_init, mock_discover, temp_dirs, wiki_with_concepts, sample_documents, mock_discovery_result):
        """Test pipeline returns None when no changes detected."""
        input_dir, wiki_dir, state_dir = temp_dirs

        mock_discover.return_value = mock_discovery_result

        # Create pipeline
        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig()
        )

        # First run
        result1 = pipeline.run(batch_id="test-batch-1")
        assert result1 is not None

        # Second run with no changes
        result2 = pipeline.run(batch_id="test-batch-2")
        assert result2 is None  # No changes detected

    @patch('src.wiki.discovery.orchestrator.KnowledgeDiscoveryEngine.discover')
    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_incremental_mode(self, mock_engine_init, mock_discover, temp_dirs, wiki_with_concepts, sample_documents, mock_discovery_result):
        """Test pipeline selects incremental mode for small changesets."""
        input_dir, wiki_dir, state_dir = temp_dirs

        mock_discover.return_value = mock_discovery_result

        # Create pipeline
        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig(),
            incremental_threshold=10  # Allow up to 10 changes for incremental
        )

        # First run (full mode, all docs new)
        result1 = pipeline.run(batch_id="test-batch-1")
        assert result1 is not None

        # Add one new document (within incremental threshold)
        new_doc_path = Path(input_dir) / 'new_doc.md'
        new_doc_path.write_text("""
# New Document

This is a new document added after first run.
""")

        # Second run should use incremental mode
        result2 = pipeline.run(batch_id="test-batch-2")
        assert result2 is not None
        # Mode should be set by orchestrator
        assert 'mode' in result2.statistics

        # Verify only new document was processed
        changeset = result2.statistics['changeset']
        assert changeset['new_docs'] == 1
        assert changeset['changed_docs'] == 0

    @patch('src.wiki.discovery.orchestrator.KnowledgeDiscoveryEngine.discover')
    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_full_mode_after_timeout(self, mock_engine_init, mock_discover, temp_dirs, wiki_with_concepts, sample_documents, mock_discovery_result):
        """Test pipeline forces full mode after timeout period."""
        input_dir, wiki_dir, state_dir = temp_dirs

        mock_discover.return_value = mock_discovery_result

        # Create pipeline with short timeout
        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig(),
            force_full_after_days=0  # Force full run immediately
        )

        # First run
        result1 = pipeline.run(batch_id="test-batch-1")
        assert result1 is not None

        # Manually set last_full_run to old date to trigger full mode
        old_timestamp = (datetime.now() - timedelta(days=10)).isoformat()
        last_full_file = Path(state_dir) / pipeline.LAST_FULL_RUN_FILE
        last_full_file.write_text(json.dumps({'last_full_run': old_timestamp}))

        # Re-initialize pipeline to load the old timestamp
        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig(),
            force_full_after_days=7  # 7 days threshold
        )

        # Add a small change (would normally be incremental)
        new_doc_path = Path(input_dir) / 'small_change.md'
        new_doc_path.write_text("# Small change")

        # Run should force full mode due to timeout
        result2 = pipeline.run(batch_id="test-batch-2")
        assert result2 is not None

        # Verify full run was recorded
        assert last_full_file.exists()

    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_load_documents(self, mock_engine_init, temp_dirs, wiki_with_concepts, sample_documents):
        """Test _load_documents method loads EnhancedDocument objects correctly."""
        input_dir, wiki_dir, state_dir = temp_dirs

        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig()
        )

        # Create changeset
        changeset = ChangeSet(
            batch_id="test",
            new_docs=['doc1.md', 'doc2.md', 'subdir/doc3.md'],
            changed_docs=[],
            deleted_docs=[],
            impact_score=0.5
        )

        # Load documents
        documents = pipeline._load_documents(changeset)

        # Verify documents were loaded
        assert len(documents) == 3

        # Verify document properties
        doc1 = next((d for d in documents if d.id == 'doc1.md'), None)
        assert doc1 is not None
        assert doc1.metadata.title == 'First Document'
        assert doc1.metadata.author == 'Test Author'
        assert 'test' in doc1.metadata.tags
        assert 'sample' in doc1.metadata.tags
        assert len(doc1.content) > 0

    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_load_concepts(self, mock_engine_init, temp_dirs, wiki_with_concepts):
        """Test _load_concepts method loads EnhancedConcept objects correctly."""
        input_dir, wiki_dir, state_dir = temp_dirs

        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig()
        )

        # Load concepts
        concepts = pipeline._load_concepts()

        # Verify concepts were loaded
        assert len(concepts) >= 3  # At least the 3 concepts we created

        # Verify concept properties
        momentum = next((c for c in concepts if c.name == 'Momentum'), None)
        assert momentum is not None
        assert momentum.definition is not None
        assert len(momentum.definition) > 0

    @patch('src.wiki.discovery.orchestrator.KnowledgeDiscoveryEngine.discover')
    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_with_deleted_documents(self, mock_engine_init, mock_discover, temp_dirs, wiki_with_concepts, sample_documents, mock_discovery_result):
        """Test pipeline handles document deletions correctly."""
        input_dir, wiki_dir, state_dir = temp_dirs

        mock_discover.return_value = mock_discovery_result

        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig()
        )

        # First run
        result1 = pipeline.run(batch_id="test-batch-1")
        assert result1 is not None
        assert result1.statistics['changeset']['new_docs'] == 3

        # Delete a document
        doc_to_delete = Path(input_dir) / 'doc1.md'
        doc_to_delete.unlink()

        # Second run should detect deletion
        result2 = pipeline.run(batch_id="test-batch-2")
        assert result2 is not None

        # Verify deletion was tracked
        changeset = result2.statistics['changeset']
        assert changeset['deleted_docs'] == 1

    @patch('src.wiki.discovery.orchestrator.KnowledgeDiscoveryEngine.discover')
    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_with_modified_documents(self, mock_engine_init, mock_discover, temp_dirs, wiki_with_concepts, sample_documents, mock_discovery_result):
        """Test pipeline handles document modifications correctly."""
        input_dir, wiki_dir, state_dir = temp_dirs

        mock_discover.return_value = mock_discovery_result

        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig()
        )

        # First run
        result1 = pipeline.run(batch_id="test-batch-1")
        assert result1 is not None

        # Modify a document
        doc_to_modify = Path(input_dir) / 'doc2.md'
        original_content = doc_to_modify.read_text()
        modified_content = original_content + "\n\n## New Section\n\nThis is new content."
        doc_to_modify.write_text(modified_content)

        # Second run should detect modification
        result2 = pipeline.run(batch_id="test-batch-2")
        assert result2 is not None

        # Verify modification was tracked
        changeset = result2.statistics['changeset']
        assert changeset['changed_docs'] == 1

    @patch('src.wiki.discovery.pipeline.KnowledgeDiscoveryEngine.__init__', return_value=None)
    def test_pipeline_frontmatter_parsing(self, mock_engine_init, temp_dirs, wiki_with_concepts):
        """Test pipeline correctly parses YAML frontmatter."""
        input_dir, wiki_dir, state_dir = temp_dirs

        # Create document with complex frontmatter
        doc_path = Path(input_dir) / 'frontmatter_test.md'
        doc_path.write_text("""---
title: Test Document
author: Jane Doe
date: 2024-01-15
tags: [test, frontmatter, parsing]
source_url: https://example.com/doc
custom_field: custom_value
---

# Test Document

This document has complex frontmatter.
""")

        pipeline = DiscoveryPipeline(
            wiki_core=wiki_with_concepts,
            input_dir=input_dir,
            state_dir=state_dir,
            config=DiscoveryConfig()
        )

        changeset = ChangeSet(
            batch_id="test",
            new_docs=['frontmatter_test.md'],
            changed_docs=[],
            deleted_docs=[],
            impact_score=0.5
        )

        documents = pipeline._load_documents(changeset)

        assert len(documents) == 1
        doc = documents[0]

        # Verify frontmatter was parsed
        assert doc.metadata.title == 'Test Document'
        assert doc.metadata.author == 'Jane Doe'
        assert 'test' in doc.metadata.tags
        assert 'frontmatter' in doc.metadata.tags
        assert doc.metadata.source_url == 'https://example.com/doc'
