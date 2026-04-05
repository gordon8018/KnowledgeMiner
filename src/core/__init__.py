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

# Import relation model (Task 5)
from src.core.relation_model import (
    RelationType,
    Relation,
)

# Import state manager (Task 8)
from src.core.state_manager import StateManager

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
    # Relation Model (Task 5)
    "RelationType",
    "Relation",
    # State Manager (Task 8)
    "StateManager",
]
