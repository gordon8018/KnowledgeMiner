# Knowledge Compiler

A comprehensive system for converting raw markdown documents into structured knowledge bases with automatic concept extraction, categorization, and relationship mapping.

## Features

- **Document Analysis**: Parse and structure markdown documents with frontmatter
- **Concept Extraction**: Automatically identify and extract key concepts from content
- **Intelligent Indexing**: Organize documents by categories and relationships
- **Content Generation**: Generate summaries, articles, and backlinks from extracted concepts
- **Interactive Review**: Review and confirm extracted concepts interactively
- **Flexible Configuration**: Extensive configuration options for customization
- **Error Handling**: Robust error handling and logging throughout the pipeline

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from src.main import KnowledgeCompiler
from src.config import Config

# Create compiler with default configuration
compiler = KnowledgeCompiler()

# Compile all documents in source directory
results = compiler.compile()

print(f"Processed {results['processed_files']} files")
print(f"Extracted {results['extracted_concepts']} concepts")
```

### Configuration

```python
from src.config import Config

# Create custom configuration
config = Config(
    source_dir="./docs",
    output_dir="./output",
    file_patterns=["*.md", "*.markdown"],
    interactive_mode=True,
    verbose_output=True
)

# Initialize compiler with custom config
compiler = KnowledgeCompiler(config)
```

### Interactive Mode

```python
# Run interactive compilation session
results = compiler.run_interactive_session()

# Review concepts manually
confirmed_concepts = compiler.review_concepts(extracted_concepts)
```

## Configuration Options

The `Config` class provides comprehensive configuration options:

```python
@dataclass
class Config:
    # Source and output directories
    source_dir: str = "."
    output_dir: str = "output"
    template_dir: str = "templates"

    # Processing settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    recursive_processing: bool = True
    file_patterns: List[str] = None

    # AI/API configuration
    api_key: Optional[str] = None
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000

    # Analysis configuration
    min_confidence_threshold: float = 0.6
    max_concepts_per_document: int = 20
    enable_relation_extraction: bool = True

    # Output configuration
    generate_backlinks: bool = True
    generate_summaries: bool = True
    generate_articles: bool = True
    output_format: str = "markdown"

    # UI/Interaction configuration
    interactive_mode: bool = True
    verbose_output: bool = False
    quiet_mode: bool = False
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

The Knowledge Compiler consists of several key components:

### Analyzers
- **DocumentAnalyzer**: Parses and structures markdown documents
- **HashCalculator**: Creates unique identifiers for documents

### Extractors
- **ConceptExtractor**: Identifies and extracts key concepts from text
- Uses pattern matching and AI analysis
- Supports multiple concept types (terms, indicators, strategies, etc.)

### Generators
- **ArticleGenerator**: Creates detailed articles from extracted concepts
- **SummaryGenerator**: Generates document summaries
- **BacklinkGenerator**: Creates cross-references between concepts

### Indexers
- **FileIndexer**: Manages document lookup and organization
- **CategoryIndexer**: Organizes documents by categories and tags
- **RelationMapper**: Maps relationships between concepts

### Utilities
- **FileOps**: Essential file operations and markdown discovery
- **MarkdownUtils**: Markdown parsing and processing utilities

## Data Models

### Document
Represents a structured markdown document:
```python
@dataclass
class Document:
    path: str
    hash: str
    metadata: Dict[str, Any]
    sections: List[Section]
    content: str
```

### Concept
Represents an extracted concept:
```python
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

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_integration.py

# Run with coverage
pytest --cov=src --cov-report=term-missing
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.