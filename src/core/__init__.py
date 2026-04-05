"""Core infrastructure for Knowledge Compiler."""

__version__ = "2.0.0"

from .base_models import BaseModel
from .document_model import EnhancedDocument
from .concept_model import EnhancedConcept
from .relation_model import Relation

__all__ = [
    "BaseModel",
    "EnhancedDocument",
    "EnhancedConcept",
    "Relation",
]
