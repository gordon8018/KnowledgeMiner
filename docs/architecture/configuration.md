# Configuration System

This document describes the configuration management system for the Knowledge Compiler.

## Overview

The configuration system uses a hierarchical, modular design based on Pydantic Settings. It supports:

- YAML-based configuration files
- Environment variable overrides
- Default values for all settings
- Type validation and conversion
- Easy programmatic access

```mermaid
graph TD
    Config[Config] --> LLM[LLMConfig]
    Config --> Storage[StorageConfig]
    Config --> Processing[ProcessingConfig]
    Config --> Quality[QualityConfig]
    Config --> Logging[LoggingConfig]

    YAML[config.yaml] -->|loads| Config
    ENV[Environment Variables] -->|override| Config
```

## Configuration Classes

### LLMConfig

Configuration for LLM provider settings.

**Environment Prefix:** `KC_LLM_`

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | `str` | `"anthropic"` | LLM provider to use (anthropic or openai) |
| `model` | `str` | `"claude-sonnet-4-6"` | Model name/identifier |
| `api_key_env` | `str` | `"ANTHROPIC_API_KEY"` | Environment variable containing API key |
| `temperature` | `float` | `0.3` | Sampling temperature (0.0 to 1.0) |
| `max_tokens` | `int` | `4096` | Maximum tokens in response |
| `timeout` | `int` | `60` | Request timeout in seconds |
| `max_retries` | `int` | `3` | Maximum retry attempts for failed requests |

**Properties:**

- `api_key` (str): Retrieves the actual API key from the environment

**Example:**

```python
from src.core.config import LLMConfig

# Use defaults
llm_config = LLMConfig()
print(llm_config.api_key)  # Gets from ANTHROPIC_API_KEY env var

# Or override programmatically
llm_config = LLMConfig(
    provider="openai",
    model="gpt-4-turbo",
    api_key_env="OPENAI_API_KEY",
    temperature=0.5
)
```

**Environment Variables:**

```bash
# Override via environment
export KC_LLM_PROVIDER=openai
export KC_LLM_MODEL=gpt-4-turbo
export KC_LLM_TEMPERATURE=0.7
export KC_LLM_MAX_TOKENS=8192
```

### StorageConfig

Configuration for storage and file system settings.

**Environment Prefix:** `KC_STORAGE_`

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `raw_dir` | `str` | `"./raw"` | Directory for raw input files |
| `wiki_dir` | `str` | `"./wiki"` | Directory for wiki output |
| `cache_dir` | `str` | `"./cache"` | Directory for cache files |
| `database_url` | `str` | `"sqlite:///./knowledge.db"` | Database connection URL |
| `enable_backups` | `bool` | `True` | Enable automatic backups |

**Example:**

```python
from src.core.config import StorageConfig

storage = StorageConfig(
    raw_dir="/data/raw",
    wiki_dir="/data/wiki",
    cache_dir="/data/cache",
    database_url="postgresql://user:pass@localhost/knowledge"
)
```

**Environment Variables:**

```bash
export KC_STORAGE_RAW_DIR=/data/raw
export KC_STORAGE_WIKI_DIR=/data/wiki
export KC_STORAGE_DATABASE_URL=postgresql://localhost/db
```

### ProcessingConfig

Configuration for document processing behavior.

**Environment Prefix:** `KC_PROCESSING_`

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_file_size` | `int` | `10485760` | Maximum file size to process (10MB) |
| `batch_size` | `int` | `10` | Number of files to process in each batch |
| `parallel_workers` | `int` | `4` | Number of parallel processing workers |
| `incremental_updates` | `bool` | `True` | Enable incremental processing |
| `cache_embeddings` | `bool` | `True` | Cache embeddings to avoid recomputation |

**Example:**

```python
from src.core.config import ProcessingConfig

processing = ProcessingConfig(
    max_file_size=20 * 1024 * 1024,  # 20MB
    batch_size=20,
    parallel_workers=8
)
```

**Environment Variables:**

```bash
export KC_PROCESSING_MAX_FILE_SIZE=20971520
export KC_PROCESSING_BATCH_SIZE=20
export KC_PROCESSING_PARALLEL_WORKERS=8
```

### QualityConfig

Configuration for quality thresholds.

**Environment Prefix:** `KC_QUALITY_`

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min_document_quality` | `float` | `0.6` | Minimum quality score for documents |
| `min_concept_confidence` | `float` | `0.7` | Minimum confidence for concepts |
| `min_relation_confidence` | `float` | `0.6` | Minimum confidence for relations |

**Example:**

```python
from src.core.config import QualityConfig

quality = QualityConfig(
    min_document_quality=0.7,
    min_concept_confidence=0.8,
    min_relation_confidence=0.7
)
```

**Environment Variables:**

```bash
export KC_QUALITY_MIN_DOCUMENT_QUALITY=0.7
export KC_QUALITY_MIN_CONCEPT_CONFIDENCE=0.8
```

### LoggingConfig

Configuration for logging settings.

**Environment Prefix:** `KC_LOGGING_`

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `level` | `str` | `"INFO"` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `format` | `str` | `"structured"` | Log format (structured or text) |
| `file` | `str` | `"./logs/compiler.log"` | Log file path |
| `rotation` | `str` | `"daily"` | Log rotation frequency |

**Example:**

```python
from src.core.config import LoggingConfig

logging = LoggingConfig(
    level="DEBUG",
    format="text",
    file="./logs/debug.log"
)
```

## Config Class

The main configuration class that aggregates all sub-configurations.

### Initialization

#### `Config(config_dict: Optional[Dict[str, Any]] = None)`

Create a new configuration instance.

**Parameters:**
- `config_dict`: Optional dictionary with configuration values

**Example:**

```python
from src.core.config import Config

# Use all defaults
config = Config()

# Or provide configuration
config = Config({
    "llm": {
        "provider": "openai",
        "model": "gpt-4-turbo"
    },
    "processing": {
        "batch_size": 20
    }
})
```

### Methods

#### `from_yaml(config_path: Path) -> Config`

Load configuration from a YAML file.

**Parameters:**
- `config_path`: Path to YAML configuration file

**Returns:** New Config instance

**Example:**

```python
from pathlib import Path
from src.core.config import Config

config = Config.from_yaml(Path("config.yaml"))
```

**YAML File Format:**

```yaml
# config.yaml
knowledge_compiler:
  llm:
    provider: anthropic
    model: claude-sonnet-4-6
    temperature: 0.3
    max_tokens: 4096

  storage:
    raw_dir: ./raw
    wiki_dir: ./wiki
    cache_dir: ./cache
    database_url: sqlite:///./knowledge.db

  processing:
    max_file_size: 10485760
    batch_size: 10
    parallel_workers: 4
    incremental_updates: true
    cache_embeddings: true

  quality:
    min_document_quality: 0.6
    min_concept_confidence: 0.7
    min_relation_confidence: 0.6

  logging:
    level: INFO
    format: structured
    file: ./logs/compiler.log
    rotation: daily
```

#### `to_dict() -> Dict[str, Any]`

Convert configuration to dictionary.

**Returns:** Dictionary representation of all configuration

**Example:**

```python
config_dict = config.to_dict()
# {
#     'llm': {'provider': 'anthropic', 'model': 'claude-sonnet-4-6', ...},
#     'storage': {'raw_dir': './raw', ...},
#     ...
# }
```

## Global Configuration

### `get_config(config_path: Optional[Path] = None) -> Config`

Get the global configuration instance (singleton pattern).

**Parameters:**
- `config_path`: Optional path to YAML configuration file

**Returns:** Config instance

**Behavior:**
- Creates configuration on first call
- Reuses same instance on subsequent calls
- Loads from YAML if provided and file exists
- Uses defaults otherwise

**Example:**

```python
from src.core.config import get_config
from pathlib import Path

# First call - creates config
config = get_config()

# Subsequent calls - returns same instance
config2 = get_config()
assert config is config2

# Or load from file
config = get_config(Path("config.yaml"))
```

## Configuration Loading Order

Configuration values are loaded in the following priority order (highest to lowest):

1. **Programmatic overrides** - Values passed to Config constructor
2. **Environment variables** - Values from environment (with prefix)
3. **YAML file** - Values from config.yaml
4. **Defaults** - Default values in code

```mermaid
graph LR
    A[Defaults] --> B[YAML File]
    B --> C[Environment Variables]
    C --> D[Programmatic Overrides]
    D --> E[Final Config]
```

## Usage Examples

### Basic Usage

```python
from src.core.config import get_config

# Get configuration with defaults
config = get_config()

# Access configuration sections
print(config.llm.provider)  # 'anthropic'
print(config.storage.raw_dir)  # './raw'
print(config.processing.batch_size)  # 10
print(config.quality.min_document_quality)  # 0.6
```

### Loading from YAML

```python
from pathlib import Path
from src.core.config import Config

# Load from YAML file
config = Config.from_yaml(Path("config.yaml"))

# Use the configuration
provider = config.llm.provider
model = config.llm.model
api_key = config.llm.api_key
```

### Environment Variable Overrides

```bash
# Set environment variables before running
export KC_LLM_PROVIDER=openai
export KC_LLM_MODEL=gpt-4-turbo
export KC_PROCESSING_BATCH_SIZE=20

# In Python
from src.core.config import get_config

config = get_config()
print(config.llm.provider)  # 'openai' (from env)
print(config.llm.model)  # 'gpt-4-turbo' (from env)
print(config.processing.batch_size)  # 20 (from env)
```

### Programmatic Configuration

```python
from src.core.config import Config

# Create configuration programmatically
config = Config({
    "llm": {
        "provider": "openai",
        "model": "gpt-4-turbo",
        "temperature": 0.7
    },
    "processing": {
        "batch_size": 20,
        "parallel_workers": 8
    },
    "quality": {
        "min_document_quality": 0.7
    }
})

# Use configuration
print(config.llm.temperature)  # 0.7
print(config.processing.parallel_workers)  # 8
```

### Combining Configuration Sources

```python
from pathlib import Path
from src.core.config import Config

# Load base configuration from YAML
config = Config.from_yaml(Path("config.yaml"))

# Override specific values programmatically
config.llm.temperature = 0.5
config.processing.batch_size = 15

# Or create new config with overrides
base_config = Config.from_yaml(Path("config.yaml"))
custom_config = Config({
    "llm": {"temperature": 0.5},
    "processing": {"batch_size": 15}
})
```

### Validating Configuration

```python
from src.core.config import Config

# All configuration is validated by Pydantic
try:
    config = Config({
        "llm": {
            "temperature": 1.5  # Invalid: must be <= 1.0
        }
    })
except ValidationError as e:
    print(f"Configuration error: {e}")
```

## Best Practices

1. **Use YAML for deployment**: Store configuration in `config.yaml` for reproducible deployments
2. **Environment variables for secrets**: Never commit API keys; use environment variables
3. **Document custom values**: Comment your YAML files with rationale for non-default values
4. **Validate on startup**: Check configuration validity when application starts
5. **Use sensible defaults**: Configure defaults that work for most use cases
6. **Version control config**: Commit your `config.yaml` (without secrets) to version control

## Example Configuration Files

### Development Configuration

```yaml
# config.dev.yaml
knowledge_compiler:
  llm:
    provider: anthropic
    model: claude-sonnet-4-6
    temperature: 0.3
    max_tokens: 4096

  storage:
    raw_dir: ./dev/raw
    wiki_dir: ./dev/wiki
    cache_dir: ./dev/cache
    database_url: sqlite:///./dev/knowledge.db

  processing:
    batch_size: 5
    parallel_workers: 2

  logging:
    level: DEBUG
    format: text
    file: ./logs/dev.log
```

### Production Configuration

```yaml
# config.prod.yaml
knowledge_compiler:
  llm:
    provider: anthropic
    model: claude-sonnet-4-6
    temperature: 0.3
    max_tokens: 8192
    timeout: 120
    max_retries: 5

  storage:
    raw_dir: /data/raw
    wiki_dir: /data/wiki
    cache_dir: /data/cache
    database_url: postgresql://user:pass@prod-db/knowledge
    enable_backups: true

  processing:
    max_file_size: 52428800  # 50MB
    batch_size: 50
    parallel_workers: 8
    incremental_updates: true
    cache_embeddings: true

  quality:
    min_document_quality: 0.7
    min_concept_confidence: 0.8
    min_relation_confidence: 0.7

  logging:
    level: INFO
    format: structured
    file: /var/log/knowledge-compiler/compiler.log
    rotation: daily
```

## Migration from Old Config

The old `src/config.py` `Config` class is different from the new `src/core/config.py` system. Here's how to migrate:

**Old System:**
```python
from src.config import Config

config = Config(
    source_dir="./input",
    output_dir="./output",
    model_name="gpt-3.5-turbo",
    temperature=0.7
)
```

**New System:**
```python
from src.core.config import Config

config = Config({
    "storage": {
        "raw_dir": "./input",
        "wiki_dir": "./output"
    },
    "llm": {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    }
})
```

The new system is more modular, type-safe, and supports environment variables and YAML files.
