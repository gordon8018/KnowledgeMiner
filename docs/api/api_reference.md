# Knowledge Compiler API Reference

Complete API documentation for the Knowledge Compiler system.

## Table of Contents

- [Core API](#core-api)
  - [KnowledgeCompiler](#knowledgecompiler)
  - [WikiCore](#wikicore)
- [Discovery API](#discovery-api)
  - [ConceptExtractor](#conceptextractor)
  - [RelationshipMapper](#relationshipmapper)
  - [InsightManager](#insightmanager)
- [Monitoring API](#monitoring-api)
  - [StructuredLogger](#structuredlogger)
  - [MetricsRegistry](#metricsregistry)
  - [AlertManager](#alertmanager)
- [Quality API](#quality-api)
  - [QualityMonitor](#qualitymonitor)
  - [IssueClassifier](#issueclassifier)
- [Performance API](#performance-api)
  - [CacheManager](#cachemanager)
  - [PerformanceOptimizer](#performanceoptimizer)

---

## Core API

### KnowledgeCompiler

Main orchestrator for knowledge compilation workflow.

```python
from src.main import KnowledgeCompiler

config = {
    "source_dir": "/path/to/documents",
    "target_dir": "/path/to/wiki",
    "categories": ["技术指标", "战法"],
    "extraction": {
        "min_confidence": 0.5,
        "max_concepts": 50
    },
    "interactive_mode": False
}

compiler = KnowledgeCompiler(config)
compiler.compile()
```

**Configuration Options:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_dir` | str | Yes | Directory containing source documents |
| `target_dir` | str | Yes | Directory for wiki output |
| `categories` | List[str] | No | Document categories for classification |
| `extraction.min_confidence` | float | No | Minimum confidence for concept extraction (default: 0.5) |
| `extraction.max_concepts` | int | No | Maximum concepts to extract per document (default: 50) |
| `interactive_mode` | bool | No | Enable interactive prompts (default: False) |

**Methods:**

- `compile()` -> None: Execute the full compilation pipeline
- `compile_document(file_path: str)` -> dict: Compile a single document
- `get_statistics()` -> dict: Get compilation statistics

---

### WikiCore

Core wiki operations and knowledge graph management.

```python
from src.wiki.core import WikiCore

wiki = WikiCore(wiki_path="/path/to/wiki")

# Create or update pages
wiki.create_page(
    page_id="concept:test",
    title="Test Concept",
    content="# Test Concept\n\nDescription here...",
    metadata={"category": "技术指标"}
)

# Query pages
page = wiki.get_page("concept:test")
related = wiki.get_related_concepts("test")

# Graph operations
wiki.add_relationship("concept_a", "concept_b", "related_to")
```

**Methods:**

- `create_page(page_id, title, content, metadata)`: Create a new wiki page
- `get_page(page_id)`: Retrieve a page by ID
- `update_page(page_id, **kwargs)`: Update page content or metadata
- `delete_page(page_id)`: Delete a page
- `search(query)`: Search pages by content
- `get_related_concepts(concept)`: Get related concepts from knowledge graph
- `add_relationship(from_id, to_id, relation_type)`: Add relationship to graph

---

## Discovery API

### ConceptExtractor

Extract concepts and relationships from documents.

```python
from src.discovery.extractors.concept_extractor import ConceptExtractor

extractor = ConceptExtractor(llm_client=llm, min_confidence=0.6)

result = extractor.extract(
    text="「弱转强」是重要的形态。",
    document_id="doc_001"
)

# Result contains:
# - concepts: List of extracted concepts
# - relationships: List of relationships
# - confidence: Extraction confidence score
```

**Extraction Result:**

```python
{
    "concepts": [
        {
            "name": "弱转强",
            "confidence": 0.9,
            "category": "战法",
            "aliases": ["弱势转强势"]
        }
    ],
    "relationships": [
        {
            "from": "弱转强",
            "to": "形态",
            "type": "is_a",
            "confidence": 0.8
        }
    ],
    "confidence": 0.85
}
```

---

### RelationshipMapper

Map relationships between concepts in the knowledge graph.

```python
from src.discovery.relationships.mapper import RelationshipMapper

mapper = RelationshipMapper(wiki_core=wiki)

# Map relationships for a concept
relationships = mapper.map_relationships("弱转强")

# Validate relationships
is_valid = mapper.validate_relationship("弱转强", "形态", "is_a")
```

**Relationship Types:**

- `is_a`: Hierarchical (A is a type of B)
- `related_to`: General association
- `depends_on`: Dependency relationship
- `contradicts`: Contradiction
- `prerequisite_for`: Prerequisite relationship

---

### InsightManager

Manage insights and their propagation through the knowledge graph.

```python
from src.wiki.insight.manager import InsightManager

manager = InsightManager(wiki_core=wiki, llm_client=llm)

# Create insight
insight = manager.create_insight(
    title="Weak to Strong Pattern",
    description="Important reversal pattern",
    related_concepts=["弱转强", "形态"],
    impact_score=0.8,
    novelty_score=0.7,
    actionability_score=0.9
)

# Propagate insight
manager.propagate_insight(insight, max_hops=2)

# Schedule insight for backfill
manager.schedule_insight(insight)
```

---

## Monitoring API

### StructuredLogger

Structured logging with JSON formatting.

```python
from src.monitoring.structured_logger import get_logger

logger = get_logger("my_module", log_file="app.log")

# Basic logging
logger.info("Processing document", document_id="doc_001")

# Context-aware logging
with logger.context(operation="compile", document_id="doc_001"):
    logger.info("Starting compilation")

# Performance timing
with logger.measure_time("document_processing"):
    process_document()

# Different log levels
logger.debug("Detailed debug info")
logger.info("Informational message")
logger.warning("Warning condition")
logger.error("Error occurred", error_code=500)
logger.critical("Critical failure")
```

**Log Levels:**

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for error events
- `CRITICAL`: Critical error messages indicating severe problems

---

### MetricsRegistry

Central registry for Prometheus-style metrics.

```python
from src.monitoring.metrics import get_metrics_registry

registry = get_metrics_registry()

# Create metrics
counter = registry.counter("documents_processed", "Total documents processed")
gauge = registry.gauge("active_connections", "Active database connections")
histogram = registry.histogram("request_duration", "Request duration", buckets=[0.1, 0.5, 1.0, 5.0])
summary = registry.summary("response_size", "Response size in bytes")

# Use metrics
counter.inc(labels={"status": "success"})
counter.inc(5, labels={"status": "error"})

gauge.set(10)
gauge.inc()
gauge.dec(2)

histogram.observe(0.23)

summary.observe(1024)
summary.observe(2048)

# Export metrics
metrics_data = registry.export_metrics()
```

**Metric Types:**

- **Counter**: Monotonically increasing counter
- **Gauge**: Arbitrary value that can increase or decrease
- **Histogram**: Counts observations in configurable buckets
- **Summary**: Calculates quantiles over a sliding window

---

### AlertManager

Manage alert rules and notifications.

```python
from src.monitoring.alerts import AlertManager, AlertRule, AlertSeverity

manager = AlertManager()

# Add alert rule
rule = AlertRule(
    name="high_error_rate",
    description="High error rate detected",
    metric_name="error_rate",
    condition="gt",
    threshold=10.0,
    severity=AlertSeverity.CRITICAL,
    duration_seconds=60,  # Condition must persist for 60 seconds
    cooldown_seconds=300  # Minimum 5 minutes between alerts
)
manager.add_rule(rule)

# Evaluate rule
current_value = get_error_rate()
alert = manager.evaluate_rule(rule, current_value)
if alert:
    manager.send_alert(alert)

# Alert lifecycle
manager.acknowledge_alert(alert.id, acknowledged_by="admin")
manager.resolve_alert(alert.id)

# Get alert stats
stats = manager.get_alert_stats()
```

**Alert Conditions:**

- `gt`: Greater than threshold
- `lt`: Less than threshold
- `eq`: Equal to threshold
- `gte`: Greater than or equal to threshold
- `lte`: Less than or equal to threshold

**Alert Severities:**

- `INFO`: Informational
- `WARNING`: Warning
- `ERROR`: Error
- `CRITICAL`: Critical

---

## Quality API

### QualityMonitor

Monitor wiki health and quality.

```python
from src.wiki.quality.monitor import QualityMonitor

monitor = QualityMonitor(wiki_core=wiki)

# Run health check
result = await monitor.run_health_check()

# Check specific issues
orphans = await monitor.check_orphan_pages()
broken_links = await monitor.check_broken_links()
duplicates = await monitor.check_duplicate_content()

# Check staleness
stale_pages = await monitor.check_staleness(max_age_days=90)
```

**Health Check Result:**

```python
{
    "status": "healthy",  # healthy, degraded, unhealthy
    "orphan_pages": 0,
    "broken_links": 0,
    "duplicate_content": 0,
    "stale_content": 5,
    "missing_metadata": 2,
    "low_quality": 1,
    "score": 0.92
}
```

---

### IssueClassifier

Classify quality issues by severity and complexity.

```python
from src.wiki.quality.classifier import IssueClassifier

classifier = IssueClassifier()

# Classify issue
classified = classifier.classify_issue(issue)

# Result includes:
# - category: Issue category
# - complexity: Repair complexity
# - approach: Recommended repair approach
# - priority_score: Priority score (0-1)
```

**Issue Categories:**

- **Content Issues**: Orphan pages, duplicate content, stale content
- **Structure Issues**: Broken links, circular references
- **Metadata Issues**: Missing metadata, incomplete metadata
- **Quality Issues**: Low quality content, formatting issues

---

## Performance API

### CacheManager

Multi-level caching system.

```python
from src.performance.cache import CacheManager

cache = CacheManager(l1_max_size=1000, l2_enabled=True)

# Set and get values
cache.set("key1", "value1", ttl=3600)  # 1 hour TTL
value = cache.get("key1")

# Pattern-based invalidation
cache.invalidate_pattern("user:*")

# Get cache statistics
stats = cache.get_stats()
print(f"L1 hit rate: {stats['l1_hit_rate']:.2%}")
```

**Cache Levels:**

- **L1 Cache**: In-memory cache with fast access
- **L2 Cache**: Disk-based persistent cache

---

### PerformanceOptimizer

Query optimization and concurrent processing.

```python
from src.performance.optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer(wiki_core=wiki, cache_manager=cache)

# Optimize query
page = await optimizer.optimize_query_get_page("concept:test")

# Batch processing
results = await optimizer.batch_process_pages(
    page_ids=["page1", "page2", "page3"],
    batch_size=10
)

# Concurrent health checks
results = await optimizer.run_concurrent_health_checks(monitor)
```

**Performance Features:**

- Query result caching
- Batch processing for bulk operations
- Concurrent execution with asyncio
- Performance monitoring and metrics

---

## Error Handling

All API methods follow consistent error handling:

```python
from src.exceptions import (
    DocumentProcessingError,
    WikiCoreError,
    ExtractionError,
    QualityError
)

try:
    result = compiler.compile_document(file_path)
except DocumentProcessingError as e:
    logger.error(f"Failed to process document: {e}")
    # Handle document processing errors
except WikiCoreError as e:
    logger.error(f"Wiki core error: {e}")
    # Handle wiki core errors
except ExtractionError as e:
    logger.error(f"Extraction failed: {e}")
    # Handle extraction errors
```

---

## Configuration

Environment variables and configuration files:

```bash
# Environment variables
export KNOWLEDGE_COMPILER_LOG_LEVEL=INFO
export KNOWLEDGE_COMPILER_CACHE_DIR=/path/to/cache
export KNOWLEDGE_COMPILER_MAX_WORKERS=4

# Configuration file (config.yaml)
compiler:
  source_dir: /path/to/documents
  target_dir: /path/to/wiki
  extraction:
    min_confidence: 0.6
    max_concepts: 50
  monitoring:
    enabled: true
    metrics_port: 9090
```

---

## API Versioning

Current API version: **v1.0.0**

API follows Semantic Versioning 2.0.0:
- MAJOR version: Incompatible API changes
- MINOR version: Backwards-compatible functionality
- PATCH version: Backwards-compatible bug fixes
