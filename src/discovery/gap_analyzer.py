"""
GapAnalyzer - Identify knowledge gaps in concepts, relations, and evidence.

This module implements three types of gap analysis:
1. Missing concepts - LLM-based inference of concepts that should exist
2. Missing relations - Graph analysis to find isolated/weakly connected concepts
3. Weak evidence - Concepts with low confidence or few evidence items
"""

import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.discovery.config import DiscoveryConfig
from src.discovery.models.gap import KnowledgeGap, GapType
from src.discovery.utils.graph_utils import (
    build_relation_graph,
    find_isolated_nodes,
    detect_communities
)
from src.core.concept_model import EnhancedConcept
from src.core.relation_model import Relation

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """
    Analyze knowledge gaps in the knowledge base.

    Identifies three types of gaps:
    - Missing concepts (via LLM inference)
    - Missing relations (via graph analysis)
    - Weak evidence (via confidence thresholding)

    Attributes:
        config: Discovery configuration
        llm_provider: Optional LLM provider for concept inference
    """

    def __init__(
        self,
        config: DiscoveryConfig,
        llm_provider: Optional[Any] = None
    ):
        """
        Initialize GapAnalyzer.

        Args:
            config: Discovery configuration
            llm_provider: Optional LLM provider for missing concept analysis
        """
        self.config = config
        self.llm_provider = llm_provider

    def analyze_gaps(
        self,
        documents: List[Dict[str, Any]],
        concepts: List[EnhancedConcept],
        relations: List[Relation],
        mode: str = 'full'
    ) -> List[KnowledgeGap]:
        """
        Analyze knowledge gaps across all dimensions.

        Args:
            documents: List of documents (dicts with 'id', 'title', 'content')
            concepts: List of EnhancedConcept objects
            relations: List of Relation objects
            mode: Processing mode ('full', 'incremental', 'hybrid')

        Returns:
            List of KnowledgeGap objects sorted by priority (high to low)
        """
        # Route to appropriate implementation based on mode
        if mode == 'full':
            return self._analyze_full(documents, concepts, relations)
        elif mode == 'incremental':
            return self._analyze_incremental(documents, concepts, relations)
        elif mode == 'hybrid':
            return self._analyze_hybrid(documents, concepts, relations)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def _analyze_full(
        self,
        documents: List[Dict[str, Any]],
        concepts: List[EnhancedConcept],
        relations: List[Relation]
    ) -> List[KnowledgeGap]:
        """
        Analyze knowledge gaps in full mode (process all documents, concepts, and relations).

        Args:
            documents: List of documents (dicts with 'id', 'title', 'content')
            concepts: List of EnhancedConcept objects
            relations: List of Relation objects

        Returns:
            List of KnowledgeGap objects sorted by priority (high to low)
        """
        all_gaps = []

        # 1. Analyze missing concepts (LLM-based)
        if self.config.enable_concept_gap_analysis:
            try:
                concept_gaps = self._analyze_missing_concepts(concepts, documents)
                all_gaps.extend(concept_gaps)
            except Exception as e:
                logger.error(f"Error analyzing missing concepts: {e}")

        # 2. Analyze missing relations (graph-based)
        if self.config.enable_relation_gap_analysis:
            try:
                relation_gaps = self._analyze_missing_relations(concepts, relations)
                all_gaps.extend(relation_gaps)
            except Exception as e:
                logger.error(f"Error analyzing missing relations: {e}")

        # 3. Analyze insufficient evidence
        if self.config.enable_evidence_analysis:
            try:
                evidence_gaps = self._analyze_insufficient_evidence(concepts)
                all_gaps.extend(evidence_gaps)
            except Exception as e:
                logger.error(f"Error analyzing insufficient evidence: {e}")

        # Sort by priority (high to low)
        all_gaps.sort(key=lambda g: g.priority, reverse=True)

        return all_gaps

    def _analyze_incremental(
        self,
        documents: List[Dict[str, Any]],
        concepts: List[EnhancedConcept],
        relations: List[Relation]
    ) -> List[KnowledgeGap]:
        """
        Analyze knowledge gaps in incremental mode (process only provided documents/concepts).

        In incremental mode, we only analyze gaps from the provided documents/concepts.
        This is useful when processing new/changed documents.

        Args:
            documents: List of documents (dicts with 'id', 'title', 'content')
            concepts: List of EnhancedConcept objects (new/changed only)
            relations: List of Relation objects

        Returns:
            List of KnowledgeGap objects sorted by priority (high to low)
        """
        # In incremental mode, we process the provided documents/concepts
        # This is the same as full mode but with the assumption that
        # only new/changed documents/concepts are provided
        all_gaps = []

        # 1. Analyze missing concepts (limited to provided concepts)
        if self.config.enable_concept_gap_analysis:
            try:
                concept_gaps = self._analyze_missing_concepts(concepts, documents)
                all_gaps.extend(concept_gaps)
            except Exception as e:
                logger.error(f"Error analyzing missing concepts: {e}")

        # 2. Analyze missing relations (limited to provided concepts)
        if self.config.enable_relation_gap_analysis:
            try:
                relation_gaps = self._analyze_missing_relations(concepts, relations)
                all_gaps.extend(relation_gaps)
            except Exception as e:
                logger.error(f"Error analyzing missing relations: {e}")

        # 3. Analyze insufficient evidence (limited to provided concepts)
        if self.config.enable_evidence_analysis:
            try:
                evidence_gaps = self._analyze_insufficient_evidence(concepts)
                all_gaps.extend(evidence_gaps)
            except Exception as e:
                logger.error(f"Error analyzing insufficient evidence: {e}")

        # Sort by priority (high to low)
        all_gaps.sort(key=lambda g: g.priority, reverse=True)

        return all_gaps

    def _analyze_hybrid(
        self,
        documents: List[Dict[str, Any]],
        concepts: List[EnhancedConcept],
        relations: List[Relation]
    ) -> List[KnowledgeGap]:
        """
        Analyze knowledge gaps in hybrid mode (smart selection based on concept count).

        Hybrid mode uses a threshold heuristic:
        - If concepts < 10: process all (like full mode)
        - If concepts >= 10: process all (like full mode for now)

        Args:
            documents: List of documents (dicts with 'id', 'title', 'content')
            concepts: List of EnhancedConcept objects
            relations: List of Relation objects

        Returns:
            List of KnowledgeGap objects sorted by priority (high to low)
        """
        # Threshold for hybrid mode
        threshold = 10

        if len(concepts) < threshold:
            logger.info(f"Hybrid mode: {len(concepts)} concepts < {threshold} threshold, processing all")
            return self._analyze_full(documents, concepts, relations)
        else:
            logger.info(f"Hybrid mode: {len(concepts)} concepts >= {threshold} threshold, processing all")
            return self._analyze_full(documents, concepts, relations)

    def _analyze_missing_concepts(
        self,
        concepts: List[EnhancedConcept],
        documents: List[Dict[str, Any]]
    ) -> List[KnowledgeGap]:
        """
        Identify missing concepts using LLM inference.

        Samples first 5 concepts and asks LLM what related concepts are missing.

        Args:
            concepts: List of existing concepts
            documents: List of documents for context

        Returns:
            List of KnowledgeGap objects for missing concepts
        """
        if not self.llm_provider:
            logger.warning("No LLM provider available for missing concept analysis")
            return []

        if not concepts:
            logger.warning("No concepts provided for missing concept analysis")
            return []

        try:
            # Sample first 5 concepts to avoid timeout
            sample_concepts = concepts[:5]
            sample_text = "\n".join([
                f"- {c.name} ({c.type}): {c.definition}"
                for c in sample_concepts
            ])

            # Build prompt
            prompt = f"""
You are analyzing a knowledge base for missing concepts.

Here are some existing concepts:
{sample_text}

Please analyze this knowledge base and identify 3-5 important concepts that are missing but should be included based on the relationships between existing concepts.

For each missing concept, provide:
1. Name of the concept
2. Type (term, indicator, strategy, theory, or person)
3. Brief description
4. Which existing concepts it relates to

Format your response as:
1. **Concept Name** - Description
2. ...

Then provide a JSON block:
```json
{{
  "missing_concepts": [
    {{
      "name": "Concept Name",
      "type": "term",
      "description": "Description of the concept",
      "related_to": ["Existing Concept 1", "Existing Concept 2"]
    }}
  ]
}}
```
"""

            # Call LLM
            response = self.llm_provider.generate_response(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7
            )

            # Parse JSON response
            gaps = self._parse_missing_concepts_response(response, concepts)

            logger.info(f"Identified {len(gaps)} missing concepts")
            return gaps

        except Exception as e:
            logger.error(f"Error in missing concept analysis: {e}")
            return []

    def _parse_missing_concepts_response(
        self,
        response: str,
        existing_concepts: List[EnhancedConcept]
    ) -> List[KnowledgeGap]:
        """
        Parse LLM response to extract missing concepts.

        Args:
            response: LLM response text
            existing_concepts: List of existing concepts for validation

        Returns:
            List of KnowledgeGap objects
        """
        gaps = []

        try:
            # Extract JSON from response
            json_start = response.find("```json")
            json_end = response.find("```", json_start + 7)

            if json_start == -1 or json_end == -1:
                logger.warning("No JSON block found in LLM response")
                return []

            json_str = response[json_start + 7:json_end].strip()
            data = json.loads(json_str)

            missing_concepts = data.get("missing_concepts", [])

            for idx, concept_data in enumerate(missing_concepts):
                concept_name = concept_data.get("name", f"Missing Concept {idx + 1}")
                description = concept_data.get("description", "Missing concept identified by LLM")
                related_to = concept_data.get("related_to", [])

                # Validate that related concepts exist
                valid_relations = [
                    r for r in related_to
                    if any(c.name == r for c in existing_concepts)
                ]

                gap = KnowledgeGap(
                    id=f"missing-concept-{uuid.uuid4().hex[:8]}",
                    gap_type=GapType.MISSING_CONCEPT,
                    description=f"Missing concept: {concept_name}",
                    severity=0.7,  # Fixed severity for missing concepts
                    affected_concepts=valid_relations,
                    affected_relations=[],
                    suggested_actions=[
                        f"Add concept '{concept_name}' to knowledge base",
                        f"Gather evidence and documentation for '{concept_name}'",
                        f"Establish relations to: {', '.join(valid_relations)}"
                    ],
                    priority=2,  # High priority
                    estimated_effort="medium",
                    metadata={
                        "concept_name": concept_name,
                        "concept_type": concept_data.get("type", "term"),
                        "proposed_description": description,
                        "related_to": related_to
                    },
                    detected_at=datetime.now()
                )

                gaps.append(gap)

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {e}")
        except Exception as e:
            logger.error(f"Error processing missing concepts: {e}")

        return gaps

    def _analyze_missing_relations(
        self,
        concepts: List[EnhancedConcept],
        relations: List[Relation]
    ) -> List[KnowledgeGap]:
        """
        Identify missing relations using graph analysis.

        Finds:
        - Isolated nodes (concepts with no relations)
        - Weakly connected communities (avg degree < 2)

        Args:
            concepts: List of EnhancedConcept objects
            relations: List of Relation objects

        Returns:
            List of KnowledgeGap objects for missing relations
        """
        gaps = []

        if not concepts:
            logger.warning("No concepts provided for missing relation analysis")
            return []

        if not relations:
            # All concepts are isolated if no relations exist
            logger.warning("No relations provided - all concepts are isolated")
            for concept in concepts:
                gap = KnowledgeGap(
                    id=f"isolated-concept-{uuid.uuid4().hex[:8]}",
                    gap_type=GapType.MISSING_RELATION,
                    description=f"Concept '{concept.name}' has no relations to other concepts",
                    severity=0.6,
                    affected_concepts=[concept.name],
                    affected_relations=[],
                    suggested_actions=[
                        f"Identify related concepts for '{concept.name}'",
                        f"Add relations to connect '{concept.name}' to the knowledge graph",
                        "Review if this concept should be merged with another"
                    ],
                    priority=4,  # Medium-high priority
                    estimated_effort="low",
                    metadata={
                        "isolation_type": "no_edges",
                        "graph_info": {
                            "node": concept.name,
                            "degree": 0
                        }
                    },
                    detected_at=datetime.now()
                )
                gaps.append(gap)
            return gaps

        try:
            # Build relation graph
            graph = build_relation_graph(relations)

            # Find concepts that exist but have no relations (not in graph)
            concept_names_in_graph = set(graph.nodes())
            concepts_with_no_relations = [
                c for c in concepts
                if c.name not in concept_names_in_graph
            ]

            for concept in concepts_with_no_relations:
                gap = KnowledgeGap(
                    id=f"isolated-concept-{uuid.uuid4().hex[:8]}",
                    gap_type=GapType.MISSING_RELATION,
                    description=f"Concept '{concept.name}' has no relations to other concepts",
                    severity=0.6,
                    affected_concepts=[concept.name],
                    affected_relations=[],
                    suggested_actions=[
                        f"Identify related concepts for '{concept.name}'",
                        f"Add relations to connect '{concept.name}' to the knowledge graph",
                        "Review if this concept should be merged with another"
                    ],
                    priority=4,  # Medium-high priority
                    estimated_effort="low",
                    metadata={
                        "isolation_type": "no_edges",
                        "graph_info": {
                            "node": concept.name,
                            "degree": 0
                        }
                    },
                    detected_at=datetime.now()
                )
                gaps.append(gap)

            # Find isolated nodes (in graph but with no edges)
            isolated_nodes = find_isolated_nodes(graph)

            for node in isolated_nodes:
                gap = KnowledgeGap(
                    id=f"isolated-node-{uuid.uuid4().hex[:8]}",
                    gap_type=GapType.MISSING_RELATION,
                    description=f"Concept '{node}' has no relations to other concepts",
                    severity=0.6,
                    affected_concepts=[node],
                    affected_relations=[],
                    suggested_actions=[
                        f"Identify related concepts for '{node}'",
                        f"Add relations to connect '{node}' to the knowledge graph",
                        "Review if this concept should be merged with another"
                    ],
                    priority=4,  # Medium-high priority
                    estimated_effort="low",
                    metadata={
                        "isolation_type": "no_edges",
                        "graph_info": {
                            "node": node,
                            "degree": 0
                        }
                    },
                    detected_at=datetime.now()
                )
                gaps.append(gap)

            # Detect communities with weak connectivity
            communities = detect_communities(graph, min_size=2)

            for community in communities:
                # Calculate average degree
                total_degree = 0
                for node in community:
                    total_degree += graph.degree(node)

                avg_degree = total_degree / len(community) if community else 0

                # Flag weak communities (avg degree < 2)
                if avg_degree < 2.0:
                    gap = KnowledgeGap(
                        id=f"weak-community-{uuid.uuid4().hex[:8]}",
                        gap_type=GapType.MISSING_RELATION,
                        description=f"Community of {len(community)} concepts has weak connectivity (avg degree: {avg_degree:.1f})",
                        severity=0.5,
                        affected_concepts=list(community),
                        affected_relations=[],
                        suggested_actions=[
                            "Add more relations within this community",
                            "Identify cross-community connections",
                            "Review if concepts should be split or merged"
                        ],
                        priority=3,  # Medium priority
                        estimated_effort="medium",
                        metadata={
                            "weakness_type": "low_connectivity",
                            "community_size": len(community),
                            "avg_degree": avg_degree,
                            "concepts": list(community)
                        },
                        detected_at=datetime.now()
                    )
                    gaps.append(gap)

            logger.info(f"Identified {len(gaps)} missing relation gaps")
            return gaps

        except Exception as e:
            logger.error(f"Error in missing relation analysis: {e}")
            return []

    def _analyze_insufficient_evidence(
        self,
        concepts: List[EnhancedConcept]
    ) -> List[KnowledgeGap]:
        """
        Identify concepts with insufficient evidence.

        Flags concepts that:
        - Have confidence below min_evidence_confidence threshold
        - Have fewer than 3 evidence items (if evidence tracking is available)

        Args:
            concepts: List of EnhancedConcept objects

        Returns:
            List of KnowledgeGap objects for weak evidence
        """
        gaps = []

        if not concepts:
            return []

        try:
            for concept in concepts:
                # Check confidence threshold
                if concept.confidence < self.config.min_evidence_confidence:
                    severity = 1.0 - concept.confidence

                    gap = KnowledgeGap(
                        id=f"weak-evidence-{uuid.uuid4().hex[:8]}",
                        gap_type=GapType.WEAK_EVIDENCE,
                        description=f"Concept '{concept.name}' has low confidence ({concept.confidence:.2f})",
                        severity=severity,
                        affected_concepts=[concept.name],
                        affected_relations=[],
                        suggested_actions=[
                            f"Find more evidence for '{concept.name}'",
                            "Improve documentation and definitions",
                            "Review if this concept should be merged or refined"
                        ],
                        priority=7,  # Lower priority
                        estimated_effort="low",
                        metadata={
                            "weakness_type": "low_confidence",
                            "confidence": concept.confidence,
                            "evidence_count": len(concept.evidence)
                        },
                        detected_at=datetime.now()
                    )
                    gaps.append(gap)

                # Check evidence count (if available)
                elif concept.evidence and len(concept.evidence) < 3:
                    gap = KnowledgeGap(
                        id=f"insufficient-evidence-{uuid.uuid4().hex[:8]}",
                        gap_type=GapType.WEAK_EVIDENCE,
                        description=f"Concept '{concept.name}' has only {len(concept.evidence)} evidence items",
                        severity=0.4,
                        affected_concepts=[concept.name],
                        affected_relations=[],
                        suggested_actions=[
                            f"Gather more supporting evidence for '{concept.name}'",
                            "Find additional source documents",
                            "Review quality of existing evidence"
                        ],
                        priority=5,  # Medium-low priority
                        estimated_effort="low",
                        metadata={
                            "weakness_type": "insufficient_count",
                            "confidence": concept.confidence,
                            "evidence_count": len(concept.evidence)
                        },
                        detected_at=datetime.now()
                    )
                    gaps.append(gap)

            logger.info(f"Identified {len(gaps)} insufficient evidence gaps")
            return gaps

        except Exception as e:
            logger.error(f"Error in insufficient evidence analysis: {e}")
            return []
