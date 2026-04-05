"""
Insight generation with multi-strategy fusion.

This module implements insight generation from patterns, relations, and gaps,
using multiple strategies and significance-based ranking.
"""

from typing import List
from datetime import datetime
from src.discovery.config import DiscoveryConfig
from src.discovery.models.insight import Insight, InsightType
from src.discovery.models.pattern import Pattern, PatternType
from src.discovery.models.gap import KnowledgeGap, GapType
from src.discovery.utils.scoring import compute_significance_score, rank_by_score
from src.core.relation_model import Relation


class InsightGenerator:
    """
    Generate insights from patterns, relations, and knowledge gaps.

    Implements multi-strategy fusion:
    1. Pattern insights - Convert patterns to insights
    2. Relation insights - Extract strong relations as insights
    3. Gap insights - Convert knowledge gaps to actionable insights
    4. Integrated insights - Cross-type analysis
    """

    def __init__(self, config: DiscoveryConfig, llm_provider):
        """
        Initialize InsightGenerator.

        Args:
            config: DiscoveryConfig instance
            llm_provider: LLM provider for enhanced analysis (optional)
        """
        self.config = config
        self.llm_provider = llm_provider

    def generate_insights(
        self,
        relations: List[Relation],
        patterns: List[Pattern],
        gaps: List[KnowledgeGap]
    ) -> List[Insight]:
        """
        Generate insights from all sources.

        Args:
            relations: List of relations
            patterns: List of patterns
            gaps: List of knowledge gaps

        Returns:
            List of ranked and filtered insights
        """
        all_insights = []

        # Generate insights from each source
        pattern_insights = self._generate_pattern_insights(patterns)
        all_insights.extend(pattern_insights)

        relation_insights = self._generate_relation_insights(relations)
        all_insights.extend(relation_insights)

        gap_insights = self._generate_gap_insights(gaps)
        all_insights.extend(gap_insights)

        integrated_insights = self._generate_integrated_insights(
            patterns, relations, gaps
        )
        all_insights.extend(integrated_insights)

        # Rank and filter insights
        ranked_insights = self._rank_insights(all_insights)

        return ranked_insights

    def _generate_pattern_insights(self, patterns: List[Pattern]) -> List[Insight]:
        """
        Generate insights from patterns.

        Args:
            patterns: List of detected patterns

        Returns:
            List of pattern-based insights
        """
        insights = []

        for pattern in patterns:
            # Compute significance scores
            novelty = min(1.0, pattern.confidence + 0.2)
            impact = pattern.significance_score
            actionability = 0.7

            significance = compute_significance_score(
                novelty=novelty,
                impact=impact,
                actionability=actionability
            )

            # Generate pattern-specific suggestions
            suggestions = self._generate_pattern_suggestions(pattern)

            # Create insight
            insight = Insight(
                id=f"insight-pattern-{pattern.id}",
                insight_type=InsightType.PATTERN,
                title=f"Pattern Insight: {pattern.title}",
                description=pattern.description,
                significance=significance,
                related_concepts=pattern.related_concepts.copy(),
                related_patterns=[pattern.id],
                related_gaps=[],
                evidence=pattern.evidence.copy(),
                actionable_suggestions=suggestions,
                generated_at=datetime.now(),
                metadata={
                    'pattern_id': pattern.id,
                    'pattern_type': pattern.pattern_type.value,
                    'pattern_confidence': pattern.confidence,
                    'pattern_significance': pattern.significance_score,
                    'novelty': novelty,
                    'impact': impact,
                    'actionability': actionability
                }
            )

            insights.append(insight)

        return insights

    def _generate_relation_insights(self, relations: List[Relation]) -> List[Insight]:
        """
        Generate insights from strong relations.

        Args:
            relations: List of relations

        Returns:
            List of relation-based insights
        """
        insights = []

        # Filter for strong relations (strength >= 0.7)
        strong_relations = [
            r for r in relations if r.strength >= 0.7
        ]

        # Sort by strength and take top 10
        strong_relations.sort(key=lambda x: x.strength, reverse=True)
        top_relations = strong_relations[:10]

        for relation in top_relations:
            # Compute significance scores
            novelty = 0.5  # Relations may not be novel
            impact = relation.strength
            actionability = 0.6

            significance = compute_significance_score(
                novelty=novelty,
                impact=impact,
                actionability=actionability
            )

            # Generate generic suggestions for relation exploration
            relation_type_str = relation.relation_type if isinstance(relation.relation_type, str) else relation.relation_type.value
            suggestions = [
                f"Investigate the {relation_type_str} relationship between {relation.source_concept} and {relation.target_concept}",
                f"Explore how {relation.source_concept} influences {relation.target_concept}",
                f"Consider the implications of this relationship for the broader knowledge graph"
            ]

            # Create insight
            insight = Insight(
                id=f"insight-relation-{relation.id}",
                insight_type=InsightType.RELATION,
                title=f"Strong Relationship: {relation.source_concept} → {relation.target_concept}",
                description=f"Strong {relation_type_str} relationship (strength: {relation.strength:.2f})",
                significance=significance,
                related_concepts=[relation.source_concept, relation.target_concept],
                related_patterns=[],
                related_gaps=[],
                evidence=[],
                actionable_suggestions=suggestions,
                generated_at=datetime.now(),
                metadata={
                    'relation_id': relation.id,
                    'relation_type': relation_type_str,
                    'relation_strength': relation.strength,
                    'relation_confidence': relation.confidence,
                    'novelty': novelty,
                    'impact': impact,
                    'actionability': actionability
                }
            )

            insights.append(insight)

        return insights

    def _generate_gap_insights(self, gaps: List[KnowledgeGap]) -> List[Insight]:
        """
        Generate insights from knowledge gaps.

        Args:
            gaps: List of knowledge gaps

        Returns:
            List of gap-based insights
        """
        insights = []

        for gap in gaps:
            # Compute significance scores
            novelty = 0.8  # Gaps point to novel areas
            impact = gap.severity
            actionability = gap.priority / 10.0

            significance = compute_significance_score(
                novelty=novelty,
                impact=impact,
                actionability=actionability
            )

            # Use gap's suggested actions directly
            suggestions = gap.suggested_actions.copy()

            # Create insight
            insight = Insight(
                id=f"insight-gap-{gap.id}",
                insight_type=InsightType.GAP,
                title=f"Knowledge Gap: {gap.gap_type.value}",
                description=gap.description,
                significance=significance,
                related_concepts=gap.affected_concepts.copy(),
                related_patterns=[],
                related_gaps=[gap.id],
                evidence=[],
                actionable_suggestions=suggestions,
                generated_at=datetime.now(),
                metadata={
                    'gap_id': gap.id,
                    'gap_type': gap.gap_type.value,
                    'gap_severity': gap.severity,
                    'gap_priority': gap.priority,
                    'estimated_effort': gap.estimated_effort,
                    'novelty': novelty,
                    'impact': impact,
                    'actionability': actionability
                }
            )

            insights.append(insight)

        return insights

    def _generate_integrated_insights(
        self,
        patterns: List[Pattern],
        relations: List[Relation],
        gaps: List[KnowledgeGap]
    ) -> List[Insight]:
        """
        Generate integrated insights from cross-type analysis.

        Args:
            patterns: List of patterns
            relations: List of relations
            gaps: List of knowledge gaps

        Returns:
            List of integrated insights
        """
        insights = []

        # Example: Temporal patterns with related gaps
        temporal_patterns = [
            p for p in patterns if p.pattern_type == PatternType.TEMPORAL
        ]

        for pattern in temporal_patterns:
            # Find gaps related to pattern concepts
            related_gaps = []
            for gap in gaps:
                if any(concept in pattern.related_concepts for concept in gap.affected_concepts):
                    related_gaps.append(gap)

            if related_gaps:
                # Compute significance scores
                novelty = 0.9  # Integrated insights are novel
                impact = pattern.confidence
                actionability = 0.8

                significance = compute_significance_score(
                    novelty=novelty,
                    impact=impact,
                    actionability=actionability
                )

                # Generate suggestions
                suggestions = [
                    f"Address knowledge gaps in the context of the {pattern.title} pattern",
                    f"Focus on understanding how {pattern.title} interacts with missing concepts",
                    f"Consider whether the temporal pattern reveals blind spots in current knowledge"
                ]

                # Create insight
                insight = Insight(
                    id=f"insight-integrated-{pattern.id}",
                    insight_type=InsightType.INTEGRATED,
                    title=f"Integrated Insight: {pattern.title} + Knowledge Gaps",
                    description=f"Temporal pattern '{pattern.title}' has {len(related_gaps)} related knowledge gaps",
                    significance=significance,
                    related_concepts=pattern.related_concepts.copy(),
                    related_patterns=[pattern.id],
                    related_gaps=[g.id for g in related_gaps],
                    evidence=pattern.evidence.copy(),
                    actionable_suggestions=suggestions,
                    generated_at=datetime.now(),
                    metadata={
                        'pattern_id': pattern.id,
                        'related_gap_ids': [g.id for g in related_gaps],
                        'integration_type': 'temporal_pattern_with_gaps',
                        'novelty': novelty,
                        'impact': impact,
                        'actionability': actionability
                    }
                )

                insights.append(insight)

        return insights

    def _generate_pattern_suggestions(self, pattern: Pattern) -> List[str]:
        """
        Generate pattern-specific actionable suggestions.

        Args:
            pattern: Pattern to generate suggestions for

        Returns:
            List of actionable suggestions
        """
        suggestions = []

        if pattern.pattern_type == PatternType.TEMPORAL:
            period = pattern.metadata.get('period', 'recurring')
            suggestions = [
                f"Monitor for recurring {pattern.title}",
                f"Prepare for the next occurrence of this {period} pattern",
                f"Establish monitoring for {period} cycles",
                f"Create alerts for {period} pattern violations"
            ]

        elif pattern.pattern_type == PatternType.CAUSAL:
            chain_length = pattern.metadata.get('chain_length', 2)
            suggestions = [
                f"Investigate root causes in the causal chain",
                f"Consider intervention points in this causal relationship",
                f"Analyze the {chain_length}-step causal chain for leverage points",
                f"Explore whether causal factors can be influenced"
            ]

        elif pattern.pattern_type == PatternType.EVOLUTIONARY:
            versions = pattern.metadata.get('versions', 0)
            suggestions = [
                f"Track concept evolution over time",
                f"Update documentation to reflect latest concept version",
                f"Analyze evolution pattern to predict future changes",
                f"Consider whether current version is optimal"
            ]

        elif pattern.pattern_type == PatternType.CONFLICT:
            conflicts = pattern.metadata.get('conflicts', 0)
            suggestions = [
                f"Reconcile conflicting information in these concepts",
                f"Investigate sources of conflict",
                f"Determine which conflicting concepts are more reliable",
                f"Resolve {conflicts} conflicts to improve knowledge consistency"
            ]

        else:
            suggestions = [
                f"Investigate this {pattern.pattern_type.value} pattern further",
                f"Analyze implications of this pattern",
                f"Consider how this pattern affects related concepts"
            ]

        return suggestions

    def _rank_insights(self, insights: List[Insight]) -> List[Insight]:
        """
        Rank insights by significance and apply filtering.

        Args:
            insights: List of insights to rank

        Returns:
            Ranked and filtered list of insights
        """
        # Rank by significance (descending)
        ranked = rank_by_score(insights, 'significance', reverse=True)

        # Filter by significance threshold
        filtered = [
            insight for insight in ranked
            if insight.significance >= self.config.insight_significance_threshold
        ]

        # Limit to max_insights
        limited = filtered[:self.config.max_insights]

        return limited
