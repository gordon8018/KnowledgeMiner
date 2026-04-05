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

# Import document model (Task 3)
from src.core.document_model import (
    DocumentMetadata,
    EnhancedDocument,
)

# Import concept model (Task 4)
from src.core.concept_model import (
    ConceptType,
    TemporalInfo,
    EnhancedConcept,
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
    # Document Model (Task 3)
    "DocumentMetadata",
    "EnhancedDocument",
    # Concept Model (Task 4)
    "ConceptType",
    "TemporalInfo",
    "EnhancedConcept",
]
