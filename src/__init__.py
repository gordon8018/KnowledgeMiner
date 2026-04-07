"""KnowledgeMiner 4.0 - Three-layer knowledge management system"""

__version__ = "4.0.0"
__author__ = "KnowledgeMiner Team"
__license__ = "MIT"

from src.orchestrator import KnowledgeMinerOrchestrator, ingest, query, lint

__all__ = ["KnowledgeMinerOrchestrator", "ingest", "query", "lint", "__version__"]
