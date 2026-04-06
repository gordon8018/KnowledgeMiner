"""
Knowledge discovery engine - main entry point.
"""

from typing import List, Optional
from datetime import datetime
from src.discovery.config import DiscoveryConfig
from src.discovery.models.result import DiscoveryResult
from src.discovery.relation_miner import RelationMiningEngine
from src.discovery.pattern_detector import PatternDetector
from src.discovery.gap_analyzer import GapAnalyzer
from src.discovery.insight_generator import InsightGenerator
from src.core.document_model import EnhancedDocument
from src.core.concept_model import EnhancedConcept
from src.core.relation_model import Relation
from src.integrations.llm_providers import LLMProvider, get_llm_provider
from src.ml.embeddings import EmbeddingGenerator


class KnowledgeDiscoveryEngine:
    """
    Main knowledge discovery engine.

    Orchestrates the complete discovery pipeline:
    1. Relation mining
    2. Pattern detection
    3. Gap analysis
    4. Insight generation
    """

    def __init__(self,
                 config: DiscoveryConfig,
                 llm_provider: LLMProvider = None,
                 embedding_generator: EmbeddingGenerator = None):
        """
        Initialize discovery engine.

        Args:
            config: Discovery configuration
            llm_provider: LLM provider (created if None)
            embedding_generator: Embedding generator (created if None)
        """
        self.config = config
        self.llm = llm_provider or get_llm_provider()
        self.embedder = embedding_generator or EmbeddingGenerator()

        # Initialize components
        self.relation_miner = RelationMiningEngine(
            config, self.llm, self.embedder
        )
        self.pattern_detector = PatternDetector(config, self.llm)
        self.gap_analyzer = GapAnalyzer(config, self.llm)
        self.insight_generator = InsightGenerator(config, self.llm)

    def discover(self,
                documents: List[EnhancedDocument],
                concepts: List[EnhancedConcept],
                relations: Optional[List[Relation]] = None) -> DiscoveryResult:
        """
        Execute complete knowledge discovery pipeline.

        Args:
            documents: List of documents
            concepts: List of concepts
            relations: Optional existing relations

        Returns:
            DiscoveryResult containing all findings
        """
        # Step 1: Mine relations
        mined_relations = self.relation_miner.mine_relations(documents, concepts)

        # Combine with existing relations if provided
        if relations:
            all_relations = relations + mined_relations
        else:
            all_relations = mined_relations

        # Step 2: Detect patterns
        patterns = self.pattern_detector.detect_patterns(
            documents, concepts, all_relations
        )

        # Step 3: Analyze gaps
        gaps = self.gap_analyzer.analyze_gaps(
            documents, concepts, all_relations
        )

        # Step 4: Generate insights
        insights = self.insight_generator.generate_insights(
            all_relations, patterns, gaps
        )

        # Compute statistics
        statistics = self._compute_statistics(
            all_relations, patterns, gaps, insights
        )

        return DiscoveryResult(
            relations=all_relations,
            patterns=patterns,
            gaps=gaps,
            insights=insights,
            statistics=statistics,
            generated_at=datetime.now()
        )

    def _compute_statistics(self,
                           relations: List,
                           patterns: List,
                           gaps: List,
                           insights: List) -> dict:
        """Compute discovery statistics."""
        return {
            'total_relations': len(relations),
            'total_patterns': len(patterns),
            'total_gaps': len(gaps),
            'total_insights': len(insights),
            'avg_insight_significance': sum(
                i.significance for i in insights
            ) / len(insights) if insights else 0.0,
            'high_priority_gaps': len([g for g in gaps if g.priority >= 7]),
            'high_confidence_patterns': len([
                p for p in patterns if p.confidence >= 0.7
            ])
        }
