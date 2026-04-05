# Knowledge Compiler Usage Guide

This guide provides detailed instructions for using the Knowledge Compiler 2.0 to process and transform your markdown documents into a structured knowledge base.

## What's New in Phase 1

- **Enhanced Configuration System**: Hierarchical, validated configuration
- **LLM Integration**: Support for OpenAI, Anthropic Claude, and Ollama
- **Embedding Generation**: Automatic semantic embeddings for search
- **State Management**: Persistent state for incremental compilation
- **Improved Data Models**: Better validation and serialization

## Table of Contents

1. [Getting Started](#getting-started)
2. [Configuration](#configuration)
3. [Phase 1 Features](#phase-1-features)
4. [Command Line Usage](#command-line-usage)
5. [Programmatic Usage](#programmatic-usage)
6. [Interactive Mode](#interactive-mode)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.8+
- Required dependencies (see `requirements.txt`)
- Source markdown documents
- Output directory for processed content
- (Optional) API keys for LLM providers (OpenAI, Anthropic)
- (Optional) Ollama installation for local models

### Basic Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your settings:**

   **Phase 1 Configuration:**
   ```json
   {
     "source_dir": "./docs",
     "output_dir": "./wiki",
     "interactive_mode": true,
     "verbose_output": true,
     "llm": {
       "provider": "openai",
       "model": "gpt-4",
       "api_key": "your-api-key",
       "temperature": 0.7
     },
     "embeddings": {
       "enabled": true,
       "model": "text-embedding-ada-002",
       "batch_size": 100
     },
     "state": {
       "enabled": true,
       "file": "./state.json"
     }
   }
   ```

   **Legacy Configuration (still supported):**
   ```json
   {
     "source_dir": "./docs",
     "output_dir": "./wiki",
     "interactive_mode": true,
     "verbose_output": true,
     "api_key": "your-api-key",
     "model_name": "gpt-3.5-turbo",
     "temperature": 0.7
   }
   ```

3. **Run the compiler:**
   ```python
   from src.main import KnowledgeCompiler
   from src.core.config import get_config

   # Phase 1: Using new configuration
   config = get_config()
   config.source_dir = "./docs"
   config.output_dir = "./wiki"
   config.llm.provider = "openai"
   config.llm.model = "gpt-4"

   compiler = KnowledgeCompiler(config)
   results = compiler.compile()

   # Or use legacy approach
   compiler = KnowledgeCompiler()
   results = compiler.compile()
   ```

## Configuration

### Phase 1 Configuration Structure

The new configuration system is hierarchical and provides better validation:

```json
{
  "source_dir": "path/to/source/documents",
  "output_dir": "path/to/output/directory",
  "file_patterns": ["*.md", "*.markdown"],
  "recursive_processing": true,

  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "your-api-key",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 30,
    "max_retries": 3
  },

  "embeddings": {
    "enabled": true,
    "model": "text-embedding-ada-002",
    "batch_size": 100,
    "dimension": 1536
  },

  "state": {
    "enabled": true,
    "file": "./state.json",
    "auto_save": true,
    "save_interval": 60
  },

  "processing": {
    "max_file_size": 10485760,
    "max_concepts_per_document": 20,
    "min_confidence_threshold": 0.6,
    "enable_relation_extraction": true
  },

  "output": {
    "generate_backlinks": true,
    "generate_summaries": true,
    "generate_articles": true,
    "output_format": "markdown"
  },

  "interactive_mode": true,
  "verbose_output": false,
  "quiet_mode": false
}
```

### Legacy Configuration File Structure

Create a `config.json` file with the following structure:

```json
{
  "source_dir": "path/to/source/documents",
  "output_dir": "path/to/output/directory",
  "template_dir": "path/to/templates",
  "max_file_size": 10485760,
  "recursive_processing": true,
  "file_patterns": ["*.md", "*.markdown"],
  "api_key": "your-api-key",
  "model_name": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_tokens": 2000,
  "min_confidence_threshold": 0.6,
  "max_concepts_per_document": 20,
  "enable_relation_extraction": true,
  "generate_backlinks": true,
  "generate_summaries": true,
  "generate_articles": true,
  "output_format": "markdown",
  "interactive_mode": true,
  "verbose_output": false,
  "quiet_mode": false
}
```

### Key Configuration Options

#### Source Configuration
- `source_dir`: Directory containing source markdown files
- `output_dir`: Directory where processed content will be saved
- `template_dir`: Directory containing template files
- `file_patterns`: List of file patterns to include (e.g., `["*.md", "*.markdown"]`)
- `recursive_processing`: Whether to process subdirectories

#### Processing Configuration
- `max_file_size`: Maximum file size in bytes (default: 10MB)
- `max_concepts_per_document`: Maximum number of concepts to extract per document
- `min_confidence_threshold`: Minimum confidence score for concept extraction
- `enable_relation_extraction`: Whether to extract relationships between concepts

#### AI Configuration
- `api_key`: API key for AI services
- `model_name`: Name of the AI model to use
- `temperature`: AI response randomness (0.0-1.0)
- `max_tokens`: Maximum tokens for AI responses

#### Output Configuration
- `generate_backlinks`: Whether to generate backlink files
- `generate_summaries`: Whether to generate document summaries
- `generate_articles`: Whether to generate concept articles
- `output_format`: Output format (markdown, html, json)

#### UI Configuration
- `interactive_mode`: Enable interactive features
- `verbose_output`: Enable verbose logging
- `quiet_mode`: Suppress non-error messages

## Phase 1 Features

### 1. LLM Integration

The Knowledge Compiler now supports multiple LLM providers for enhanced concept extraction and content generation.

#### Supported Providers

**OpenAI**
```python
from src.core.config import get_config

config = get_config()
config.llm.provider = "openai"
config.llm.model = "gpt-4"  # or "gpt-3.5-turbo"
config.llm.api_key = "sk-..."
config.llm.temperature = 0.7
config.llm.max_tokens = 2000
```

**Anthropic Claude**
```python
config.llm.provider = "anthropic"
config.llm.model = "claude-3-opus-20240229"  # or "claude-3-sonnet-20240229"
config.llm.api_key = "sk-ant-..."
```

**Ollama (Local Models)**
```python
config.llm.provider = "ollama"
config.llm.model = "llama2"  # or "mistral", "neural-chat", etc.
config.llm.base_url = "http://localhost:11434"  # Optional
```

#### Using LLM Providers

```python
from src.main import KnowledgeCompiler
from src.integrations.llm_providers import create_llm_provider

# Method 1: Through configuration
config = get_config()
config.llm.provider = "openai"
config.llm.model = "gpt-4"

compiler = KnowledgeCompiler(config)
results = compiler.compile()

# Method 2: Direct provider usage
provider = create_llm_provider(
    provider="openai",
    model="gpt-4",
    api_key="your-key"
)

response = provider.generate(
    prompt="Extract key concepts from this text...",
    temperature=0.7
)
```

#### Error Handling and Retries

LLM providers include automatic retry logic with exponential backoff:

```python
# Configure retry behavior
config.llm.max_retries = 3
config.llm.retry_delay = 1.0  # seconds
config.llm.timeout = 30  # seconds

# The provider will automatically retry on transient errors
```

### 2. Embedding Generation

Generate semantic embeddings for concepts and documents to enable similarity search and clustering.

#### Enabling Embeddings

```python
config = get_config()
config.embeddings.enabled = True
config.embeddings.model = "text-embedding-ada-002"
config.embeddings.batch_size = 100
config.embeddings.dimension = 1536  # Model-specific
```

#### Supported Embedding Models

**OpenAI Embeddings**
```python
config.embeddings.provider = "openai"
config.embeddings.model = "text-embedding-ada-002"  # 1536 dimensions
# or
config.embeddings.model = "text-embedding-3-small"   # 1536 dimensions
# or
config.embeddings.model = "text-embedding-3-large"   # 3072 dimensions
```

**Local Embeddings (Future)**
```python
# Planned for future releases
config.embeddings.provider = "local"
config.embeddings.model = "all-MiniLM-L6-v2"
```

#### Using Embeddings

```python
from src.ml.embeddings import EmbeddingGenerator

# After compilation, concepts have embeddings
compiler = KnowledgeCompiler(config)
results = compiler.compile()

# Access embeddings
for concept in compiler.extracted_concepts:
    if concept.embedding is not None:
        print(f"Concept: {concept.name}")
        print(f"Embedding shape: {concept.embedding.shape}")

# Calculate similarity
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def find_similar_concepts(target_concept, concepts, top_k=5):
    """Find most similar concepts using embeddings"""
    if target_concept.embedding is None:
        return []

    similarities = []
    for concept in concepts:
        if concept.embedding is not None and concept != target_concept:
            sim = cosine_similarity(
                [target_concept.embedding],
                [concept.embedding]
            )[0][0]
            similarities.append((concept, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]

# Example usage
similar = find_similar_concepts(
    compiler.extracted_concepts[0],
    compiler.extracted_concepts
)
for concept, score in similar:
    print(f"{concept.name}: {score:.3f}")
```

#### Embedding Use Cases

1. **Semantic Search**: Find concepts by meaning, not just keywords
2. **Clustering**: Group similar concepts automatically
3. **Recommendations**: Suggest related concepts
4. **Deduplication**: Identify duplicate or very similar concepts
5. **Visualization**: Plot concept relationships in 2D/3D space

### 3. State Management

Persistent state tracking enables incremental compilation and avoids reprocessing unchanged documents.

#### Enabling State Management

```python
config = get_config()
config.state.enabled = True
config.state.file = "./compilation_state.json"
config.state.auto_save = True
config.state.save_interval = 60  # seconds
```

#### State Features

```python
from src.core.state_manager import StateManager

# The compiler automatically uses state
compiler = KnowledgeCompiler(config)

# First run: processes all documents
results1 = compiler.compile()

# Second run: only processes new/changed documents
results2 = compiler.compile()

# State includes:
# - Document hashes (detects changes)
# - Processed concepts
# - Compilation metadata
# - Timestamps
```

#### Manual State Operations

```python
# Access state manager
state_manager = compiler.state_manager

# Get last compilation time
last_run = state_manager.get_last_run_time()

# Check if document needs processing
needs_processing = state_manager.needs_processing(document_path)

# Manually save state
state_manager.save_state()

# Reset state (start fresh)
state_manager.reset_state()
```

#### State File Format

```json
{
  "version": "2.0",
  "last_run": "2026-04-05T10:30:00",
  "documents": {
    "doc1.md": {
      "hash": "abc123",
      "processed_at": "2026-04-05T10:25:00",
      "concepts_count": 5
    }
  },
  "metadata": {
    "total_concepts": 150,
    "total_documents": 30
  }
}
```

### 4. Enhanced Data Models

Phase 1 introduces improved data models with validation and serialization.

#### Enhanced Document Model

```python
from src.core.document_model import Document

# Create document
doc = Document(
    path="./docs/concept.md",
    title="My Concept",
    content="# Content...",
    metadata={"author": "John"},
    sections=[],
    hash="abc123"
)

# Validate structure
is_valid = doc.validate()

# Serialize/Deserialize
doc_dict = doc.to_dict()
doc2 = Document.from_dict(doc_dict)
```

#### Enhanced Concept Model

```python
from src.core.concept_model import Concept, ConceptType

# Create concept
concept = Concept(
    name="Momentum",
    type=ConceptType.INDICATOR,
    definition="A technical indicator...",
    confidence=0.95,
    metadata={"source": "technical_analysis"}
)

# Add embedding
import numpy as np
concept.embedding = np.random.rand(1536)

# Validate and serialize
concept.validate()
concept_dict = concept.to_dict()
```

#### Relation Model (New)

```python
from src.core.relation_model import Relation, RelationType

# Create relation
relation = Relation(
    source="Momentum",
    target="RSI",
    relation_type=RelationType.RELATES_TO,
    strength=0.8,
    metadata={"context": "technical_analysis"}
)

# Serialize
relation_dict = relation.to_dict()
```

### 5. Configuration Management

#### Loading Configuration

```python
from src.core.config import Config, get_config

# Method 1: Get default config
config = get_config()

# Method 2: Load from file
config = Config.from_file("config.json")

# Method 3: Load from dict
config = Config.from_dict({
    "source_dir": "./docs",
    "llm": {"provider": "openai"}
})

# Method 4: Environment variables
import os
config = get_config()
config.llm.api_key = os.getenv("OPENAI_API_KEY")
```

#### Validating Configuration

```python
# Validate before use
try:
    config.validate()
    print("Configuration is valid")
except ValueError as e:
    print(f"Configuration error: {e}")
```

#### Saving Configuration

```python
# Save to file
config.save_to_file("my_config.json")

# Export as dict
config_dict = config.to_dict()
```

### 6. Advanced Usage Examples

#### Combining Phase 1 Features

```python
from src.main import KnowledgeCompiler
from src.core.config import get_config

# Create comprehensive config
config = get_config()
config.source_dir = "./docs"
config.output_dir = "./output"

# Enable LLM
config.llm.provider = "openai"
config.llm.model = "gpt-4"
config.llm.api_key = os.getenv("OPENAI_API_KEY")

# Enable embeddings
config.embeddings.enabled = True
config.embeddings.model = "text-embedding-ada-002"

# Enable state
config.state.enabled = True
config.state.file = "./state.json"

# Run compilation
compiler = KnowledgeCompiler(config)
results = compiler.compile()

# Use embeddings for similarity search
target = compiler.extracted_concepts[0]
similar = find_similar_concepts(target, compiler.extracted_concepts)
print(f"Concepts similar to {target.name}:")
for concept, score in similar:
    print(f"  {concept.name}: {score:.3f}")
```

#### Incremental Compilation

```python
# First run
config.state.enabled = True
compiler = KnowledgeCompiler(config)
results1 = compiler.compile()
print(f"Processed {results1['processed_files']} files")

# Modify one document
# ...

# Second run (only processes modified document)
results2 = compiler.compile()
print(f"Processed {results2['processed_files']} files (should be 1)")
```

#### Error Handling

```python
# Configure robust error handling
config.llm.max_retries = 5
config.llm.timeout = 60

# Handle errors gracefully
try:
    results = compiler.compile()
except Exception as e:
    print(f"Compilation failed: {e}")

    # Check state
    if config.state.enabled:
        state = compiler.state_manager.get_state()
        print(f"Last successful run: {state['last_run']}")

    # Retry with different config
    config.llm.provider = "ollama"  # Fallback to local
    compiler = KnowledgeCompiler(config)
    results = compiler.compile()
```

## Command Line Usage

### Basic Command Line Interface

The Knowledge Compiler can be used programmatically. Here's how to use it:

```python
from src.main import KnowledgeCompiler
from src.config import Config

# Basic usage
compiler = KnowledgeCompiler()
results = compiler.compile()

# With custom configuration
config = Config.from_file("config.json")
compiler = KnowledgeCompiler(config)
results = compiler.compile()

# Run interactive session
if config.interactive_mode:
    results = compiler.run_interactive_session()
```

### Command Line Interface

The Knowledge Compiler now provides a comprehensive command-line interface:

```bash
# Basic usage
python -m src.main_cli --source ./docs --output ./knowledge_base

# Show help
python -m src.main_cli --help

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

### Available CLI Arguments

#### Positional Arguments
- `source_dir`: Source directory containing markdown files (default: current directory)

#### Output Options
- `--output`, `-o`: Output directory for generated files (default: output)
- `--config`, `-c`: Path to configuration file (JSON format)

#### Processing Options
- `--recursive`, `-r`: Process files recursively (default: True)
- `--non-recursive`: Process files in the source directory only (no recursion)

#### Output Generation Options
- `--no-summaries`: Disable summary generation
- `--no-articles`: Disable article generation
- `--no-backlinks`: Disable backlink generation

#### Interactive Options
- `--no-interactive`: Disable interactive mode
- `--verbose`, `-v`: Enable verbose output
- `--quiet`, `-q`: Suppress all output except errors

#### Model Options
- `--model`: AI model to use for processing (default: gpt-3.5-turbo)
- `--temperature`: Temperature for AI model (0.0-1.0, default: 0.7)
- `--max-tokens`: Maximum tokens for AI model (default: 2000)

#### File Options
- `--max-file-size`: Maximum file size to process in bytes (default: 10MB)
- `--file-patterns`: File patterns to match (default: *.md *.markdown)

#### Analysis Options
- `--min-confidence`: Minimum confidence threshold for concept extraction (0.0-1.0, default: 0.6)
- `--max-concepts`: Maximum concepts to extract per document (default: 20)
- `--no-relations`: Disable relation extraction

## Programmatic Usage

### 1. Basic Compilation

```python
from src.main import KnowledgeCompiler

# Create compiler with default settings
compiler = KnowledgeCompiler()

# Run compilation
results = compiler.compile()

# Print results
print(f"Processed {results['processed_files']} files")
print(f"Extracted {results['extracted_concepts']} concepts")
print(f"Generated {results['generated_articles']} articles")
```

### 2. Custom Configuration

```python
from src.config import Config
from src.main import KnowledgeCompiler

# Create custom configuration
config = Config(
    source_dir="./my_documents",
    output_dir="./my_wiki",
    file_patterns=["*.md", "*.markdown"],
    interactive_mode=True,
    generate_articles=True,
    generate_summaries=True
)

# Initialize and run
compiler = KnowledgeCompiler(config)
results = compiler.compile()
```

### 3. Working with Individual Components

```python
from src.main import KnowledgeCompiler
from src.analyzers.document_analyzer import DocumentAnalyzer
from src.extractors.concept_extractor import ConceptExtractor

# Analyze individual document
analyzer = DocumentAnalyzer()
document = analyzer.analyze("path/to/document.md")

# Extract concepts
extractor = ConceptExtractor()
concepts = extractor.extract_concepts(document)

# Add to compiler
compiler = KnowledgeCompiler()
compiler.extracted_concepts.extend(concepts)
```

### 4. Processing Statistics

```python
# Get detailed statistics
stats = compiler.get_processing_statistics()

print("Documents by category:")
for category in stats['documents']['by_category']:
    count = compiler.category_indexer.get_category_document_count(category)
    print(f"  {category}: {count} documents")

print("\nRelation statistics:")
for relation_type, count in stats['concepts']['relations'].items():
    print(f"  {relation_type}: {count} relations")
```

### 5. Saving Results

```python
# Save compilation report
report_path = os.path.join(config.output_dir, "compilation_report.md")
compiler.save_results_report(report_path)

# Generate individual outputs
for concept in compiler.extracted_concepts:
    # Generate article
    article = compiler.article_generator.generate_article(
        concept, compiler.extracted_concepts
    )

    # Save article
    article_path = os.path.join(config.output_dir, f"article_{concept.name}.md")
    write_file(article_path, article)
```

## Interactive Mode

### 1. Enabling Interactive Mode

```python
from src.config import Config
from src.main import KnowledgeCompiler

# Enable interactive mode
config = Config(interactive_mode=True, verbose_output=True)
compiler = KnowledgeCompiler(config)

# Run interactive compilation
results = compiler.run_interactive_session()
```

### 2. Interactive Workflows

#### Concept Confirmation

```python
# Extract concepts
concepts = compiler.extracted_concepts

# Confirm concepts interactively
confirmed = compiler.confirm_concepts(concepts)
print(f"Confirmed {len(confirmed)} out of {len(concepts)} concepts")
```

#### Individual Concept Review

```python
# Review concepts one by one
reviewed = compiler.review_concepts(concepts)

# For each concept, you can:
# - Keep it
# - Skip it
# - Update its definition
# - Quit early
```

#### Manual Editing

```python
# Manually edit concepts
edited = compiler._manual_edit_concepts(concepts)

# This calls confirm_concepts for user selection
```

### 3. Interactive Session Flow

1. **Document Processing**: All documents are processed first
2. **Concept Extraction**: Concepts are extracted from documents
3. **Interactive Review**: User reviews and confirms concepts
4. **Output Generation**: Final outputs are generated with confirmed concepts
5. **Report Generation**: Compilation report is created

### 4. Interactive Input Commands

During concept review, use these commands:

- `k` or `keep`: Keep the current concept
- `s` or `skip`: Skip the current concept
- `u` or `update`: Update the concept definition
- `q` or `quit`: Quit the review process
- `c` or `continue`: Continue to next concept (during definition update)

## Advanced Features

### 1. Custom Configuration Loading

```python
# Load from JSON file
config = Config.from_file("path/to/config.json")

# Load from dictionary
config_dict = {
    "source_dir": "./docs",
    "output_dir": "./output",
    "interactive_mode": False
}
config = Config.from_dict(config_dict)

# Save configuration
config.save_to_file("my_config.json")
```

### 2. Custom File Processing

```python
# Process specific files only
markdown_files = find_markdown_files(config.source_dir)
filtered_files = [f for f in markdown_files if config.should_process_file(f)]

for file_path in filtered_files:
    document = compiler.document_analyzer.analyze(file_path)
    # Process document...
```

### 3. Custom Concept Filtering

```python
# Filter concepts by type
from src.models.concept import ConceptType

term_concepts = [c for c in compiler.extracted_concepts
                if c.type == ConceptType.TERM]

# Filter by confidence
high_confidence_concepts = [c for c in compiler.extracted_concepts
                           if c.confidence > 0.8]
```

### 4. Custom Output Generation

```python
# Generate custom outputs
for concept in compiler.extracted_concepts:
    # Generate article
    article = compiler.article_generator.generate_article(
        concept, compiler.extracted_concepts
    )

    # Generate backlinks
    backlinks = compiler.backlink_generator.generate_backlinks(
        concept, compiler.extracted_concepts
    )

    # Save custom output
    output = f"# {concept.name}\n\n{article}\n\n{backlinks}"
    output_path = os.path.join(config.output_dir, f"concept_{concept.name}.md")
    write_file(output_path, output)
```

### 5. Error Handling

```python
try:
    results = compiler.compile()
except Exception as e:
    print(f"Compilation failed: {e}")

    # Check for errors in results
    if 'errors' in results:
        for error in results['errors']:
            print(f"Error: {error}")
```

## Troubleshooting

### Common Issues

#### 1. No Documents Found

**Problem**: `processed_files` is 0

**Solutions**:
- Check that `source_dir` exists and contains markdown files
- Verify `file_patterns` match your file extensions
- Ensure `recursive_processing` is set correctly

```python
# Check file discovery
from src.utils.file_ops import find_markdown_files

files = find_markdown_files(config.source_dir)
print(f"Found {len(files)} files: {files}")
```

#### 2. No Concepts Extracted

**Problem**: `extracted_concepts` is 0

**Solutions**:
- Check `min_confidence_threshold` setting
- Verify document content contains extractable concepts
- Check AI API configuration if using AI-based extraction

```python
# Check document processing
for document in compiler.processed_documents:
    print(f"Document: {document.path}")
    print(f"Content length: {len(document.content)}")
    print(f"Sections: {len(document.sections)}")
```

#### 3. Permission Errors

**Problem**: Cannot write to output directory

**Solutions**:
- Ensure output directory exists and is writable
- Check file permissions
- Use absolute paths

```python
# Create output directory
import os
os.makedirs(config.output_dir, exist_ok=True)

# Check permissions
if os.access(config.output_dir, os.W_OK):
    print("Output directory is writable")
else:
    print("Output directory is not writable")
```

#### 4. Memory Issues

**Problem**: Out of memory with large documents

**Solutions**:
- Reduce `max_file_size` setting
- Reduce `max_concepts_per_document`
- Process documents in smaller batches

```python
# Process documents in batches
batch_size = 10
for i in range(0, len(documents), batch_size):
    batch = documents[i:i + batch_size]
    # Process batch...
```

### Debug Mode

```python
# Enable verbose logging
config = Config(verbose_output=True)
compiler = KnowledgeCompiler(config)

# Run with detailed output
results = compiler.compile()

# Check detailed statistics
stats = compiler.get_processing_statistics()
print(f"Detailed statistics: {stats}")
```

### Logging

The system provides comprehensive logging:

```python
import logging

# Get logger
logger = logging.getLogger('src.main')

# Log levels (controlled by config)
# DEBUG: Detailed diagnostic information
# INFO: General information about compilation progress
# WARNING: Important warnings that don't stop execution
# ERROR: Serious errors that affect compilation
```

### Performance Optimization

#### 1. Configuration Optimization

```python
# For better performance:
config = Config(
    max_file_size=5 * 1024 * 1024,  # Reduce file size limit
    max_concepts_per_document=15,   # Reduce concepts per document
    generate_backlinks=False,        # Disable unnecessary features
    verbose_output=False           # Reduce logging overhead
)
```

#### 2. Parallel Processing (Future Enhancement)

Note: Parallel processing is planned for future versions to improve performance with large document sets.

#### 3. Caching (Future Enhancement)

Note: Result caching is planned to improve performance for repeated compilations.

## Best Practices

### 1. Document Organization

- Use consistent markdown formatting
- Include frontmatter with relevant metadata
- Use descriptive headings and clear structure
- Keep documents focused on specific topics

### 2. Configuration Management

- Use separate configuration files for different environments
- Validate configuration before processing
- Save configuration with your processed outputs
- Document custom configuration settings

### 3. Quality Control

- Use interactive mode for critical documents
- Review extracted concepts for accuracy
- Test configuration changes with small document sets
- Monitor compilation logs for issues

### 4. Performance Considerations

- Process documents in manageable batches
- Use appropriate file size limits
- Enable only necessary output features
- Regularly clean up temporary files

### 5. Integration

- Integrate with existing knowledge management systems
- Use consistent naming conventions
- Maintain backup of original documents
- Document your processing pipeline

## Support

For additional support:
1. Check the troubleshooting section
2. Review the test files in the `tests/` directory
3. Examine example configurations in the repository
4. File issues on the project repository