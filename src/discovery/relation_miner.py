"""
Relation Mining Engine - discovers explicit and implicit relations between concepts.

Implements 4 relation mining strategies:
1. Explicit relations - Text pattern matching
2. Implicit relations - LLM reasoning
3. Statistical relations - Co-occurrence and PMI
4. Semantic relations - Embedding similarity
"""

import json
import logging
import re
import uuid
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional, Tuple
from itertools import combinations

import numpy as np

from src.discovery.config import DiscoveryConfig
from src.discovery.patterns.relation_patterns import RelationPatternLoader
from src.core.document_model import EnhancedDocument
from src.core.concept_model import EnhancedConcept
from src.core.relation_model import Relation, RelationType


logger = logging.getLogger(__name__)


class RelationMiningEngine:
    """
    Discovers relations between concepts using multiple strategies.

    This engine implements four complementary relation mining approaches:
    - Explicit: Pattern-based extraction from text
    - Implicit: LLM-based reasoning about concept relationships
    - Statistical: Co-occurrence analysis with PMI scoring
    - Semantic: Embedding-based similarity detection

    Attributes:
        config: Discovery configuration
        llm: LLM provider for implicit relation discovery
        embedder: Embedding generator for semantic similarity
        pattern_loader: Relation pattern loader for explicit extraction
    """

    def __init__(
        self,
        config: DiscoveryConfig,
        llm_provider: Any,
        embedding_generator: Any
    ):
        """
        Initialize the relation mining engine.

        Args:
            config: Discovery configuration
            llm_provider: LLM provider instance (must have generate() method)
            embedding_generator: Embedding generator (must have generate_embeddings() method)
        """
        self.config = config
        self.llm = llm_provider
        self.embedder = embedding_generator
        self.pattern_loader = RelationPatternLoader()

        logger.info(
            f"Initialized RelationMiningEngine with "
            f"explicit={config.enable_explicit_mining}, "
            f"implicit={config.enable_implicit_mining}, "
            f"statistical={config.enable_statistical_mining}, "
            f"semantic={config.enable_semantic_mining}"
        )

    def mine_relations(
        self,
        documents: List[EnhancedDocument],
        concepts: List[EnhancedConcept]
    ) -> List[Relation]:
        """
        Mine relations between concepts using all enabled strategies.

        This is the main entry point that orchestrates all relation mining strategies,
        merges duplicate relations, and applies filtering based on confidence thresholds.

        Args:
            documents: List of enhanced documents
            concepts: List of enhanced concepts

        Returns:
            List of unique, scored relations meeting minimum confidence threshold
        """
        logger.info(f"Starting relation mining for {len(concepts)} concepts across {len(documents)} documents")

        all_relations = []

        # 1. Explicit relation mining
        if self.config.enable_explicit_mining:
            try:
                explicit_relations = self._extract_explicit_relations(documents)
                all_relations.extend(explicit_relations)
                logger.info(f"Extracted {len(explicit_relations)} explicit relations")
            except Exception as e:
                logger.error(f"Error in explicit relation mining: {e}")

        # 2. Implicit relation mining
        if self.config.enable_implicit_mining:
            try:
                implicit_relations = self._discover_implicit_relations(concepts, documents)
                all_relations.extend(implicit_relations)
                logger.info(f"Discovered {len(implicit_relations)} implicit relations")
            except Exception as e:
                logger.error(f"Error in implicit relation mining: {e}")

        # 3. Statistical relation mining
        if self.config.enable_statistical_mining:
            try:
                statistical_relations = self._compute_statistical_relations(documents, concepts)
                all_relations.extend(statistical_relations)
                logger.info(f"Computed {len(statistical_relations)} statistical relations")
            except Exception as e:
                logger.error(f"Error in statistical relation mining: {e}")

        # 4. Semantic relation mining
        if self.config.enable_semantic_mining:
            try:
                semantic_relations = self._compute_semantic_relations(concepts)
                all_relations.extend(semantic_relations)
                logger.info(f"Computed {len(semantic_relations)} semantic relations")
            except Exception as e:
                logger.error(f"Error in semantic relation mining: {e}")

        # Merge duplicate relations and compute final scores
        merged_relations = self._merge_and_score_relations(all_relations)
        logger.info(f"Merged to {len(merged_relations)} unique relations")

        # Filter by minimum confidence
        filtered_relations = [
            r for r in merged_relations
            if r.confidence >= self.config.min_relation_confidence
        ]
        logger.info(f"Filtered to {len(filtered_relations)} relations with confidence >= {self.config.min_relation_confidence}")

        # Limit relations per concept
        final_relations = self._limit_relations_per_concept(filtered_relations)
        logger.info(f"Limited to {len(final_relations)} relations (max {self.config.max_relations_per_concept} per concept)")

        return final_relations

    def _extract_explicit_relations(self, documents: List[EnhancedDocument]) -> List[Relation]:
        """
        Extract explicit relations using pattern matching.

        Scans document content for linguistic patterns that indicate relationships
        between concepts (e.g., "A causes B", "A depends on B").

        Args:
            documents: List of enhanced documents

        Returns:
            List of relations extracted from explicit patterns
        """
        relations = []

        for doc in documents:
            # Extract relations from document content
            extracted = self.pattern_loader.extract_relations(doc.content)

            for source_text, target_text, rel_type in extracted:
                # Create relation with evidence
                relation = Relation(
                    id=f"rel-explicit-{uuid.uuid4().hex[:8]}",
                    source_concept=source_text,  # Will be mapped to concept IDs later
                    target_concept=target_text,
                    relation_type=rel_type,
                    confidence=0.7,  # Base confidence for explicit patterns
                    strength=0.6,
                    evidence=[{
                        "source": doc.id,
                        "quote": f"{source_text} -> {target_text}",
                        "confidence": 0.7,
                        "extraction_method": "explicit",
                        "pattern_matched": True
                    }]
                )
                relations.append(relation)

        return relations

    def _discover_implicit_relations(
        self,
        concepts: List[EnhancedConcept],
        documents: List[EnhancedDocument]
    ) -> List[Relation]:
        """
        Discover implicit relations using LLM reasoning.

        Uses LLM to infer relationships that aren't explicitly stated in text,
        based on concept definitions and context.

        Args:
            concepts: List of enhanced concepts
            documents: List of enhanced documents (for context)

        Returns:
            List of implicitly discovered relations
        """
        relations = []

        if not concepts:
            return relations

        # Process concepts in batches to avoid timeouts
        batch_size = self.config.batch_size
        for i in range(0, len(concepts), batch_size):
            batch = concepts[i:i + batch_size]

            try:
                # Format concepts for LLM
                concepts_text = self._format_concepts_for_llm(batch)

                # Create LLM prompt
                prompt = f"""Analyze the following concepts and identify implicit relationships between them.

{concepts_text}

Identify relationships that are not explicitly stated but can be inferred from the definitions.
For each relationship, provide:
- source: The source concept name
- target: The target concept name
- relation_type: Type of relationship (causes, caused_by, contains, contained_in, similar_to, opposes, supports, precedes, follows, depends_on, enables, related_to)
- confidence: Confidence score (0.0 to 1.0)
- evidence: Brief explanation of the relationship

Return ONLY a JSON array of objects, no other text."""

                # Call LLM
                response = self.llm.generate(
                    prompt,
                    max_tokens=2000,
                    temperature=0.3
                )

                # Parse LLM response
                batch_relations = self._parse_llm_relations(response, batch)
                relations.extend(batch_relations)

            except Exception as e:
                logger.error(f"Error in LLM call for batch {i}: {e}")
                continue

        return relations

    def _compute_statistical_relations(
        self,
        documents: List[EnhancedDocument],
        concepts: List[EnhancedConcept]
    ) -> List[Relation]:
        """
        Compute statistical relations based on co-occurrence and PMI.

        Analyzes how often concepts appear together in documents compared to
        what would be expected by chance, using Pointwise Mutual Information.

        Args:
            documents: List of enhanced documents
            concepts: List of enhanced concepts

        Returns:
            List of statistically significant relations
        """
        relations = []

        if not concepts or not documents:
            return relations

        # Build concept to documents mapping
        concept_docs = defaultdict(set)
        for concept in concepts:
            for doc_id in concept.source_documents:
                concept_docs[concept.name].add(doc_id)

        # Calculate co-occurrence statistics
        total_docs = len(documents)
        concept_names = list(concept_docs.keys())

        for name1, name2 in combinations(concept_names, 2):
            docs1 = concept_docs[name1]
            docs2 = concept_docs[name2]

            # Co-occurrence count
            co_occurrence = len(docs1 & docs2)

            if co_occurrence == 0:
                continue

            # Individual probabilities
            p1 = len(docs1) / total_docs
            p2 = len(docs2) / total_docs

            # Joint probability
            p_joint = co_occurrence / total_docs

            # Pointwise Mutual Information
            # PMI = log(P(a,b) / (P(a) * P(b)))
            if p1 > 0 and p2 > 0:
                pmi = np.log(p_joint / (p1 * p2))

                # Convert PMI to confidence score
                # PMI can be negative (less likely than chance), zero (independent), or positive (more likely)
                # We normalize to [0, 1] range
                confidence = max(0.0, min(1.0, (pmi + 5) / 10))

                if confidence >= self.config.min_relation_confidence:
                    # Create relation
                    relation = Relation(
                        id=f"rel-stat-{uuid.uuid4().hex[:8]}",
                        source_concept=name1,
                        target_concept=name2,
                        relation_type=RelationType.RELATED_TO,
                        confidence=confidence,
                        strength=confidence * 0.8,
                        evidence=[{
                            "source": "statistical",
                            "quote": f"Co-occurs in {co_occurrence} documents",
                            "confidence": confidence,
                            "extraction_method": "statistical",
                            "pmi": float(pmi),
                            "co_occurrence_count": co_occurrence
                        }]
                    )
                    relations.append(relation)

        return relations

    def _compute_semantic_relations(self, concepts: List[EnhancedConcept]) -> List[Relation]:
        """
        Compute semantic relations based on embedding similarity.

        Uses cosine similarity between concept embeddings to identify
        semantically related concepts.

        Args:
            concepts: List of enhanced concepts

        Returns:
            List of semantically similar relations
        """
        relations = []

        if not concepts:
            return relations

        # Generate embeddings for concepts
        concept_texts = [c.name + ": " + c.definition for c in concepts]

        try:
            embeddings = self.embedder.generate_embeddings(concept_texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return relations

        # Compute pairwise similarities
        for i, j in combinations(range(len(concepts)), 2):
            emb1 = embeddings[i]
            emb2 = embeddings[j]

            # Compute cosine similarity
            similarity = self._cosine_similarity(emb1, emb2)

            # Convert similarity to confidence
            confidence = similarity

            if confidence >= self.config.min_relation_confidence:
                relation = Relation(
                    id=f"rel-sem-{uuid.uuid4().hex[:8]}",
                    source_concept=concepts[i].name,
                    target_concept=concepts[j].name,
                    relation_type=RelationType.SIMILAR_TO,
                    confidence=confidence,
                    strength=confidence,
                    evidence=[{
                        "source": "semantic",
                        "quote": f"Cosine similarity: {similarity:.3f}",
                        "confidence": confidence,
                        "extraction_method": "semantic",
                        "cosine_similarity": float(similarity)
                    }]
                )
                relations.append(relation)

        return relations

    def _merge_and_score_relations(self, relations: List[Relation]) -> List[Relation]:
        """
        Merge duplicate relations and compute final scores.

        When the same relation is found by multiple strategies, merge them by:
        - Combining evidence from all sources
        - Computing weighted average of confidence scores
        - Computing strength from confidence, evidence count, and source diversity

        Args:
            relations: List of relations (may contain duplicates)

        Returns:
            List of merged, scored relations
        """
        # Group by (source, target, relation_type)
        relation_groups = defaultdict(list)

        for relation in relations:
            key = (relation.source_concept, relation.target_concept, relation.relation_type)
            relation_groups[key].append(relation)

        merged_relations = []

        for key, group in relation_groups.items():
            merged = self._merge_relation_group(group)
            merged_relations.append(merged)

        return merged_relations

    def _merge_relation_group(self, group: List[Relation]) -> Relation:
        """
        Merge a group of identical relations into one.

        Args:
            group: List of relations with same (source, target, type)

        Returns:
            Merged relation with combined evidence and computed score
        """
        if len(group) == 1:
            return group[0]

        # Combine evidence
        all_evidence = []
        source_methods = set()

        for relation in group:
            all_evidence.extend(relation.evidence)
            # Check extraction method from evidence items
            for evidence_item in relation.evidence:
                if "extraction_method" in evidence_item:
                    source_methods.add(evidence_item["extraction_method"])

        # Compute weighted confidence average
        # Explicit patterns get weight 1.0, LLM gets 0.9, statistical gets 0.7, semantic gets 0.6
        method_weights = {
            "explicit": 1.0,
            "implicit": 0.9,
            "statistical": 0.7,
            "semantic": 0.6
        }

        weighted_sum = 0.0
        weight_total = 0.0

        for relation in group:
            # Get extraction method from evidence
            method = "explicit"  # default
            for evidence_item in relation.evidence:
                if "extraction_method" in evidence_item:
                    method = evidence_item["extraction_method"]
                    break

            weight = method_weights.get(method, 0.5)
            weighted_sum += relation.confidence * weight
            weight_total += weight

        avg_confidence = weighted_sum / weight_total if weight_total > 0 else 0.5

        # Compute strength from confidence, evidence count, and source diversity
        evidence_score = min(1.0, len(all_evidence) / 5)  # Cap at 5 evidence items
        diversity_score = min(1.0, len(source_methods) / 4)  # Max 4 methods

        strength = (
            avg_confidence * 0.4 +
            evidence_score * 0.3 +
            diversity_score * 0.3
        )

        # Create merged relation
        merged = Relation(
            id=f"rel-merged-{uuid.uuid4().hex[:8]}",
            source_concept=group[0].source_concept,
            target_concept=group[0].target_concept,
            relation_type=group[0].relation_type,
            confidence=avg_confidence,
            strength=strength,
            evidence=[{
                "source": "merged",
                "quote": f"Merged from {len(group)} relations",
                "confidence": avg_confidence,
                "extraction_method": "merged",
                "source_methods": list(source_methods),
                "num_merged": len(group)
            }]
        )

        return merged

    def _format_concepts_for_llm(self, concepts: List[EnhancedConcept]) -> str:
        """
        Format concepts for LLM input.

        Args:
            concepts: List of concepts

        Returns:
            Formatted string with concept names and definitions
        """
        lines = []
        for concept in concepts:
            lines.append(f"- {concept.name}: {concept.definition}")
        return "\n".join(lines)

    def _parse_llm_relations(
        self,
        llm_response: str,
        concepts: List[EnhancedConcept]
    ) -> List[Relation]:
        """
        Parse LLM response into relations.

        Args:
            llm_response: JSON response from LLM
            concepts: List of concepts for validation

        Returns:
            List of parsed relations
        """
        relations = []

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_text = llm_response.strip()

            # Parse JSON
            data = json.loads(json_text)

            if not isinstance(data, list):
                logger.warning(f"LLM response is not a list: {type(data)}")
                return relations

            # Create concept name to ID mapping
            concept_name_to_id = {c.name: c.id for c in concepts}

            for item in data:
                try:
                    # Map relation type string to enum
                    rel_type_str = item.get("relation_type", "related_to")
                    try:
                        rel_type = RelationType(rel_type_str)
                    except ValueError:
                        rel_type = RelationType.RELATED_TO

                    # Map concept names to IDs
                    source_name = item.get("source", "")
                    target_name = item.get("target", "")

                    # Use concept ID if available, otherwise use name
                    source_concept = concept_name_to_id.get(source_name, source_name)
                    target_concept = concept_name_to_id.get(target_name, target_name)

                    relation = Relation(
                        id=f"rel-implicit-{uuid.uuid4().hex[:8]}",
                        source_concept=source_concept,
                        target_concept=target_concept,
                        relation_type=rel_type,
                        confidence=float(item.get("confidence", 0.5)),
                        strength=float(item.get("confidence", 0.5)),
                        evidence=[{
                            "source": "llm",
                            "quote": item.get("evidence", ""),
                            "confidence": float(item.get("confidence", 0.5)),
                            "extraction_method": "implicit"
                        }]
                    )
                    relations.append(relation)

                except Exception as e:
                    logger.warning(f"Error parsing relation item: {e}")
                    continue

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM JSON response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")

        return relations

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity in range [-1, 1]
        """
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Error computing cosine similarity: {e}")
            return 0.0

    def _limit_relations_per_concept(self, relations: List[Relation]) -> List[Relation]:
        """
        Limit the number of relations per concept.

        For each concept, keep only the top-k relations by confidence/strength
        to prevent concept explosion in the knowledge graph.

        Args:
            relations: List of relations

        Returns:
            Filtered list of relations
        """
        if not relations:
            return relations

        # Count relations per concept
        concept_counts = Counter()

        # For each relation, increment count for both source and target
        for relation in relations:
            concept_counts[relation.source_concept] += 1
            concept_counts[relation.target_concept] += 1

        # If no concept exceeds limit, return all
        if all(count <= self.config.max_relations_per_concept for count in concept_counts.values()):
            return relations

        # Otherwise, filter relations
        filtered_relations = []

        # Group relations by source concept
        by_source = defaultdict(list)
        for relation in relations:
            by_source[relation.source_concept].append(relation)

        # For each source, keep top-k by confidence
        for source, source_relations in by_source.items():
            # Sort by confidence descending
            sorted_relations = sorted(
                source_relations,
                key=lambda r: (r.confidence, r.strength),
                reverse=True
            )

            # Keep top-k
            top_k = sorted_relations[:self.config.max_relations_per_concept]
            filtered_relations.extend(top_k)

        return filtered_relations
