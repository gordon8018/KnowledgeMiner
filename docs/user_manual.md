# Knowledge Compiler User Manual

Complete guide for using the Knowledge Compiler system.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Basic Usage](#basic-usage)
6. [Advanced Features](#advanced-features)
7. [Monitoring and Debugging](#monitoring-and-debugging)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Introduction

The Knowledge Compiler is an intelligent system that transforms unstructured documents into a well-organized wiki with automatic concept extraction, relationship mapping, and insight management.

**Key Features:**

- **Automatic Concept Extraction**: Identifies and extracts key concepts from documents
- **Relationship Mapping**: Maps relationships between concepts automatically
- **Insight Management**: Discovers and propagates insights through the knowledge graph
- **Quality Assurance**: Monitors and maintains wiki quality automatically
- **Performance Optimization**: Multi-level caching and query optimization
- **Production Monitoring**: Comprehensive metrics and alerting

---

## Installation

### Requirements

- Python 3.10 or higher
- Git
- 2GB RAM minimum (4GB recommended)
- 500MB disk space

### Installation Steps

```bash
# Clone repository
git clone https://github.com/your-org/knowledge-compiler.git
cd knowledge-compiler

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m pytest tests/ -v
```

---

## Quick Start

### Basic Compilation

Create a simple configuration file `config.yaml`:

```yaml
source_dir: ./documents
target_dir: ./wiki
categories:
  - "技术指标"
  - "战法"
extraction:
  min_confidence: 0.6
  max_concepts: 50
interactive_mode: false
```

Run the compiler:

```bash
python -m src.main_cli --config config.yaml
```

### Using Python API

```python
from src.main import KnowledgeCompiler

config = {
    "source_dir": "./documents",
    "target_dir": "./wiki",
    "categories": ["技术指标", "战法"]
}

compiler = KnowledgeCompiler(config)
compiler.compile()
```

---

## Configuration

### Configuration Options

```yaml
# Source and target directories
source_dir: "./documents"          # Required: Source documents directory
target_dir: "./wiki"               # Required: Output wiki directory

# Document categories
categories:                        # Optional: Document categories
  - "技术指标"
  - "战法"

# Extraction settings
extraction:
  min_confidence: 0.6              # Minimum confidence for concept extraction (0.0-1.0)
  max_concepts: 50                 # Maximum concepts to extract per document
  min_relationships: 3             # Minimum relationships to maintain

# Insight settings
insights:
  enabled: true                    # Enable insight management
  max_hops: 2                      # Maximum hops for insight propagation
  backfill_batch_size: 10          # Batch size for insight backfill

# Quality settings
quality:
  enabled: true                    # Enable quality monitoring
  max_stale_days: 90              # Days before content is considered stale
  min_quality_score: 0.7          # Minimum quality score threshold

# Performance settings
performance:
  cache_enabled: true              # Enable caching
  cache_ttl: 3600                  # Cache TTL in seconds
  max_workers: 4                   # Maximum parallel workers

# Monitoring settings
monitoring:
  enabled: true                    # Enable monitoring
  log_level: INFO                  # Log level (DEBUG, INFO, WARNING, ERROR)
  log_file: logs/compiler.log      # Log file path
  metrics_enabled: true            # Enable metrics collection
  metrics_port: 9090              # Metrics server port
```

### Environment Variables

```bash
# Compiler settings
export KNOWLEDGE_COMPILER_CONFIG=/path/to/config.yaml
export KNOWLEDGE_COMPILER_LOG_LEVEL=INFO
export KNOWLEDGE_COMPILER_CACHE_DIR=/tmp/kc_cache

# LLM settings
export LLM_API_KEY=your_api_key_here
export LLM_MODEL=gpt-4
export LLM_MAX_TOKENS=2000

# Performance settings
export KNOWLEDGE_COMPILER_MAX_WORKERS=4
export KNOWLEDGE_COMPILER_CACHE_TTL=3600
```

---

## Basic Usage

### Command Line Interface

```bash
# Compile documents
python -m src.main_cli --config config.yaml

# Compile with verbose output
python -m src.main_cli --config config.yaml --verbose

# Compile specific document
python -m src.main_cli --config config.yaml --document path/to/document.md

# Run quality check
python -m src.main_cli --config config.yaml --quality-check

# Show statistics
python -m src.main_cli --config config.yaml --stats
```

### Python API

#### Basic Compilation

```python
from src.main import KnowledgeCompiler

config = {
    "source_dir": "./documents",
    "target_dir": "./wiki",
    "categories": ["技术指标", "战法"]
}

compiler = KnowledgeCompiler(config)
compiler.compile()
```

#### Compile Single Document

```python
result = compiler.compile_document("documents/example.md")
print(f"Extracted {len(result['concepts'])} concepts")
print(f"Found {len(result['relationships'])} relationships")
```

#### Get Statistics

```python
stats = compiler.get_statistics()
print(f"Total documents: {stats['total_documents']}")
print(f"Total concepts: {stats['total_concepts']}")
print(f"Total relationships: {stats['total_relationships']}")
```

---

## Advanced Features

### Custom Concept Extraction

```python
from src.discovery.extractors.concept_extractor import ConceptExtractor

extractor = ConceptExtractor(
    llm_client=llm,
    min_confidence=0.7,
    max_concepts=100
)

# Custom extraction
result = extractor.extract(
    text="Custom document text...",
    document_id="custom_doc_001",
    context={"domain": "finance"}
)
```

### Insight Management

```python
from src.wiki.insight.manager import InsightManager

manager = InsightManager(wiki_core=wiki, llm_client=llm)

# Create insight
insight = manager.create_insight(
    title="Important Pattern",
    description="This pattern indicates strong reversal",
    related_concepts=["弱转强", "形态"],
    impact_score=0.9,
    novelty_score=0.8,
    actionability_score=0.7
)

# Propagate through knowledge graph
manager.propagate_insight(insight, max_hops=2)

# Schedule for backfill
manager.schedule_insight(insight)
```

### Quality Monitoring

```python
from src.wiki.quality.monitor import QualityMonitor

monitor = QualityMonitor(wiki_core=wiki)

# Run health check
result = await monitor.run_health_check()
print(f"Wiki status: {result['status']}")
print(f"Quality score: {result['score']:.2f}")

# Check specific issues
orphans = await monitor.check_orphan_pages()
broken_links = await monitor.check_broken_links()

# Generate quality report
from src.wiki.quality.reporter import QualityReporter
reporter = QualityReporter(wiki_core=wiki)
report = await reporter.generate_report(result)
```

### Performance Optimization

```python
from src.performance.cache import CacheManager
from src.performance.optimizer import PerformanceOptimizer

# Setup caching
cache = CacheManager(l1_max_size=1000, l2_enabled=True)

# Optimize queries
optimizer = PerformanceOptimizer(wiki_core=wiki, cache_manager=cache)

# Use optimized query
page = await optimizer.optimize_query_get_page("concept:test")

# Batch processing
results = await optimizer.batch_process_pages(
    page_ids=["page1", "page2", "page3"],
    batch_size=10
)
```

---

## Monitoring and Debugging

### Structured Logging

```python
from src.monitoring.structured_logger import get_logger

logger = get_logger("my_module", log_file="app.log")

# Context-aware logging
with logger.context(operation="compile", document_id="doc_001"):
    logger.info("Starting compilation")
    # ... processing ...
    logger.info("Compilation complete", duration_ms=150)

# Performance timing
with logger.measure_time("document_processing"):
    process_document()
```

### Metrics Collection

```python
from src.monitoring.metrics import get_metrics_registry

registry = get_metrics_registry()

# Track operations
counter = registry.counter("documents_processed", "Documents processed")
counter.inc(labels={"status": "success"})

# Track duration
histogram = registry.histogram("processing_duration", "Processing duration")
histogram.observe(0.23)

# Export metrics
metrics = registry.export_metrics()
```

### Alert Management

```python
from src.monitoring.alerts import AlertManager, AlertRule, AlertSeverity

manager = AlertManager()

# Setup alert rule
rule = AlertRule(
    name="high_error_rate",
    description="Error rate exceeds threshold",
    metric_name="error_rate",
    condition="gt",
    threshold=5.0,
    severity=AlertSeverity.WARNING
)
manager.add_rule(rule)

# Monitor and alert
current_error_rate = get_current_error_rate()
alert = manager.evaluate_rule(rule, current_error_rate)
if alert:
    manager.send_alert(alert)
```

### Debugging Tips

1. **Enable Debug Logging**

```yaml
monitoring:
  log_level: DEBUG
```

2. **Run Quality Checks**

```bash
python -m src.main_cli --config config.yaml --quality-check
```

3. **Inspect Wiki Structure**

```python
from src.wiki.core import WikiCore

wiki = WikiCore(wiki_path="./wiki")

# List all pages
pages = wiki.list_pages()
print(f"Total pages: {len(pages)}")

# Inspect specific page
page = wiki.get_page("concept:test")
print(f"Page title: {page.title}")
print(f"Page content: {page.content[:100]}...")
```

4. **Check Cache Effectiveness**

```python
stats = cache.get_stats()
print(f"L1 hit rate: {stats['l1_hit_rate']:.2%}")
print(f"Total requests: {stats['total_requests']}")
```

---

## Troubleshooting

### Common Issues

#### 1. Low Concept Extraction Confidence

**Problem**: Concepts not being extracted or low confidence scores.

**Solutions**:
- Lower `min_confidence` threshold in configuration
- Improve document formatting and structure
- Use domain-specific categories
- Increase `max_concepts` limit

```yaml
extraction:
  min_confidence: 0.5  # Lower threshold
  max_concepts: 100    # Increase limit
```

#### 2. Memory Issues

**Problem**: System runs out of memory when processing large documents.

**Solutions**:
- Reduce batch sizes
- Enable caching with appropriate limits
- Process documents in smaller batches
- Increase system memory

```yaml
performance:
  cache_enabled: true
  cache_ttl: 3600
  max_workers: 2  # Reduce parallelism
```

#### 3. Slow Performance

**Problem**: Compilation takes too long.

**Solutions**:
- Enable caching
- Increase worker count
- Use batch processing
- Optimize query patterns

```yaml
performance:
  cache_enabled: true
  max_workers: 8  # Increase workers
```

#### 4. Quality Issues

**Problem**: Generated wiki has quality issues.

**Solutions**:
- Run quality checks regularly
- Configure quality thresholds
- Fix reported issues
- Review quality reports

```bash
# Run quality check
python -m src.main_cli --config config.yaml --quality-check

# Generate quality report
python -m src.main_cli --config config.yaml --quality-report
```

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `DocumentProcessingError` | Invalid document format | Check document format and encoding |
| `WikiCoreError` | Wiki initialization failed | Check target directory permissions |
| `ExtractionError` | LLM API error | Check API key and rate limits |
| `QualityError` | Quality check failed | Review quality report for details |
| `CacheError` | Cache initialization failed | Check cache directory permissions |

### Getting Help

1. **Check Logs**: Review logs in `logs/compiler.log`
2. **Enable Debug Mode**: Set `log_level: DEBUG` in configuration
3. **Run Diagnostics**: Use `--diagnose` flag to run system diagnostics
4. **Review Documentation**: Check API reference and troubleshooting guide
5. **Report Issues**: Use GitHub issues with detailed error information

---

## Best Practices

### Document Organization

1. **Use Consistent Naming**
   - Use descriptive filenames
   - Follow naming conventions
   - Avoid special characters

2. **Structure Content**
   - Use markdown headers (# ## ###)
   - Organize content logically
   - Include metadata when possible

3. **Optimize for Extraction**
   - Use clear, concise language
   - Define concepts explicitly
   - Provide context

### Performance Optimization

1. **Enable Caching**
   ```yaml
   performance:
     cache_enabled: true
     cache_ttl: 3600
   ```

2. **Batch Processing**
   ```python
   # Process multiple documents at once
   results = await compiler.compile_batch(document_paths)
   ```

3. **Monitor Performance**
   ```python
   # Track metrics
   stats = optimizer.get_performance_summary()
   print(f"Avg query time: {stats['avg_query_time']:.3f}s")
   ```

### Quality Maintenance

1. **Regular Quality Checks**
   ```bash
   # Run weekly quality checks
   python -m src.main_cli --config config.yaml --quality-check
   ```

2. **Address Issues Promptly**
   - Fix orphan pages
   - Repair broken links
   - Update stale content

3. **Monitor Metrics**
   - Track quality scores
   - Monitor error rates
   - Review performance metrics

### Security

1. **API Keys**
   - Store in environment variables
   - Never commit to version control
   - Rotate regularly

2. **File Permissions**
   - Restrict write access to target directory
   - Use appropriate file permissions
   - Secure sensitive documents

3. **Logging**
   - Avoid logging sensitive information
   - Use appropriate log levels
   - Regular log rotation

---

## Additional Resources

- [API Reference](api/api_reference.md) - Complete API documentation
- [Deployment Guide](deployment.md) - Production deployment guide
- [Migration Guide](migration.md) - Version migration guide
- [Troubleshooting Guide](troubleshooting.md) - Detailed troubleshooting
- [GitHub Repository](https://github.com/your-org/knowledge-compiler) - Source code and issues

---

## Version

Current version: **v1.0.0**

For version history and changes, see [CHANGELOG.md](CHANGELOG.md).
