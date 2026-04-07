# KnowledgeMiner 2.0

A comprehensive system for converting raw markdown documents into structured knowledge bases with automatic concept extraction, categorization, relationship mapping, and intelligent knowledge discovery.

## 🎯 Project Overview

KnowledgeMiner 2.0 is an intelligent knowledge mining system featuring modular architecture, enhanced data models, LLM integration, and semantic search capabilities. Phase 1 establishes a robust foundation with pluggable components, while Phase 2 adds advanced knowledge discovery and insight generation.

## ✨ Features

### Core Features
- **Document Analysis**: Parse and structure markdown documents with frontmatter
- **Concept Extraction**: Automatically identify and extract key concepts from content
- **Intelligent Indexing**: Organize documents by categories and relationships
- **Content Generation**: Generate summaries, articles, and backlinks from extracted concepts
- **Interactive Review**: Review and confirm extracted concepts interactively
- **Flexible Configuration**: Extensive configuration options for customization
- **Error Handling**: Robust error handling and logging throughout the pipeline

### Phase 1 Enhancements
- **Enhanced Data Models**: New core models with better type safety and validation
- **LLM Integration**: Support for OpenAI, Anthropic Claude, and local models (Ollama)
- **Embedding Generation**: Automatic semantic embeddings for concepts and documents
- **State Management**: Persistent state tracking for incremental compilation
- **Modular Architecture**: Pluggable components with clear interfaces
- **Improved Performance**: 82% test coverage with optimized processing pipelines

### Phase 2: Knowledge Discovery Engine (New!)
- **Intelligent Relation Mining**: Discover explicit, implicit, statistical, and semantic relationships
- **Pattern Detection**: Identify temporal, causal, evolutionary, and conflict patterns
- **Gap Analysis**: Find missing concepts, relations, and evidence in your knowledge base
- **Insight Generation**: Generate actionable insights with significance scoring
- **Interactive Exploration**: Query your knowledge base with natural language
- **Comprehensive Testing**: 117 tests with full coverage of discovery features

### Phase 2: Code Review & Security Improvements (April 2025)
- **Security Hardening**: Path traversal vulnerability eliminated, API key protection implemented
- **Performance Optimization**: 50% reduction in file I/O, O(n²) → O(n) algorithm improvements
- **Architecture Enhancement**: Dependency injection pattern for better testability
- **Cache Optimization**: Proper LRU cache implementation with OrderedDict
- **Comprehensive Validation**: 6 validation tests for all fixes (100% passing)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/knowledge_compiler.git
cd knowledge_compiler

# Install dependencies
pip install -r requirements.txt
```

### Phase 2 Dependencies

For Phase 2 features (Knowledge Discovery Engine):

```bash
# Install with Phase 2 dependencies
pip install -r requirements.txt

# Phase 2 requires additional dependencies:
# - scikit-learn: Statistical analysis and clustering
# - networkx: Graph algorithms for relation mining
# - pydantic-settings: Enhanced configuration management

# These are already included in requirements.txt
```

### Phase 1 Dependencies

For Phase 1 features (LLM integration, embeddings):

```bash
# Install with Phase 1 dependencies
pip install -r requirements.txt

# Optional: For specific LLM providers
pip install openai anthropic
pip install ollama  # For local models
```

### Development Installation

```bash
# Install with development dependencies
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .
```

## Quick Start

### Command Line Usage (Phase 1 Enhanced)

```bash
# Basic usage
python -m src.main_cli --source ./docs --output ./knowledge_base

# With LLM integration
python -m src.main_cli --source ./docs --output ./knowledge_base --llm-provider openai --model gpt-4

# With embedding generation
python -m src.main_cli --source ./docs --output ./knowledge_base --enable-embeddings

# With state management (incremental compilation)
python -m src.main_cli --source ./docs --output ./knowledge_base --state-file state.json

# With verbose output
python -m src.main_cli --source ./docs --output ./knowledge_base --verbose

# Quiet mode
python -m src.main_cli --source ./docs --output ./knowledge_base --quiet

# Non-interactive mode
python -m src.main_cli --source ./docs --output ./knowledge_base --no-interactive

# Disable specific outputs
python -m src.main_cli --source ./docs --output ./knowledge_base --no-summaries --no-articles

# Use custom configuration
python -m src.main_cli --source ./docs --output ./knowledge_base --config config.json
```

### Python API Usage (Phase 1 Enhanced)

```python
from src.main import KnowledgeCompiler
from src.core.config import Config, get_config

# Create compiler with default configuration
compiler = KnowledgeCompiler()

# Compile all documents in source directory
results = compiler.compile()

print(f"Processed {results['processed_files']} files")
print(f"Extracted {results['extracted_concepts']} concepts")

# Phase 1: Using new configuration system
config = get_config()
config.llm.provider = "openai"
config.llm.model = "gpt-4"
config.embeddings.enabled = True

compiler = KnowledgeCompiler(config)
results = compiler.compile()
```

### Configuration (Phase 1 Enhanced)

```python
from src.core.config import Config, get_config

# Method 1: Use the new configuration system
config = get_config()
config.source_dir = "./docs"
config.output_dir = "./output"

# Configure LLM provider
config.llm.provider = "openai"
config.llm.model = "gpt-4"
config.llm.api_key = "your-api-key"
config.llm.temperature = 0.7

# Enable embeddings
config.embeddings.enabled = True
config.embeddings.model = "text-embedding-ada-002"

# Configure state management
config.state.enabled = True
config.state.file = "./state.json"

# Initialize compiler
compiler = KnowledgeCompiler(config)

# Method 2: Load from file
config = Config.from_file("config.json")
compiler = KnowledgeCompiler(config)
```

### Interactive Mode

```python
# Run interactive compilation session
results = compiler.run_interactive_session()

# Review concepts manually
confirmed_concepts = compiler.review_concepts(extracted_concepts)

# Phase 1: Enhanced with LLM assistance
config.interactive_mode = True
config.llm.provider = "anthropic"  # Use Claude for interactive assistance
compiler = KnowledgeCompiler(config)
results = compiler.run_interactive_session()
```

### Phase 2: Knowledge Discovery

```python
from src.discovery import (
    KnowledgeDiscoveryEngine,
    InteractiveDiscovery,
    DiscoveryConfig
)
from src.core.concept_model import EnhancedConcept, ConceptType
from src.core.document_model import EnhancedDocument
from src.core.relation_model import Relation

# Create discovery configuration
config = DiscoveryConfig(
    enable_explicit_mining=True,
    enable_implicit_mining=True,
    enable_statistical_mining=True,
    enable_semantic_mining=True,
    enable_temporal_detection=True,
    enable_causal_detection=True,
    enable_evolutionary_detection=True,
    enable_conflict_detection=True
)

# Initialize discovery engine
engine = KnowledgeDiscoveryEngine(config)

# Run discovery on your knowledge base
result = engine.discover(
    documents=your_documents,
    concepts=your_concepts,
    relations=existing_relations  # optional
)

# Access discoveries
print(f"Discovered {len(result.relations)} relations")
print(f"Detected {len(result.patterns)} patterns")
print(f"Found {len(result.gaps)} gaps")
print(f"Generated {len(result.insights)} insights")

# Interactive exploration
interactive = InteractiveDiscovery(engine)
interactive.discover_and_store(documents, concepts, relations)

# Explore relations for a concept
momentum_relations = interactive.explore_relations("Momentum")

# Find patterns by keyword
trading_patterns = interactive.find_patterns("trading")

# Analyze gaps in a domain
technical_gaps = interactive.analyze_gaps_in_domain("technical_analysis")

# Get top insights
top_insights = interactive.get_top_insights(10)

# Ask natural language questions
answer = interactive.ask_question(
    "How are momentum indicators used in trend following strategies?"
)
```

For a complete working example, see `examples/discovery_example.py`.

## Configuration Options

### Phase 1 Configuration System

The new configuration system provides hierarchical, validated settings:

```python
@dataclass
class Config:
    # Core settings
    source_dir: str
    output_dir: str
    file_patterns: List[str]

    # LLM configuration
    llm: LLMConfig

    # Embeddings configuration
    embeddings: EmbeddingsConfig

    # State management
    state: StateConfig

    # Processing settings
    processing: ProcessingConfig

    # Output settings
    output: OutputConfig
```

### Legacy Configuration (Still Supported)

The old `Config` class is still available for backward compatibility:

```python
from src.config import Config  # Legacy config

config = Config(
    source_dir="./docs",
    output_dir="./output",
    template_dir="templates",
    max_file_size=10 * 1024 * 1024,
    recursive_processing=True,
    file_patterns=["*.md"],
    api_key="your-key",
    model_name="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=2000,
    min_confidence_threshold=0.6,
    max_concepts_per_document=20,
    enable_relation_extraction=True,
    generate_backlinks=True,
    generate_summaries=True,
    generate_articles=True,
    output_format="markdown",
    interactive_mode=True,
    verbose_output=False,
    quiet_mode=False
)
```

### Loading Configuration from File

```python
# Load from JSON file
config = Config.from_file("config.json")

# Load from dictionary
config_data = {
    "source_dir": "./docs",
    "output_dir": "./output",
    "interactive_mode": True
}
config = Config.from_dict(config_data)
```

## Architecture

### Phase 1 Architecture

The Knowledge Compiler 2.0 features a modular, layered architecture:

#### Core Layer (Phase 1 New)
- **Base Models**: Abstract base classes for all domain models
- **Document Model**: Enhanced document representation with validation
- **Concept Model**: Rich concept model with flexible attributes
- **Relation Model**: Sophisticated relationship mapping between concepts
- **State Manager**: Persistent state tracking for incremental compilation
- **Configuration**: Hierarchical configuration with validation

#### Integration Layer (Phase 1 New)
- **LLM Providers**: Unified interface for OpenAI, Anthropic, and Ollama
- **Embeddings**: Semantic embedding generation for concepts and documents
- **Retry Logic**: Automatic retry with exponential backoff
- **Error Handling**: Comprehensive error handling and recovery

#### Processing Layer
- **Analyzers**:
  - **DocumentAnalyzer**: Parses and structures markdown documents
  - **HashCalculator**: Creates unique identifiers for documents

- **Extractors**:
  - **ConceptExtractor**: Identifies and extracts key concepts
  - Uses pattern matching and AI analysis
  - Supports multiple concept types (terms, indicators, strategies, etc.)

- **Generators**:
  - **ArticleGenerator**: Creates detailed articles from concepts
  - **SummaryGenerator**: Generates document summaries
  - **BacklinkGenerator**: Creates cross-references between concepts

- **Indexers**:
  - **FileIndexer**: Manages document lookup and organization
  - **CategoryIndexer**: Organizes documents by categories and tags
  - **RelationMapper**: Maps relationships between concepts

#### Utilities
- **FileOps**: Essential file operations and markdown discovery
- **MarkdownUtils**: Markdown parsing and processing utilities

### Phase 2: Code Review Architecture Improvements (April 2025)

The code review introduced several architectural enhancements:

#### Security Enhancements
- **Path Validation**: All file operations now validate paths to prevent traversal attacks
- **API Key Redaction**: Sensitive credentials automatically redacted from error messages
- **Input Sanitization**: Comprehensive validation on all user inputs

#### Performance Optimizations
- **Content Caching**: Documents are read once and cached, eliminating redundant I/O
- **Algorithm Optimization**: String operations improved from O(n²) to O(n) complexity
- **Cache Efficiency**: Proper LRU cache implementation using `collections.OrderedDict`

#### Code Quality Improvements
- **Dependency Injection**: `KnowledgeCompiler` supports component injection for better testability
- **Modular Design**: Components can be swapped or mocked for testing
- **Maintainability**: Clear separation of concerns and reduced coupling

```python
# Example: Dependency injection in action
from src.main import KnowledgeCompiler
from src.analyzers.document_analyzer import DocumentAnalyzer

# Inject custom analyzer for testing
mock_analyzer = DocumentAnalyzer()
compiler = KnowledgeCompiler(document_analyzer=mock_analyzer)
```

## Data Models

### Phase 1 Enhanced Models

#### Document (Enhanced)
```python
from src.core.document_model import Document

@dataclass
class Document:
    """Enhanced document model with validation and embeddings"""
    path: str
    title: str
    content: str
    metadata: Dict[str, Any]
    sections: List[Section]
    hash: str
    embedding: Optional[np.ndarray] = None  # Phase 1: Semantic embedding
    created_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> bool:
        """Validate document structure and content"""
        pass
```

#### Concept (Enhanced)
```python
from src.core.concept_model import Concept

@dataclass
class Concept:
    """Enhanced concept model with flexible attributes"""
    name: str
    type: ConceptType
    definition: str
    criteria: Optional[str] = None
    applications: List[Dict[str, str]] = field(default_factory=list)
    cases: List[str] = field(default_factory=list)
    formulas: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    backlinks: List[Dict[str, str]] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None  # Phase 1: Semantic embedding
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Concept':
        """Deserialize from dictionary"""
        pass
```

#### Relation (Phase 1 New)
```python
from src.core.relation_model import Relation, RelationType

@dataclass
class Relation:
    """Represents a relationship between concepts"""
    source: str
    target: str
    relation_type: RelationType
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class RelationType(Enum):
    """Types of relationships"""
    DEFINES = "defines"
    RELATES_TO = "relates_to"
    DEPENDS_ON = "depends_on"
    CONTRADICTS = "contradicts"
    EXTENDS = "extends"
    USES = "uses"
    EXAMPLE_OF = "example_of"
```

### Legacy Models (Still Supported)

#### Document (Legacy)
```python
from src.models.document import Document

@dataclass
class Document:
    path: str
    hash: str
    metadata: Dict[str, Any]
    sections: List[Section]
    content: str
```

#### Concept (Legacy)
```python
from src.models.concept import Concept

@dataclass
class Concept:
    name: str
    type: ConceptType
    definition: str
    criteria: str
    applications: List[Dict[str, str]]
    cases: List[str]
    formulas: List[str]
    related_concepts: List[str]
    backlinks: List[Dict[str, str]]
```

### Concept Types
- **TERM**: General terms and terminology
- **INDICATOR**: Technical indicators and metrics
- **STRATEGY**: Trading strategies and methods
- **THEORY**: Theoretical frameworks and models
- **PERSON**: People and their contributions

## Interactive Features

### Concept Confirmation
```python
# Confirm extracted concepts interactively
confirmed = compiler.confirm_concepts(extracted_concepts)

# Review concepts individually
reviewed = compiler.review_concepts(extracted_concepts)
```

### Interactive Session
```python
# Run complete interactive compilation session
results = compiler.run_interactive_session()

# Access compilation results
print(f"Confirmed concepts: {results.get('confirmed_concepts', 0)}")
print(f"Generated articles: {results.get('generated_articles', 0)}")
```

## Error Handling and Logging

The system provides comprehensive error handling and logging:

```python
# Configure logging levels
config = Config(verbose_output=True)  # DEBUG level
config = Config(quiet_mode=True)      # ERROR level only

# Access compilation statistics
stats = compiler.get_processing_statistics()
```

## Examples

### Phase 2: Knowledge Discovery

```python
# Run the discovery example
python examples/discovery_example.py

# Or import and use in your code
from src.discovery import KnowledgeDiscoveryEngine, DiscoveryConfig

config = DiscoveryConfig()
engine = KnowledgeDiscoveryEngine(config)
result = engine.discover(documents, concepts, relations)
```

### Basic Compilation
```python
from src.main import KnowledgeCompiler

# Initialize compiler
compiler = KnowledgeCompiler()

# Compile all documents
results = compiler.compile()

# Generate report
compiler.save_results_report("compilation_report.md")
```

### Custom Configuration
```python
from src.config import Config
from src.main import KnowledgeCompiler

# Custom configuration
config = Config(
    source_dir="./knowledge_base",
    output_dir="./wiki_output",
    file_patterns=["*.md", "*.markdown"],
    interactive_mode=False,
    generate_articles=True,
    generate_summaries=True,
    generate_backlinks=True
)

compiler = KnowledgeCompiler(config)
results = compiler.compile()
```

### Interactive Workflow
```python
from src.main import KnowledgeCompiler

# Initialize with interactive mode
config = Config(interactive_mode=True)
compiler = KnowledgeCompiler(config)

# Run interactive compilation
results = compiler.run_interactive_session()

# Review and update concepts
concepts = compiler.extracted_concepts
for concept in concepts:
    print(f"Concept: {concept.name}")
    print(f"Definition: {concept.definition}")
    # Interactive updates would happen here
```

## Testing

### Test Coverage

The project maintains comprehensive test coverage:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_integration.py

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run Phase 2 code review validation tests
python test_phase2_review_fixes.py
```

### Phase 2 Test Statistics

- **Total Coverage**: 85%+ (comprehensive discovery module coverage)
- **Test Count**: 117 tests for discovery features (all passing)
- **Discovery Components**: 90-100% coverage
- **Integration Tests**: End-to-end discovery pipeline validated

### Code Review Validation Tests (April 2025)

- **Security Tests**: Path traversal attack prevention (2/2 tests passing)
- **Performance Tests**: Redundant I/O elimination, O(n²) → O(n) optimization verified
- **Quality Tests**: API key protection, dependency injection, LRU cache implementation
- **Overall Results**: 6/6 validation tests passing (100%)
- **Regression Tests**: All existing functionality preserved

## Development Status

### Current Status: Phase 2 Complete with Security Hardening ✅

**Phase 1: Foundation and Core Enhancements** (Completed)
- ✅ Enhanced data models with validation
- ✅ LLM provider integration (OpenAI, Anthropic, Ollama)
- ✅ Embedding generation for semantic search
- ✅ State management for incremental compilation
- ✅ Comprehensive test coverage (82%)
- ✅ Documentation updates

**Phase 2: Knowledge Discovery Engine** (Completed)
- ✅ Intelligent relation mining (explicit, implicit, statistical, semantic)
- ✅ Pattern detection (temporal, causal, evolutionary, conflict)
- ✅ Gap analysis (concepts, relations, evidence)
- ✅ Insight generation with significance scoring
- ✅ Interactive exploration API
- ✅ 117 comprehensive tests (all passing)
- ✅ Complete documentation and examples

**Phase 2: Code Review & Security Improvements** (Completed - April 2025)
- ✅ Security: Path traversal vulnerability eliminated (HIGH priority)
- ✅ Security: API key exposure prevention in error messages (MEDIUM priority)
- ✅ Performance: 50% reduction in file I/O operations (HIGH priority)
- ✅ Performance: O(n²) → O(n) algorithm optimization (MEDIUM priority)
- ✅ Architecture: Dependency injection for better testability (MEDIUM priority)
- ✅ Performance: Proper LRU cache implementation (MEDIUM priority)
- ✅ 6 validation tests created and passing (100%)
- ✅ Comprehensive documentation in `docs/Phase2_Code_Review_Fixes_Summary.md`

### Upcoming Phases

**Phase 3: Production Hardening** (Planned)
- Scalability improvements
- Monitoring and metrics
- Deployment automation
- Advanced error handling
- Additional performance optimizations

## Migration Guide

### From Legacy to Phase 1

#### Configuration Migration

**Old approach:**
```python
from src.config import Config

config = Config(
    api_key="key",
    model_name="gpt-3.5-turbo",
    temperature=0.7
)
```

**New approach:**
```python
from src.core.config import get_config

config = get_config()
config.llm.api_key = "key"
config.llm.model = "gpt-4"
config.llm.temperature = 0.7
```

#### Data Model Migration

**Old approach:**
```python
from src.models.document import Document
from src.models.concept import Concept
```

**New approach:**
```python
from src.core.document_model import Document
from src.core.concept_model import Concept

# Enhanced models include:
# - Validation methods
# - Embedding support
# - Better serialization
```

#### Adding LLM Integration

```python
# Before: No LLM support
compiler = KnowledgeCompiler()

# After: With LLM
config = get_config()
config.llm.provider = "openai"
config.llm.model = "gpt-4"
compiler = KnowledgeCompiler(config)
```

#### Adding Embeddings

```python
# Enable embeddings
config.embeddings.enabled = True
config.embeddings.model = "text-embedding-ada-002"

# Concepts will now have semantic embeddings
concepts = compiler.extracted_concepts
for concept in concepts:
    if concept.embedding is not None:
        print(f"{concept.name} has embedding vector")
```

### From Phase 1 to Phase 2

#### Adding Knowledge Discovery

```python
# Phase 1: Basic compilation
from src.main import KnowledgeCompiler
from src.core.config import get_config

config = get_config()
compiler = KnowledgeCompiler(config)
results = compiler.compile()
documents = compiler.processed_documents
concepts = compiler.extracted_concepts

# Phase 2: Add knowledge discovery
from src.discovery import KnowledgeDiscoveryEngine, DiscoveryConfig

discovery_config = DiscoveryConfig(
    enable_explicit_mining=True,
    enable_implicit_mining=True,
    enable_statistical_mining=True,
    enable_semantic_mining=True
)

discovery_engine = KnowledgeDiscoveryEngine(
    config=discovery_config,
    llm_provider=compiler.llm_provider,  # Reuse LLM from compiler
    embedding_generator=compiler.embedding_generator  # Reuse embedder
)

# Run discovery on compiled knowledge
discovery_result = discovery_engine.discover(
    documents=documents,
    concepts=concepts,
    relations=compiler.extracted_relations  # Existing relations
)

# Access discoveries
print(f"Discovered {len(discovery_result.relations)} new relations")
print(f"Detected {len(discovery_result.patterns)} patterns")
print(f"Found {len(discovery_result.gaps)} knowledge gaps")
print(f"Generated {len(discovery_result.insights)} insights")
```

#### Interactive Knowledge Exploration

```python
# Phase 2: Add interactive exploration
from src.discovery import InteractiveDiscovery

interactive = InteractiveDiscovery(discovery_engine)
interactive.discover_and_store(documents, concepts, relations)

# Explore your knowledge base interactively
momentum_relations = interactive.explore_relations("Momentum")
trading_patterns = interactive.find_patterns("trading strategy")
technical_gaps = interactive.analyze_gaps_in_domain("technical analysis")

# Get top insights
top_insights = interactive.get_top_insights(10)

# Ask natural language questions
answer = interactive.ask_question(
    "What are the most common patterns in momentum trading strategies?"
)
```

#### Integrating with Existing Workflow

```python
# Complete Phase 1 + Phase 2 workflow
from src.main import KnowledgeCompiler
from src.discovery import KnowledgeDiscoveryEngine, InteractiveDiscovery
from src.core.config import get_config

# Step 1: Compile documents (Phase 1)
config = get_config()
config.source_dir = "./docs"
config.output_dir = "./output"

compiler = KnowledgeCompiler(config)
compilation_result = compiler.compile()

# Step 2: Discover knowledge (Phase 2)
discovery_config = DiscoveryConfig()
discovery_engine = KnowledgeDiscoveryEngine(discovery_config)
discovery_result = discovery_engine.discover(
    documents=compiler.processed_documents,
    concepts=compiler.extracted_concepts
)

# Step 3: Explore interactively (Phase 2)
interactive = InteractiveDiscovery(discovery_engine)
interactive.discover_and_store(
    documents=compiler.processed_documents,
    concepts=compiler.extracted_concepts
)

# Now you have a complete, explorable knowledge base!
```

## Performance

### Phase 1 Benchmarks

- **Document Processing**: ~100ms per document
- **Concept Extraction**: ~200ms per document
- **Embedding Generation**: ~500ms per 100 concepts (batch)
- **State Persistence**: ~50ms per save
- **Test Suite**: ~20 seconds for 429 tests

### Phase 2 Benchmarks

- **Relation Mining**: ~500ms per 100 concepts
- **Pattern Detection**: ~300ms per 100 concepts
- **Gap Analysis**: ~200ms per 100 concepts
- **Insight Generation**: ~1s per 100 insights (with LLM)
- **Full Discovery Pipeline**: ~2-3s for 100 documents
- **Discovery Test Suite**: ~15 seconds for 117 tests

### Code Review Performance Improvements (April 2025)

- **File I/O**: 50% reduction in redundant disk operations (cached content usage)
- **String Operations**: O(n²) → O(n) complexity in relation lookups
- **Cache Efficiency**: Proper LRU implementation improves hit rates
- **Overall Impact**: Faster concept extraction and better scalability

### Scalability

- Tested with up to 1000 documents
- Handles documents up to 10MB
- Efficient memory usage with streaming
- Incremental compilation reduces reprocessing
- Discovery engine scales linearly with concept count
- Batch processing for large knowledge bases
- **Security**: Path validation prevents unauthorized file access
- **Architecture**: Dependency injection enables better testing and modularity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.