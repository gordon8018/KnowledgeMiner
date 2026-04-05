"""Core infrastructure for Knowledge Compiler."""

__version__ = "2.0.0"

# Import base models and configuration (Task 2)
from src.core.base_models import (
    BaseModel,
    SourceType,
    ProcessingStatus,
)

from src.core.config import (
    Config,
    LLMConfig,
    StorageConfig,
    ProcessingConfig,
    QualityConfig,
    LoggingConfig,
    get_config,
)

__all__ = [
    # Base Models (Task 2)
    "BaseModel",
    "SourceType",
    "ProcessingStatus",
    # Configuration (Task 2)
    "Config",
    "LLMConfig",
    "StorageConfig",
    "ProcessingConfig",
    "QualityConfig",
    "LoggingConfig",
    "get_config",
]
