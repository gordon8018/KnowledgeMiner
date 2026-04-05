"""
Knowledge Discovery Module

Provides intelligent discovery capabilities for:
- Relation mining (explicit, implicit, statistical, semantic)
- Pattern detection (temporal, causal, evolutionary, conflict)
- Gap analysis (missing concepts, relations, evidence)
- Insight generation (with significance scoring)
"""

from src.discovery.models.pattern import Pattern, PatternType
from src.discovery.models.gap import KnowledgeGap, GapType
from src.discovery.models.insight import Insight, InsightType
from src.discovery.models.result import DiscoveryResult
from src.discovery.config import DiscoveryConfig
from src.discovery.relation_miner import RelationMiningEngine
from src.discovery.pattern_detector import PatternDetector
from src.discovery.gap_analyzer import GapAnalyzer
from src.discovery.insight_generator import InsightGenerator
from src.discovery.engine import KnowledgeDiscoveryEngine
from src.discovery.interactive import InteractiveDiscovery

__all__ = [
    'Pattern', 'PatternType',
    'KnowledgeGap', 'GapType',
    'Insight', 'InsightType',
    'DiscoveryResult',
    'DiscoveryConfig',
    'RelationMiningEngine',
    'PatternDetector',
    'GapAnalyzer',
    'InsightGenerator',
    'KnowledgeDiscoveryEngine',
    'InteractiveDiscovery',
]
