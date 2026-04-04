# Knowledge Compiler Usage Guide

This guide provides detailed instructions for using the Knowledge Compiler to process and transform your markdown documents into a structured knowledge base.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Configuration](#configuration)
3. [Command Line Usage](#command-line-usage)
4. [Programmatic Usage](#programmatic-usage)
5. [Interactive Mode](#interactive-mode)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.8+
- Required dependencies (see `requirements.txt`)
- Source markdown documents
- Output directory for processed content

### Basic Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your settings:**
   ```json
   {
     "source_dir": "./docs",
     "output_dir": "./wiki",
     "interactive_mode": true,
     "verbose_output": true
   }
   ```

3. **Run the compiler:**
   ```python
   from src.main import KnowledgeCompiler

   compiler = KnowledgeCompiler()
   results = compiler.compile()
   ```

## Configuration

### Configuration File Structure

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

### CLI Arguments (Future Enhancement)

Note: Full CLI interface with argparse is planned for future versions. Currently, you need to use the programmatic interface.

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