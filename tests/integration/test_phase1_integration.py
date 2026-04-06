"""Integration tests for Phase 1 components.

Tests the integration of all Phase 1 components:
- Configuration system
- Data models (Document, Concept, Relation)
- LLM providers (Anthropic, OpenAI)
- Embedding generation
- State manager

This file tests that components work together correctly.
"""

import pytest
import tempfile
import json
import os
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import numpy as np

from src.core.config import Config, get_config
from src.core.document_model import EnhancedDocument, DocumentMetadata
from src.core.concept_model import EnhancedConcept, ConceptType, TemporalInfo
from src.core.relation_model import Relation, RelationType
from src.core.base_models import SourceType, ProcessingStatus
from src.integrations.llm_providers import AnthropicProvider, OpenAIProvider, get_llm_provider
from src.ml.embeddings import EmbeddingGenerator, EmbeddingCache
from src.core.state_manager import StateManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    config_content = """
knowledge_compiler:
  llm:
    provider: anthropic
    model: claude-sonnet-4-6
    temperature: 0.3
    max_tokens: 4096
    api_key_env: ANTHROPIC_API_KEY
  storage:
    raw_dir: ./test_raw
    wiki_dir: ./test_wiki
    cache_dir: ./test_cache
  processing:
    max_file_size: 10485760
    batch_size: 10
  quality:
    min_document_quality: 0.6
  logging:
    level: INFO
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_state_file():
    """Create a temporary state file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_document():
    """Create a sample document for testing"""
    metadata = DocumentMetadata(
        title="Test Document",
        author="Test Author",
        tags=["test", "sample"]
    )
    doc = EnhancedDocument(
        id="doc-001",
        source_type=SourceType.MARKDOWN,
        content="This is a test document with some content.",
        metadata=metadata,
        quality_score=0.8
    )
    return doc


@pytest.fixture
def sample_concept():
    """Create a sample concept for testing"""
    concept = EnhancedConcept(
        id="concept-001",
        name="Test Concept",
        type=ConceptType.TERM,
        definition="A concept for testing purposes",
        confidence=0.85
    )
    return concept


@pytest.fixture
def sample_relation():
    """Create a sample relation for testing"""
    relation = Relation(
        id="relation-001",
        source_concept="concept-001",
        target_concept="concept-002",
        relation_type=RelationType.RELATED_TO,
        strength=0.75,
        confidence=0.8
    )
    return relation


# ============================================================================
# Configuration Integration Tests
# ============================================================================

class TestConfigurationIntegration:
    """Test configuration system integration with other components"""

    def test_config_loading_and_access(self, temp_config_file):
        """Test that configuration can be loaded and accessed globally"""
        # Clear any existing config
        import src.core.config
        src.core.config._config = None

        # Load configuration
        config = get_config(temp_config_file)

        # Verify configuration is accessible
        assert config.llm.provider == "anthropic"
        assert config.llm.model == "claude-sonnet-4-6"
        assert config.storage.raw_dir == "./test_raw"
        assert config.processing.max_file_size == 10485760

    def test_config_environment_variable_override(self):
        """Test that environment variables override config file"""
        # Set environment variable
        os.environ["KC_LLM_MODEL"] = "claude-3-opus"
        os.environ["ANTHROPIC_API_KEY"] = "test-key-from-env"

        try:
            config = Config()
            assert config.llm.api_key == "test-key-from-env"
        finally:
            # Clean up
            os.environ.pop("KC_LLM_MODEL", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_config_to_dict_serialization(self, temp_config_file):
        """Test that configuration can be serialized to dict"""
        config = Config.from_yaml(temp_config_file)
        config_dict = config.to_dict()

        # Verify all sections are present
        assert "llm" in config_dict
        assert "storage" in config_dict
        assert "processing" in config_dict
        assert "quality" in config_dict
        assert "logging" in config_dict

        # Verify values are preserved
        assert config_dict["llm"]["provider"] == "anthropic"
        assert config_dict["storage"]["raw_dir"] == "./test_raw"


# ============================================================================
# Data Model Integration Tests
# ============================================================================

class TestDataModelIntegration:
    """Test data model integration and serialization"""

    def test_document_model_creation_and_serialization(self, sample_document):
        """Test document model can be created and serialized"""
        # Verify document was created correctly
        assert sample_document.id == "doc-001"
        assert sample_document.source_type == SourceType.MARKDOWN
        assert sample_document.quality_score == 0.8
        assert sample_document.metadata.title == "Test Document"

        # Test serialization
        doc_dict = sample_document.to_dict()
        assert doc_dict["id"] == "doc-001"
        assert doc_dict["source_type"] == "markdown"
        assert "created_at" in doc_dict
        assert "updated_at" in doc_dict

    def test_document_model_with_embeddings(self, sample_document):
        """Test document model with numpy array embeddings"""
        # Add embeddings
        embeddings = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        sample_document.embeddings = embeddings

        # Verify embeddings are stored
        assert sample_document.embeddings is not None
        assert isinstance(sample_document.embeddings, np.ndarray)
        assert sample_document.embeddings.shape == (4,)

        # Test serialization converts numpy to list
        doc_dict = sample_document.to_dict()
        assert "embeddings" in doc_dict
        assert isinstance(doc_dict["embeddings"], list)
        # Use approximate comparison for floating point
        assert len(doc_dict["embeddings"]) == 4
        assert all(abs(a - b) < 1e-6 for a, b in zip(doc_dict["embeddings"], [0.1, 0.2, 0.3, 0.4]))

    def test_document_concept_and_relation_tracking(self, sample_document):
        """Test document can track concepts and relations"""
        # Add concepts
        sample_document.add_concept("concept-001")
        sample_document.add_concept("concept-002")

        # Verify concepts were added
        assert "concept-001" in sample_document.concepts
        assert "concept-002" in sample_document.concepts
        assert len(sample_document.concepts) == 2

        # Add relation
        sample_document.add_relation("relation-001")
        assert "relation-001" in sample_document.relations

        # Verify duplicate is ignored
        sample_document.add_concept("concept-001")
        assert sample_document.concepts.count("concept-001") == 1

    def test_concept_model_creation_and_methods(self, sample_concept):
        """Test concept model creation and methods"""
        # Verify concept was created correctly
        assert sample_concept.id == "concept-001"
        assert sample_concept.name == "Test Concept"
        assert sample_concept.type == ConceptType.TERM
        assert sample_concept.confidence == 0.85

        # Test adding evidence
        sample_concept.add_evidence("doc-001", "Supporting quote", 0.9)
        assert len(sample_concept.evidence) == 1
        assert sample_concept.evidence[0]["source"] == "doc-001"

        # Test adding source document
        sample_concept.add_source_document("doc-001")
        sample_concept.add_source_document("doc-002")
        assert "doc-001" in sample_concept.source_documents
        assert "doc-002" in sample_concept.source_documents

        # Test confidence update
        sample_concept.update_confidence(0.95)
        assert sample_concept.confidence == 0.95

    def test_concept_model_with_embeddings(self):
        """Test concept model with embeddings"""
        concept = EnhancedConcept(
            id="concept-002",
            name="Embedding Concept",
            type=ConceptType.INDICATOR,
            definition="Concept with embeddings"
        )

        # Add embeddings
        embeddings = np.array([0.5, 0.6, 0.7], dtype=np.float32)
        concept.embeddings = embeddings

        # Verify embeddings
        assert concept.embeddings is not None
        assert isinstance(concept.embeddings, np.ndarray)

    def test_concept_model_with_temporal_info(self):
        """Test concept model with temporal information"""
        temporal = TemporalInfo(
            created=datetime.now(),
            modified=datetime.now()
        )

        concept = EnhancedConcept(
            id="concept-003",
            name="Temporal Concept",
            type=ConceptType.THEORY,
            definition="Concept with temporal info",
            temporal_info=temporal
        )

        # Verify temporal info
        assert concept.temporal_info is not None
        assert concept.temporal_info.created is not None
        assert concept.temporal_info.modified is not None

    def test_relation_model_creation_and_methods(self, sample_relation):
        """Test relation model creation and methods"""
        # Verify relation was created correctly
        assert sample_relation.id == "relation-001"
        assert sample_relation.source_concept == "concept-001"
        assert sample_relation.target_concept == "concept-002"
        assert sample_relation.relation_type == RelationType.RELATED_TO
        assert sample_relation.strength == 0.75

        # Test adding evidence
        sample_relation.add_evidence("doc-001", "Evidence quote", 0.8)
        assert len(sample_relation.evidence) == 1

        # Test updating strength
        sample_relation.update_strength(0.9)
        assert sample_relation.strength == 0.9

        # Test updating confidence
        sample_relation.update_confidence(0.85)
        assert sample_relation.confidence == 0.85

    def test_relation_model_validation(self):
        """Test relation model validation"""
        # Test invalid strength - Pydantic raises ValidationError
        from pydantic import ValidationError as PydanticValidationError
        with pytest.raises(PydanticValidationError):
            relation = Relation(
                id="relation-invalid",
                source_concept="concept-001",
                target_concept="concept-002",
                relation_type=RelationType.RELATED_TO,
                strength=1.5  # Invalid
            )

        # Test invalid confidence - Pydantic raises ValidationError
        with pytest.raises(PydanticValidationError):
            relation = Relation(
                id="relation-invalid2",
                source_concept="concept-001",
                target_concept="concept-002",
                relation_type=RelationType.RELATED_TO,
                confidence=-0.1  # Invalid
            )

    def test_models_with_temporal_info(self):
        """Test temporal info updates"""
        concept = EnhancedConcept(
            id="concept-004",
            name="Test",
            type=ConceptType.TERM,
            definition="Test"
        )

        # Get initial timestamp
        initial_time = concept.updated_at

        # Wait a bit
        time.sleep(0.01)

        # Update timestamp
        concept.update_timestamp()

        # Verify timestamp was updated
        assert concept.updated_at > initial_time


# ============================================================================
# LLM Provider Integration Tests
# ============================================================================

class TestLLMProviderIntegration:
    """Test LLM provider integration with configuration"""

    @patch('src.integrations.llm_providers.anthropic', create=True)
    def test_anthropic_provider_with_config(self, mock_anthropic):
        """Test Anthropic provider can be instantiated with config"""
        # Mock the client creation
        mock_client = MagicMock()
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        # Create provider with config-like parameters
        provider = AnthropicProvider(
            model="claude-sonnet-4-6",
            temperature=0.3,
            max_tokens=4096,
            api_key="test-key"
        )

        # Verify provider was created
        assert provider.model == "claude-sonnet-4-6"
        assert provider.temperature == 0.3
        assert provider.api_key == "test-key"

    @patch('src.integrations.llm_providers.openai', create=True)
    def test_openai_provider_with_config(self, mock_openai):
        """Test OpenAI provider can be instantiated with config"""
        # Mock the client creation
        mock_client = MagicMock()
        mock_openai.OpenAI = MagicMock(return_value=mock_client)

        # Create provider with config-like parameters
        provider = OpenAIProvider(
            model="gpt-4-turbo",
            temperature=0.3,
            max_tokens=4096,
            api_key="test-key"
        )

        # Verify provider was created
        assert provider.model == "gpt-4-turbo"
        assert provider.temperature == 0.3
        assert provider.api_key == "test-key"

    @patch('src.integrations.llm_providers.anthropic')
    def test_provider_generate_with_mock(self, mock_anthropic):
        """Test provider can generate text with mocked API"""
        # Mock the API response
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Generated text")]
        mock_client.messages.create = MagicMock(return_value=mock_message)
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        # Create provider and generate
        provider = AnthropicProvider(api_key="test-key")
        result = provider.generate("Test prompt")

        # Verify result
        assert result == "Generated text"
        mock_client.messages.create.assert_called_once()

    @patch('src.integrations.llm_providers.anthropic')
    def test_provider_generate_structured_with_mock(self, mock_anthropic):
        """Test provider can generate structured data with mocked API"""
        # Mock the API response
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='{"result": "structured data"}')]
        mock_client.messages.create = MagicMock(return_value=mock_message)
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client)

        # Create provider and generate
        provider = AnthropicProvider(api_key="test-key")
        schema = {"type": "object"}
        result = provider.generate_structured("Generate data", schema)

        # Verify result
        assert result == {"result": "structured data"}

    def test_factory_function(self):
        """Test factory function returns correct provider"""
        # Test Anthropic
        provider = get_llm_provider("anthropic", api_key_env="ANTHROPIC_API_KEY")
        assert isinstance(provider, AnthropicProvider)

        # Test OpenAI
        provider = get_llm_provider("openai", api_key_env="OPENAI_API_KEY")
        assert isinstance(provider, OpenAIProvider)

        # Test invalid provider
        with pytest.raises(ValueError):
            get_llm_provider("invalid")


# ============================================================================
# Embedding Generation Integration Tests
# ============================================================================

class TestEmbeddingIntegration:
    """Test embedding generation integration"""

    def test_embedding_cache(self):
        """Test embedding cache works correctly"""
        cache = EmbeddingCache(max_size=3)

        # Test cache miss
        result = cache.get("key1")
        assert result is None

        # Test cache hit
        embedding = np.array([0.1, 0.2, 0.3])
        cache.put("key1", embedding)
        result = cache.get("key1")
        assert np.array_equal(result, embedding)

        # Test cache eviction
        cache.put("key2", np.array([0.4, 0.5, 0.6]))
        cache.put("key3", np.array([0.7, 0.8, 0.9]))
        cache.put("key4", np.array([1.0, 1.1, 1.2]))  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key4") is not None

        # Test cache size
        assert cache.size() == 3
        assert "key2" in cache
        assert "key3" in cache

    @patch('src.ml.embeddings.openai')
    def test_embedding_generator_initialization(self, mock_openai):
        """Test embedding generator can be initialized"""
        # Set required API key
        os.environ["OPENAI_API_KEY"] = "test-key"

        try:
            # Mock the client
            mock_client = MagicMock()
            mock_openai.OpenAI = MagicMock(return_value=mock_client)

            # Create generator
            generator = EmbeddingGenerator()

            # Verify initialization
            assert generator.model_name == "text-embedding-3-small"
            assert generator.batch_size == 100
            assert generator.cache is not None

        finally:
            os.environ.pop("OPENAI_API_KEY", None)

    @patch('src.ml.embeddings.openai')
    def test_embedding_generator_cache_integration(self, mock_openai):
        """Test embedding generator uses cache correctly"""
        # Set required API key
        os.environ["OPENAI_API_KEY"] = "test-key"

        try:
            # Mock the API response
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
            mock_client.embeddings.create = MagicMock(return_value=mock_response)
            mock_openai.OpenAI = MagicMock(return_value=mock_client)

            # Create generator
            generator = EmbeddingGenerator()

            # Generate embedding twice
            text = "Test text"
            embedding1 = generator.generate_embedding(text)
            embedding2 = generator.generate_embedding(text)

            # Verify same embedding returned
            assert np.array_equal(embedding1, embedding2)

            # Verify API was called only once (cache hit on second call)
            assert mock_client.embeddings.create.call_count == 1

        finally:
            os.environ.pop("OPENAI_API_KEY", None)

    def test_embedding_generator_requires_api_key(self):
        """Test embedding generator requires API key"""
        # Ensure API key is not set
        os.environ.pop("OPENAI_API_KEY", None)

        with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
            EmbeddingGenerator()


# ============================================================================
# State Manager Integration Tests
# ============================================================================

class TestStateManagerIntegration:
    """Test state manager integration"""

    def test_state_manager_initialization(self, temp_state_file):
        """Test state manager can be initialized"""
        manager = StateManager(temp_state_file)

        # Verify initialization
        assert manager.state_file_path == temp_state_file
        assert isinstance(manager._state, dict)

    def test_state_manager_document_tracking(self, temp_state_file):
        """Test state manager can track document processing"""
        manager = StateManager(temp_state_file)

        # Set document state
        doc_id = "doc-001"
        state = {
            "status": ProcessingStatus.PROCESSING,
            "metadata": {"test": "data"}
        }
        manager.set_document_state(doc_id, state)

        # Get document state
        retrieved_state = manager.get_document_state(doc_id)
        assert retrieved_state is not None
        assert retrieved_state["status"] == ProcessingStatus.PROCESSING
        assert retrieved_state["metadata"]["test"] == "data"

    def test_state_manager_status_updates(self, temp_state_file):
        """Test state manager can update document status"""
        manager = StateManager(temp_state_file)

        # Update status
        doc_id = "doc-002"
        manager.update_document_status(doc_id, ProcessingStatus.PROCESSED)

        # Verify status
        state = manager.get_document_state(doc_id)
        assert state["status"] == ProcessingStatus.PROCESSED
        assert "last_updated" in state

    def test_state_manager_persistence(self, temp_state_file):
        """Test state manager can persist and load state"""
        # Create manager and set state
        manager1 = StateManager(temp_state_file)
        manager1.set_document_state("doc-003", {"status": ProcessingStatus.PROCESSED})
        manager1.save()

        # Create new manager and load state
        manager2 = StateManager(temp_state_file)
        manager2.load()

        # Verify state was loaded
        state = manager2.get_document_state("doc-003")
        assert state is not None
        assert state["status"] == ProcessingStatus.PROCESSED

    def test_state_manager_thread_safety(self, temp_state_file):
        """Test state manager is thread-safe"""
        manager = StateManager(temp_state_file)
        errors = []

        def update_document(doc_id):
            try:
                for i in range(10):
                    manager.update_document_status(doc_id, ProcessingStatus.PROCESSING)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            doc_id = f"doc-{i:03d}"
            thread = threading.Thread(target=update_document, args=(doc_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0

    def test_state_manager_query_methods(self, temp_state_file):
        """Test state manager query methods"""
        manager = StateManager(temp_state_file)

        # Add documents with different statuses
        manager.update_document_status("doc-001", ProcessingStatus.PENDING)
        manager.update_document_status("doc-002", ProcessingStatus.PENDING)
        manager.update_document_status("doc-003", ProcessingStatus.PROCESSED)

        # Get pending documents
        pending = manager.get_all_pending_documents()
        assert len(pending) == 2
        assert "doc-001" in pending
        assert "doc-002" in pending

    def test_state_manager_clear(self, temp_state_file):
        """Test state manager can clear state"""
        manager = StateManager(temp_state_file)

        # Add some state
        manager.set_document_state("doc-001", {"status": ProcessingStatus.PROCESSED})
        manager.save()

        # Clear state
        manager.clear()

        # Verify state is empty
        assert manager.get_document_state("doc-001") is None
        assert not os.path.exists(temp_state_file)


# ============================================================================
# End-to-End Integration Tests
# ============================================================================

class TestEndToEndIntegration:
    """Test end-to-end workflows with all components"""

    @patch('src.integrations.llm_providers.anthropic')
    @patch('src.ml.embeddings.openai')
    def test_complete_document_processing_workflow(self, mock_openai, mock_anthropic, temp_state_file):
        """Test complete workflow: Config → Document → LLM → Embeddings → State"""
        # Setup mocks
        mock_client_llm = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Generated summary")]
        mock_client_llm.messages.create = MagicMock(return_value=mock_message)
        mock_anthropic.Anthropic = MagicMock(return_value=mock_client_llm)

        mock_client_emb = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_client_emb.embeddings.create = MagicMock(return_value=mock_response)
        mock_openai.OpenAI = MagicMock(return_value=mock_client_emb)

        os.environ["OPENAI_API_KEY"] = "test-key"

        try:
            # 1. Load configuration
            config = Config()

            # 2. Create document
            metadata = DocumentMetadata(title="Test Doc", author="Test Author")
            doc = EnhancedDocument(
                id="doc-001",
                source_type=SourceType.MARKDOWN,
                content="Test content",
                metadata=metadata
            )

            # 3. Use LLM provider
            llm_provider = AnthropicProvider(api_key="test-key")
            summary = llm_provider.generate("Summarize: Test content")

            # 4. Generate embeddings
            embedding_gen = EmbeddingGenerator()
            embeddings = embedding_gen.generate_embedding(doc.content)
            doc.embeddings = embeddings

            # 5. Track with state manager
            state_mgr = StateManager(temp_state_file)
            state_mgr.update_document_status(doc.id, ProcessingStatus.PROCESSED)
            state_mgr.set_document_state(doc.id, {
                "status": ProcessingStatus.PROCESSED,
                "summary": summary,
                "embedding_dim": len(embeddings)
            })
            state_mgr.save()

            # Verify workflow completed successfully
            assert doc.id == "doc-001"
            assert summary == "Generated summary"
            assert doc.embeddings is not None
            assert state_mgr.get_document_state("doc-001") is not None

        finally:
            os.environ.pop("OPENAI_API_KEY", None)

    def test_document_concept_relation_workflow(self):
        """Test workflow linking documents, concepts, and relations"""
        # Create document
        metadata = DocumentMetadata(title="Knowledge Graph Doc")
        doc = EnhancedDocument(
            id="doc-001",
            source_type=SourceType.MARKDOWN,
            content="Content about knowledge graphs",
            metadata=metadata
        )

        # Create concepts
        concept1 = EnhancedConcept(
            id="concept-001",
            name="Knowledge Graph",
            type=ConceptType.TERM,
            definition="A graph representing knowledge"
        )

        concept2 = EnhancedConcept(
            id="concept-002",
            name="Graph Database",
            type=ConceptType.INDICATOR,
            definition="A database for graphs"
        )

        # Create relation
        relation = Relation(
            id="relation-001",
            source_concept="concept-001",
            target_concept="concept-002",
            relation_type=RelationType.RELATED_TO,
            strength=0.8
        )

        # Link everything
        doc.add_concept(concept1.id)
        doc.add_concept(concept2.id)
        doc.add_relation(relation.id)

        concept1.add_source_document(doc.id)
        concept2.add_source_document(doc.id)

        # Verify linking
        assert concept1.id in doc.concepts
        assert concept2.id in doc.concepts
        assert relation.id in doc.relations
        assert doc.id in concept1.source_documents
        assert doc.id in concept2.source_documents

    def test_serialization_deserialization_workflow(self, sample_document, sample_concept, sample_relation):
        """Test that models can be serialized and deserialized correctly"""
        # Serialize models
        doc_dict = sample_document.to_dict()
        concept_dict = sample_concept.to_dict()
        relation_dict = sample_relation.to_dict()

        # Verify serialization
        assert doc_dict["id"] == sample_document.id
        assert concept_dict["id"] == sample_concept.id
        assert relation_dict["id"] == sample_relation.id

        # Can be deserialized (Pydantic supports this)
        doc_recreated = EnhancedDocument(**doc_dict)
        concept_recreated = EnhancedConcept(**concept_dict)
        relation_recreated = Relation(**relation_dict)

        # Verify deserialization
        assert doc_recreated.id == sample_document.id
        assert concept_recreated.id == sample_concept.id
        assert relation_recreated.id == sample_relation.id


# ============================================================================
# Import Tests
# ============================================================================

class TestImportIntegration:
    """Test that all modules can be imported without circular dependencies"""

    def test_import_all_phase1_components(self):
        """Test that all Phase 1 components can be imported"""
        # Configuration
        from src.core.config import Config, get_config

        # Models
        from src.core.base_models import BaseModel, SourceType, ProcessingStatus
        from src.core.document_model import EnhancedDocument, DocumentMetadata
        from src.core.concept_model import EnhancedConcept, ConceptType, TemporalInfo
        from src.core.relation_model import Relation, RelationType

        # LLM Providers
        from src.integrations.llm_providers import (
            LLMProvider,
            AnthropicProvider,
            OpenAIProvider,
            get_llm_provider
        )

        # Embeddings
        from src.ml.embeddings import EmbeddingGenerator, EmbeddingCache

        # State Manager
        from src.core.state_manager import StateManager

        # If we get here without errors, imports are successful
        assert True

    def test_no_circular_imports(self):
        """Test that there are no circular import issues"""
        # This test passes if it can import all modules without hanging
        import src.core.config
        import src.core.document_model
        import src.core.concept_model
        import src.core.relation_model
        import src.integrations.llm_providers
        import src.ml.embeddings
        import src.core.state_manager

        assert True
