"""
Pattern detection engine for discovering patterns in knowledge bases.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
import networkx as nx

logger = logging.getLogger(__name__)

from src.discovery.config import DiscoveryConfig
from src.discovery.models.pattern import Pattern, PatternType, Evidence
from src.discovery.patterns.temporal_patterns import (
    extract_time_references,
    detect_periodicity,
    bin_time_references
)
from src.discovery.utils import build_relation_graph
from src.core.document_model import EnhancedDocument
from src.core.concept_model import EnhancedConcept
from src.core.relation_model import Relation, RelationType


class PatternDetector:
    """
    Detects various patterns in knowledge bases including temporal,
    causal, evolutionary, and conflict patterns.
    """

    def __init__(self, config: DiscoveryConfig, llm_provider: Any):
        """
        Initialize the PatternDetector.

        Args:
            config: Discovery configuration
            llm_provider: LLM provider for advanced pattern detection
        """
        self.config = config
        self.llm_provider = llm_provider

    def detect_patterns(
        self,
        documents: List[EnhancedDocument],
        concepts: List[EnhancedConcept],
        relations: List[Relation],
        mode: str = 'full'
    ) -> List[Pattern]:
        """
        Detect all types of patterns in the knowledge base.

        Args:
            documents: List of documents to analyze
            concepts: List of concepts to analyze
            relations: List of relations to analyze
            mode: Processing mode ('full', 'incremental', 'hybrid')

        Returns:
            List of detected patterns
        """
        # Route to appropriate implementation based on mode
        if mode == 'full':
            return self._detect_full(documents, concepts, relations)
        elif mode == 'incremental':
            return self._detect_incremental(documents, concepts, relations)
        elif mode == 'hybrid':
            return self._detect_hybrid(documents, concepts, relations)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def _detect_full(
        self,
        documents: List[EnhancedDocument],
        concepts: List[EnhancedConcept],
        relations: List[Relation]
    ) -> List[Pattern]:
        """
        Detect patterns in full mode (process all documents, concepts, and relations).

        Args:
            documents: List of documents to analyze
            concepts: List of concepts to analyze
            relations: List of relations to analyze

        Returns:
            List of detected patterns
        """
        all_patterns = []

        # Detect temporal patterns
        if self.config.enable_temporal_detection:
            temporal_patterns = self._detect_temporal_patterns(documents)
            all_patterns.extend(temporal_patterns)

        # Detect causal patterns
        if self.config.enable_causal_detection:
            causal_patterns = self._detect_causal_patterns(relations)
            all_patterns.extend(causal_patterns)

        # Detect evolutionary patterns
        if self.config.enable_evolutionary_detection:
            evolutionary_patterns = self._detect_evolutionary_patterns(concepts)
            all_patterns.extend(evolutionary_patterns)

        # Detect conflict patterns
        if self.config.enable_conflict_detection:
            conflict_patterns = self._detect_conflict_patterns(concepts, relations)
            all_patterns.extend(conflict_patterns)

        # Filter patterns by minimum confidence
        filtered_patterns = [
            p for p in all_patterns
            if p.confidence >= self.config.min_pattern_confidence
        ]

        return filtered_patterns

    def _detect_incremental(
        self,
        documents: List[EnhancedDocument],
        concepts: List[EnhancedConcept],
        relations: List[Relation]
    ) -> List[Pattern]:
        """
        Detect patterns in incremental mode (process only provided documents/concepts).

        In incremental mode, we only detect patterns from the provided documents.
        This is useful when processing new/changed documents.

        Args:
            documents: List of documents to analyze (new/changed only)
            concepts: List of concepts to analyze
            relations: List of relations to analyze

        Returns:
            List of detected patterns
        """
        # In incremental mode, we process the provided documents/concepts
        # This is the same as full mode but with the assumption that
        # only new/changed documents/concepts are provided
        all_patterns = []

        # Detect temporal patterns (limited to provided documents)
        if self.config.enable_temporal_detection:
            temporal_patterns = self._detect_temporal_patterns(documents)
            all_patterns.extend(temporal_patterns)

        # Detect causal patterns (limited to provided relations)
        if self.config.enable_causal_detection:
            causal_patterns = self._detect_causal_patterns(relations)
            all_patterns.extend(causal_patterns)

        # Detect evolutionary patterns (limited to provided concepts)
        if self.config.enable_evolutionary_detection:
            evolutionary_patterns = self._detect_evolutionary_patterns(concepts)
            all_patterns.extend(evolutionary_patterns)

        # Detect conflict patterns (limited to provided concepts/relations)
        if self.config.enable_conflict_detection:
            conflict_patterns = self._detect_conflict_patterns(concepts, relations)
            all_patterns.extend(conflict_patterns)

        # Filter patterns by minimum confidence
        filtered_patterns = [
            p for p in all_patterns
            if p.confidence >= self.config.min_pattern_confidence
        ]

        return filtered_patterns

    def _detect_hybrid(
        self,
        documents: List[EnhancedDocument],
        concepts: List[EnhancedConcept],
        relations: List[Relation]
    ) -> List[Pattern]:
        """
        Detect patterns in hybrid mode (smart selection based on document count).

        Hybrid mode uses a threshold heuristic:
        - If documents < 10: process all (like full mode)
        - If documents >= 10: process all (like full mode for now)

        Args:
            documents: List of documents to analyze
            concepts: List of concepts to analyze
            relations: List of relations to analyze

        Returns:
            List of detected patterns
        """
        # Threshold for hybrid mode
        threshold = 10

        if len(documents) < threshold:
            logger.info(f"Hybrid mode: {len(documents)} documents < {threshold} threshold, processing all")
            return self._detect_full(documents, concepts, relations)
        else:
            logger.info(f"Hybrid mode: {len(documents)} documents >= {threshold} threshold, processing all")
            return self._detect_full(documents, concepts, relations)

    def _detect_temporal_patterns(self, documents: List[EnhancedDocument]) -> List[Pattern]:
        """
        Detect temporal patterns in document timestamps.

        Args:
            documents: List of documents to analyze

        Returns:
            List of temporal patterns
        """
        patterns = []

        # Extract all time references from documents
        all_time_refs = []
        doc_time_map = {}  # Map time to document IDs

        for doc in documents:
            # Extract time references from content
            time_refs = extract_time_references(doc.content)

            # Also use document metadata date if available
            if doc.metadata.date:
                time_refs.append(doc.metadata.date)

            for time_ref in time_refs:
                all_time_refs.append(time_ref)
                if time_ref not in doc_time_map:
                    doc_time_map[time_ref] = []
                doc_time_map[time_ref].append(doc.id)

        if not all_time_refs:
            return patterns

        # Detect periodicity
        periods = detect_periodicity(all_time_refs)

        # Create pattern for each detected period
        for period in periods:
            # Calculate confidence based on consistency
            confidence = self._calculate_temporal_confidence(all_time_refs, period)

            # Enforce hard threshold of 0.7 for temporal patterns
            if confidence < 0.7:
                continue

            # Create evidence from time bins
            bins = bin_time_references(all_time_refs, bin_size_days=30)
            evidence = []
            for start, end, count in bins:
                if count > 0:
                    ev = Evidence(
                        source_id=f"time-bin-{start.strftime('%Y%m%d')}",
                        content=f"Time period {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')} with {count} references",
                        confidence=min(count / len(all_time_refs), 1.0),
                        timestamp=start
                    )
                    evidence.append(ev)

            # Calculate significance based on coverage
            significance = min(len(bins) / max(len(all_time_refs), 1), 1.0)

            pattern = Pattern(
                id=f"temporal-{period}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                pattern_type=PatternType.TEMPORAL,
                title=f"{period.capitalize()} Temporal Pattern",
                description=f"Detected {period} periodicity in document timestamps with {len(all_time_refs)} time references",
                confidence=confidence,
                evidence=evidence,
                related_concepts=[],
                related_patterns=[],
                metadata={
                    "period": period,
                    "time_reference_count": len(all_time_refs),
                    "bin_count": len(bins)
                },
                significance_score=significance,
                detected_at=datetime.now()
            )
            patterns.append(pattern)

        return patterns

    def _detect_causal_patterns(self, relations: List[Relation]) -> List[Pattern]:
        """
        Detect causal chain patterns from CAUSES relations.

        Args:
            relations: List of relations to analyze

        Returns:
            List of causal patterns
        """
        patterns = []

        # Build directed graph from causal relations
        graph = nx.DiGraph()

        for rel in relations:
            if rel.relation_type in [RelationType.CAUSES, RelationType.CAUSED_BY]:
                # For CAUSED_BY, reverse the edge direction
                if rel.relation_type == RelationType.CAUSED_BY:
                    source = rel.target_concept
                    target = rel.source_concept
                else:
                    source = rel.source_concept
                    target = rel.target_concept

                graph.add_edge(source, target, weight=rel.strength)

        # Find all simple paths of length 3-5 (2-4 edges)
        all_paths = []
        nodes = list(graph.nodes())

        for source in nodes:
            for target in nodes:
                if source == target:
                    continue

                try:
                    # Find paths of different lengths (cutoff=4 gives max 5 nodes)
                    paths = list(nx.all_simple_paths(graph, source, target, cutoff=4))
                    # Filter paths with length 3-5 nodes (2-4 edges)
                    valid_paths = [p for p in paths if 3 <= len(p) <= 5]
                    all_paths.extend(valid_paths)
                except nx.NetworkXNoPath:
                    continue

        # Prioritize longer paths
        all_paths.sort(key=len, reverse=True)

        # Create patterns for unique paths
        seen_paths = set()
        for path in all_paths:
            path_tuple = tuple(path)
            if path_tuple in seen_paths:
                continue
            seen_paths.add(path_tuple)

            # Compute path strength
            strength = self._compute_path_strength(graph, path)

            if strength < self.config.min_pattern_confidence:
                continue

            # Find supporting relations
            supporting_rels = []
            for i in range(len(path) - 1):
                for rel in relations:
                    if (rel.source_concept == path[i] and
                        rel.target_concept == path[i+1] and
                        rel.relation_type == RelationType.CAUSES):
                        supporting_rels.append(rel)
                        break

            # Create evidence
            evidence = []
            for rel in supporting_rels:
                for ev in rel.evidence:
                    evidence.append(Evidence(
                        source_id=ev.get("source", "unknown"),
                        content=ev.get("quote", ""),
                        confidence=ev.get("confidence", rel.confidence)
                    ))

            # Calculate significance based on path length and strength
            significance = strength * (len(path) / 5.0)

            pattern = Pattern(
                id=f"causal-{'-'.join(path)}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                pattern_type=PatternType.CAUSAL,
                title=f"Causal Chain: {' → '.join(path)}",
                description=f"Causal chain detected: {path[0]} causes {path[-1]} through {len(path)-1} intermediate steps",
                confidence=strength,
                evidence=evidence,
                related_concepts=list(path),
                related_patterns=[],
                metadata={
                    "path_length": len(path),
                    "supporting_relation_count": len(supporting_rels),
                    "path": path
                },
                significance_score=significance,
                detected_at=datetime.now()
            )
            patterns.append(pattern)

        return patterns

    def _detect_evolutionary_patterns(self, concepts: List[EnhancedConcept]) -> List[Pattern]:
        """
        Detect evolutionary patterns from concept version changes.

        Args:
            concepts: List of concepts to analyze

        Returns:
            List of evolutionary patterns
        """
        patterns = []

        # Group concepts by base name (split by '_')
        concept_groups = {}
        for concept in concepts:
            # Extract base name (before version suffix)
            base_name = concept.name.split('_')[0]
            if base_name not in concept_groups:
                concept_groups[base_name] = []
            concept_groups[base_name].append(concept)

        # Detect evolution in groups with 2+ versions
        for base_name, group in concept_groups.items():
            if len(group) < 2:
                continue

            # Sort by ID to get temporal order
            sorted_group = sorted(group, key=lambda c: c.id)

            # Detect definition changes
            definition_changes = []
            for i in range(1, len(sorted_group)):
                prev_def = sorted_group[i-1].definition
                curr_def = sorted_group[i].definition
                if prev_def != curr_def:
                    definition_changes.append({
                        "from": sorted_group[i-1].id,
                        "to": sorted_group[i].id,
                        "previous_definition": prev_def,
                        "new_definition": curr_def
                    })

            if not definition_changes:
                continue

            # Calculate confidence based on number of versions and changes
            confidence = min(len(definition_changes) / len(sorted_group), 1.0)

            # Create evidence
            evidence = []
            for change in definition_changes:
                ev = Evidence(
                    source_id=change["to"],
                    content=f"Definition changed from '{change['previous_definition']}' to '{change['new_definition']}'",
                    confidence=confidence
                )
                evidence.append(ev)

            # Calculate significance based on evolution depth
            significance = min(len(sorted_group) / 5.0, 1.0)

            pattern = Pattern(
                id=f"evolutionary-{base_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                pattern_type=PatternType.EVOLUTIONARY,
                title=f"Evolution of {base_name}",
                description=f"Concept '{base_name}' has evolved through {len(sorted_group)} versions with {len(definition_changes)} definition changes",
                confidence=confidence,
                evidence=evidence,
                related_concepts=[c.id for c in sorted_group],
                related_patterns=[],
                metadata={
                    "base_name": base_name,
                    "version_count": len(sorted_group),
                    "change_count": len(definition_changes),
                    "changes": definition_changes
                },
                significance_score=significance,
                detected_at=datetime.now()
            )
            patterns.append(pattern)

        return patterns

    def _detect_conflict_patterns(
        self,
        concepts: List[EnhancedConcept],
        relations: List[Relation]
    ) -> List[Pattern]:
        """
        Detect conflict patterns from OPPOSES relations.

        Args:
            concepts: List of concepts to analyze
            relations: List of relations to analyze

        Returns:
            List of conflict patterns
        """
        patterns = []

        # Find all OPPOSES relations
        opposes_relations = [
            rel for rel in relations
            if rel.relation_type == RelationType.OPPOSES
        ]

        # Create concept map for easy lookup
        concept_map = {c.id: c for c in concepts}

        for rel in opposes_relations:
            source_concept = concept_map.get(rel.source_concept)
            target_concept = concept_map.get(rel.target_concept)

            # Check if relation has high confidence
            if not source_concept or not target_concept:
                continue

            if rel.confidence < 0.7:
                continue

            # Calculate confidence based on relation strength and concept confidence
            confidence = (
                rel.strength * 0.6 +
                source_concept.confidence * 0.2 +
                target_concept.confidence * 0.2
            )

            # Create evidence
            evidence = []
            for ev in rel.evidence:
                evidence.append(Evidence(
                    source_id=ev.get("source", "unknown"),
                    content=ev.get("quote", ""),
                    confidence=ev.get("confidence", rel.confidence)
                ))

            # Add concept definitions as evidence
            evidence.append(Evidence(
                source_id=source_concept.id,
                content=f"Source concept: {source_concept.definition}",
                confidence=source_concept.confidence
            ))
            evidence.append(Evidence(
                source_id=target_concept.id,
                content=f"Target concept: {target_concept.definition}",
                confidence=target_concept.confidence
            ))

            # Calculate significance based on confidence and strength
            significance = (rel.strength + confidence) / 2.0

            pattern = Pattern(
                id=f"conflict-{rel.source_concept}-vs-{rel.target_concept}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                pattern_type=PatternType.CONFLICT,
                title=f"Conflict: {source_concept.name} vs {target_concept.name}",
                description=f"Detected conflict between '{source_concept.name}' and '{target_concept.name}' with {rel.strength:.2f} opposition strength",
                confidence=confidence,
                evidence=evidence,
                related_concepts=[rel.source_concept, rel.target_concept],
                related_patterns=[],
                metadata={
                    "relation_id": rel.id,
                    "opposition_strength": rel.strength,
                    "source_confidence": source_concept.confidence,
                    "target_confidence": target_concept.confidence
                },
                significance_score=significance,
                detected_at=datetime.now()
            )
            patterns.append(pattern)

        return patterns

    def _compute_path_strength(self, graph: nx.DiGraph, path: List[str]) -> float:
        """
        Compute the strength of a causal path by multiplying edge weights.

        Args:
            graph: NetworkX directed graph
            path: List of node IDs representing the path

        Returns:
            Path strength (0.0 to 1.0)
        """
        if len(path) < 2:
            return 0.0

        strength = 1.0
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i+1]

            # Check if edge exists
            if not graph.has_edge(source, target):
                return 0.0

            # Get edge weight
            edge_data = graph.get_edge_data(source, target)
            weight = edge_data.get('weight', 0.5)

            # Multiply strength
            strength *= weight

        return strength

    def _calculate_temporal_confidence(
        self,
        time_refs: List[datetime],
        period: str
    ) -> float:
        """
        Calculate confidence score for temporal pattern detection.

        Args:
            time_refs: List of time references
            period: Detected period type

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if len(time_refs) < 3:
            return 0.0

        # Base confidence on number of time references
        base_confidence = min(len(time_refs) / 10.0, 1.0)

        # Adjust based on period type (yearly is more confident than weekly)
        period_multiplier = {
            "weekly": 0.7,
            "monthly": 0.8,
            "quarterly": 0.9,
            "yearly": 1.0
        }.get(period, 0.8)

        return base_confidence * period_multiplier
