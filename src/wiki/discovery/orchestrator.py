"""
DiscoveryOrchestrator - Orchestrates complete discovery pipeline.

This module coordinates Phase 2 discovery components:
- Relation mining
- Pattern detection
- Gap analysis
- Insight generation

And integrates results with Wiki via WikiIntegrator.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.discovery.engine import KnowledgeDiscoveryEngine
from src.discovery.config import DiscoveryConfig
from src.discovery.models.result import DiscoveryResult
from src.discovery.models.pattern import Pattern
from src.discovery.models.gap import KnowledgeGap
from src.discovery.models.insight import Insight
from src.core.relation_model import Relation
from src.core.concept_model import EnhancedConcept
from src.core.document_model import EnhancedDocument

logger = logging.getLogger(__name__)


class DiscoveryOrchestrator:
    """
    Orchestrates complete knowledge discovery pipeline.

    Coordinates:
    1. Knowledge discovery via KnowledgeDiscoveryEngine
    2. Wiki integration via WikiIntegrator

    Attributes:
        discovery_engine: KnowledgeDiscoveryEngine instance
        integrator: WikiIntegrator instance
        config: DiscoveryConfig instance
    """

    def __init__(
        self,
        discovery_engine: KnowledgeDiscoveryEngine,
        wiki_path: Optional[str] = None,
        config: Optional[DiscoveryConfig] = None
    ):
        """
        Initialize DiscoveryOrchestrator.

        Args:
            discovery_engine: KnowledgeDiscoveryEngine instance
            wiki_path: Optional path to wiki directory
            config: Optional DiscoveryConfig instance
        """
        self.discovery_engine = discovery_engine
        self.config = config or discovery_engine.config

        # Initialize WikiIntegrator
        from src.wiki.discovery.integrator import WikiIntegrator
        self.integrator = WikiIntegrator(wiki_path=wiki_path)

        logger.info("DiscoveryOrchestrator initialized")

    def orchestrate(
        self,
        documents: List[EnhancedDocument],
        concepts: List[EnhancedConcept],
        mode: str = 'full',
        existing_relations: Optional[List[Relation]] = None,
        integrate_to_wiki: bool = True
    ) -> DiscoveryResult:
        """
        Orchestrate complete discovery pipeline.

        Args:
            documents: List of EnhancedDocument objects
            concepts: List of EnhancedConcept objects
            mode: Processing mode ('full', 'incremental', 'hybrid')
            existing_relations: Optional existing relations to include
            integrate_to_wiki: Whether to integrate results to wiki

        Returns:
            DiscoveryResult containing all findings

        Raises:
            ValueError: If mode is not recognized
        """
        logger.info(f"Starting discovery orchestration in {mode} mode")
        start_time = datetime.now()

        try:
            # Execute discovery pipeline with EnhancedDocument objects
            # The discovery engine expects EnhancedDocument objects, not dicts
            discovery_result = self.discovery_engine.discover(
                documents=documents,
                concepts=concepts,
                relations=existing_relations
            )

            # Add mode to result
            discovery_result.statistics['mode'] = mode
            discovery_result.statistics['orchestration_time'] = (
                datetime.now() - start_time
            ).total_seconds()

            logger.info(
                f"Discovery completed: {len(discovery_result.relations)} relations, "
                f"{len(discovery_result.patterns)} patterns, "
                f"{len(discovery_result.gaps)} gaps, "
                f"{len(discovery_result.insights)} insights"
            )

            # Integrate to wiki if requested
            if integrate_to_wiki:
                logger.info("Integrating discovery results to wiki")
                integration_result = self.integrator.integrate(
                    relations=discovery_result.relations,
                    patterns=discovery_result.patterns,
                    gaps=discovery_result.gaps,
                    insights=discovery_result.insights
                )

                if integration_result['success']:
                    logger.info(
                        f"Successfully integrated {integration_result['changes_applied']} changes to wiki"
                    )
                    discovery_result.statistics['wiki_integration'] = integration_result
                else:
                    logger.warning(f"Wiki integration failed: {integration_result.get('error')}")
                    discovery_result.statistics['wiki_integration'] = integration_result

            return discovery_result

        except Exception as e:
            logger.error(f"Error during discovery orchestration: {e}", exc_info=True)
            raise

    def _convert_documents_to_dict(
        self,
        documents: List[EnhancedDocument]
    ) -> List[Dict[str, Any]]:
        """
        Convert EnhancedDocument objects to dict format.

        Args:
            documents: List of EnhancedDocument objects

        Returns:
            List of document dictionaries
        """
        documents_dict = []
        for doc in documents:
            # Handle both enum and string source_type
            source_type = (
                doc.source_type.value
                if hasattr(doc.source_type, 'value')
                else doc.source_type
            )

            doc_dict = {
                'id': doc.id,
                'title': doc.metadata.title or doc.id,
                'content': doc.content,
                'source': doc.metadata.file_path or 'unknown',
                'source_type': source_type,
                'quality_score': doc.quality_score
            }
            documents_dict.append(doc_dict)

        return documents_dict

    def get_statistics(self, result: DiscoveryResult) -> Dict[str, Any]:
        """
        Get summary statistics from discovery result.

        Args:
            result: DiscoveryResult instance

        Returns:
            Dictionary of summary statistics
        """
        return {
            'total_relations': len(result.relations),
            'total_patterns': len(result.patterns),
            'total_gaps': len(result.gaps),
            'total_insights': len(result.insights),
            'avg_insight_significance': (
                sum(i.significance for i in result.insights) / len(result.insights)
                if result.insights else 0.0
            ),
            'high_priority_gaps': len([g for g in result.gaps if g.priority >= 7]),
            'high_confidence_patterns': len([
                p for p in result.patterns if p.confidence >= 0.7
            ]),
            'mode': result.statistics.get('mode', 'unknown'),
            'orchestration_time': result.statistics.get('orchestration_time', 0.0)
        }
