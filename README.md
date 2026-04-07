# KnowledgeMiner 3.0

A comprehensive intelligent knowledge accumulation system that transforms static markdown documents into a dynamic, self-maintaining Wiki with automatic concept extraction, relationship discovery, insight generation, and continuous quality assurance.

## 🎯 Project Overview

KnowledgeMiner 3.0 is a next-generation knowledge management system that goes beyond one-time analysis to create a living knowledge base. It automatically processes documents, discovers insights, backfills findings to historical content, and maintains Wiki quality through intelligent monitoring and repair.

## ✨ Features

### 🔄 Wiki Knowledge Management
- **Persistent Wiki Storage**: Version-controlled knowledge base with complete history tracking
- **Automatic Maintenance**: Self-maintaining Wiki that updates as new documents arrive
- **Batch Processing**: Efficient daily/weekly scheduled processing of new documents
- **Incremental Updates**: Smart hybrid mode selects optimal update strategy automatically
- **Wiki Organization**: Topic-based structure with automatic categorization and tagging

### 🧠 Intelligent Knowledge Discovery
- **Relation Mining**: Discover explicit, implicit, statistical, and semantic relationships between concepts
- **Pattern Detection**: Identify temporal, causal, evolutionary, and conflict patterns in knowledge
- **Gap Analysis**: Automatically find missing concepts, relations, and evidence
- **Insight Generation**: Generate actionable insights with multi-dimensional priority scoring
- **Semantic Search**: Full-text and semantic search across all Wiki content

### 💡 Smart Insight Management
- **Automatic Backfilling**: Intelligently propagate new insights to relevant historical pages
- **Priority Scoring**: Multi-dimensional assessment (novelty × impact × actionability)
- **Smart Propagation**: Direct propagation to affected pages (max 2 hops) with cycle detection
- **Queue Management**: Priority-based backfill with immediate (P0) and batch queues
- **Impact Analysis**: Assess which pages need updates when new insights emerge

### 🔍 Quality Assurance System
- **Health Monitoring**: Continuous monitoring of Wiki quality with comprehensive health checks
- **Consistency Checking**: Validate internal, cross-reference, and temporal consistency
- **Issue Classification**: Intelligent triage of issues (critical/important/minor)
- **Staged Repair**: Gradual automation from manual → semi-auto → full auto repairs
- **Quality Metrics**: Track health scores, issue distribution, and quality trends

### 🔒 Security & Performance
- **Path Traversal Protection**: All file operations validated to prevent attacks
- **API Key Security**: Automatic redaction of sensitive credentials in error messages
- **Content Caching**: 50% reduction in file I/O through intelligent caching
- **Algorithm Optimization**: O(n²) → O(n) complexity improvements for scalability
- **Dependency Injection**: Modular architecture for better testability and maintainability

### 🤖 LLM Integration
- **Multi-Provider Support**: OpenAI, Anthropic Claude, and local models (Ollama)
- **Semantic Embeddings**: Automatic generation of concept and document embeddings
- **AI-Assisted Review**: Interactive concept confirmation with LLM assistance
- **Smart Generation**: LLM-powered summaries, articles, and backlink generation

### 📊 Document Analysis
- **Automatic Extraction**: Parse and structure markdown documents with frontmatter
- **Concept Identification**: Extract key concepts, definitions, criteria, and examples
- **Relationship Mapping**: Map complex relationships between concepts
- **Categorization**: Intelligent organization by categories and tags
- **Confidence Scoring**: Assess extraction quality with confidence metrics

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

# Enhanced with LLM assistance
config.interactive_mode = True
config.llm.provider = "anthropic"  # Use Claude for interactive assistance
compiler = KnowledgeCompiler(config)
results = compiler.run_interactive_session()
```

### Phase 3: Wiki Knowledge Management

```python
from src.wiki import WikiSystem, WikiConfig
from src.discovery import KnowledgeDiscoveryEngine, DiscoveryConfig

# Create Wiki configuration
config = WikiConfig.profile_production()  # Pre-configured production settings
config.wiki_storage_path = "./wiki_storage"
config.batch_schedule = "0 2 * * *"  # Daily at 2am
config.enable_backfill = True
config.auto_repair_stage = 2  # Semi-automatic repairs

# Initialize Wiki system
wiki = WikiSystem(config)

# Initial Wiki build from existing documents
wiki.build_from_directory(
    source_dir="./documents",
    mode="full"  # Full analysis for initial build
)

# Add new documents incrementally
wiki.add_documents(
    new_docs=["./documents/new_article.md"],
    mode="hybrid"  # Smart mode selection
)

# Query the Wiki
results = wiki.search("machine learning algorithms")
topic_page = wiki.get_topic("Reinforcement Learning")
concept_info = wiki.get_concept("Q-Learning")

# Access Wiki history
version_history = wiki.get_history("Reinforcement Learning")
old_version = wiki.get_version("Reinforcement Learning", version=5)

# Monitor Wiki quality
health_report = wiki.get_health_report()
quality_metrics = wiki.get_quality_metrics()
```

### Knowledge Discovery with Wiki Integration

```python
from src.discovery import (
    KnowledgeDiscoveryEngine,
    InteractiveDiscovery,
    DiscoveryConfig
)

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

# Integrate with Wiki for automatic updates
wiki.update_from_discovery(result)

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

### Wiki Quality Management

```python
from src.wiki.quality import QualitySystem

# Initialize quality system
quality_system = QualitySystem(wiki)

# Run health check
health_report = quality_system.run_health_check()
print(f"Health Score: {health_report.overall_score}/100")
print(f"Critical Issues: {len(health_report.critical_issues)}")
print(f"Important Issues: {len(health_report.important_issues)}")

# Review and repair issues
repair_queue = quality_system.get_repair_queue()
for issue in repair_queue.critical:
    print(f"Critical: {issue.description}")
    # Manual review and approval
    if quality_system.propose_repair(issue):
        quality_system.apply_repair(issue)

# Get quality trends
trends = quality_system.get_quality_trends()
print(f"Quality Trend: {trends.direction}")  # improving/stable/declining
```

For complete working examples, see:
- `examples/wiki_example.py` - Wiki management
- `examples/discovery_example.py` - Knowledge discovery
- `examples/quality_example.py` - Quality assurance

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

### System Architecture

KnowledgeMiner 3.0 features a modular, four-component architecture designed for persistent knowledge accumulation:

#### 🗄️ WikiCore - Knowledge Storage Foundation
- **WikiStore**: Unified storage for topics, concepts, and relations
- **VersionLog**: Complete version history with Git integration
- **KnowledgeGraph**: NetworkX-based graph operations
- **QueryEngine**: Full-text search (Whoosh) and semantic queries
- **Immutable Storage**: Append-only writes for data integrity

#### 🔍 DiscoveryPipeline 2.0 - Intelligent Discovery Engine
- **InputProcessor**: Detect new, changed, and deleted documents
- **ModeSelector**: Smart selection between full/incremental/hybrid modes
- **DiscoveryOrchestrator**: Integrate relation mining, pattern detection, gap analysis
- **WikiIntegrator**: Direct Wiki updates with transaction safety

#### 💡 InsightManager - Insight Lifecycle Management
- **InsightReceiver**: Collect, deduplicate, and index insights
- **PriorityScorer**: Multi-dimensional scoring (novelty, impact, actionability)
- **BackfillScheduler**: Priority-based queue management (P0-P3)
- **BackfillExecutor**: Smart backfilling to affected pages
- **InsightPropagator**: Direct propagation with cycle detection

#### 🛡️ QualitySystem - Wiki Health Guardian
- **HealthMonitor**: Consistency, quality, and staleness detection
- **IssueClassifier**: Intelligent triage (critical/important/minor)
- **Staged Repair System**: Gradual automation (manual → semi-auto → auto)
- **QualityReporter**: Metrics, trends, and improvement suggestions

### Document Processing Layer

#### Analyzers
- **DocumentAnalyzer**: Parse and structure markdown documents with frontmatter
- **HashCalculator**: Create unique identifiers for change detection

#### Extractors
- **ConceptExtractor**: Identify and extract key concepts with pattern matching
- **RelationMiner**: Discover explicit, implicit, statistical, and semantic relations
- **PatternDetector**: Identify temporal, causal, evolutionary, and conflict patterns
- **GapAnalyzer**: Find missing concepts, relations, and evidence
- **InsightGenerator**: Generate actionable insights with significance scoring

#### Generators
- **ArticleGenerator**: Create detailed articles from concepts
- **SummaryGenerator**: Generate document summaries
- **BacklinkGenerator**: Create cross-references between concepts

### Integration Layer

#### LLM Providers
- **OpenAI Integration**: GPT models for text generation and analysis
- **Anthropic Integration**: Claude models for advanced reasoning
- **Local Models**: Ollama support for privacy and cost control
- **Unified Interface**: Consistent API across all providers

#### Embeddings & Search
- **Semantic Embeddings**: Vector representations for concepts and documents
- **Full-Text Search**: Whoosh-based search with highlighting
- **Semantic Search**: Vector similarity search with embeddings
- **Graph Navigation**: NetworkX for relationship traversal

### Security & Quality

#### Security Features
- **Path Validation**: All file operations validated to prevent traversal attacks
- **API Key Protection**: Automatic redaction of sensitive credentials
- **Input Sanitization**: Comprehensive validation on all user inputs
- **Transaction Safety**: ACID guarantees for Wiki updates

#### Performance Optimizations
- **Content Caching**: Documents read once and cached (50% I/O reduction)
- **Algorithm Optimization**: O(n²) → O(n) complexity improvements
- **LRU Cache**: Proper cache eviction with OrderedDict
- **Batch Processing**: Efficient handling of large document sets

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

KnowledgeMiner 3.0 maintains comprehensive test coverage across all components:

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_core/           # WikiCore tests (80+ tests)
pytest tests/test_discovery/      # DiscoveryPipeline tests (80+ tests)
pytest tests/test_insight/        # InsightManager tests (90+ tests)
pytest tests/test_quality/        # QualitySystem tests (55+ tests)
pytest tests/test_integration/    # End-to-end tests (30+ tests)
pytest tests/test_resilience/     # Resilience tests (60+ tests)

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run security validation tests
python test_phase2_review_fixes.py
```

### Test Statistics

- **Total Coverage**: 85%+ across all modules
- **Test Count**: 395+ tests (all passing)
- **WikiCore**: 80+ tests with full coverage
- **DiscoveryPipeline**: 80+ tests covering all modes
- **InsightManager**: 90+ tests for backfilling and propagation
- **QualitySystem**: 55+ tests for health monitoring and repairs
- **Resilience**: 60+ tests for chaos engineering and scalability
- **Security Validation**: 6/6 tests passing (100%)

### Test Categories

**Unit Tests**: Individual component testing
- Storage engine operations
- Discovery algorithms
- Insight scoring and propagation
- Quality checks and repairs

**Integration Tests**: End-to-end workflows
- Document processing → Wiki updates
- Insight discovery → Backfilling → Propagation
- Quality monitoring → Issue detection → Repair

**Resilience Tests**: Production readiness
- Crash recovery and data corruption
- Concurrent access and race conditions
- Large-scale performance (10,000+ pages)
- Migration and rollback scenarios

**Security Tests**: Vulnerability prevention
- Path traversal attack prevention
- API key protection in error messages
- Input validation and sanitization

## Performance

### Benchmarks

**Document Processing**:
- Document analysis: ~100ms per document
- Concept extraction: ~200ms per document
- Embedding generation: ~500ms per 100 concepts (batch)
- State persistence: ~50ms per save

**Knowledge Discovery**:
- Relation mining: ~500ms per 100 concepts
- Pattern detection: ~300ms per 100 concepts
- Gap analysis: ~200ms per 100 concepts
- Insight generation: ~1s per 100 insights (with LLM)

**Wiki Operations**:
- Full analysis (100 documents): ~5 minutes
- Incremental update (10 documents): ~30 seconds
- Wiki query response: <1 second
- Backfill processing: ~1 hour for P0 insights

**Quality Assurance**:
- Health check (1000 pages): ~2 minutes
- Consistency validation: ~30 seconds
- Auto-repair (low-risk): ~5 seconds per issue

### Scalability

- Tested with up to 10,000 Wiki pages
- Supports 100,000+ concept entries
- Handles 1,000,000+ relation records
- Processes batches of 1,000+ documents
- Efficient memory usage with streaming
- Incremental compilation reduces reprocessing

### Optimizations

**I/O Performance**:
- 50% reduction in file operations through content caching
- Lazy loading of Wiki pages
- Batch processing for large updates

**Algorithm Efficiency**:
- O(n²) → O(n) complexity in relation lookups
- Proper LRU cache implementation
- Smart mode selection (full vs incremental)

**Database Performance**:
- Indexed queries on all metadata fields
- Connection pooling for concurrent access
- Transaction batching for bulk updates

## Contributing

We welcome contributions to KnowledgeMiner 3.0! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/gordon8018/KnowledgeMiner.git
cd KnowledgeMiner

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/test_wiki/test_core/
```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for all modules, classes, and functions
- Add tests for new functionality (aim for >85% coverage)

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Write tests for your changes
4. Ensure all tests pass: `pytest`
5. Commit your changes: `git commit -m "feat: add amazing feature"`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Reporting Issues

When reporting bugs or requesting features:
- Use clear, descriptive titles
- Provide minimal reproduction cases for bugs
- Include environment details (OS, Python version)
- Search existing issues first

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Phase 1 Foundation**: Enhanced data models, LLM integration, embeddings
- **Phase 2 Discovery**: Intelligent relation mining, pattern detection, insight generation
- **Phase 3 Wiki System**: Persistent knowledge accumulation, quality assurance, automation
- **Security Hardening**: Comprehensive code review and vulnerability fixes

Built with ❤️ for intelligent knowledge management.