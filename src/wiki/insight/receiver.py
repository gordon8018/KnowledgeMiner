"""
Insight receiver for managing and prioritizing insights.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.discovery.models.insight import Insight
from src.wiki.insight.scorer import PriorityScorer, PriorityLevel

logger = logging.getLogger(__name__)


class InsightReceiver:
    """
    Receive, score, and prioritize insights.

    Manages a queue of pending insights with enhanced priority scoring.
    """

    def __init__(self):
        """Initialize InsightReceiver."""
        self.scorer = PriorityScorer()
        self.pending_insights: List[Insight] = []

    def receive(
        self,
        insights: List[Insight],
        backfilled: bool = False
    ) -> List[Insight]:
        """
        Receive and score insights.

        Args:
            insights: List of insights to receive
            backfilled: Whether these insights are backfilled (default: False)

        Returns:
            List of received insights with scoring metadata added
        """
        received = []

        for insight in insights:
            # Score the insight
            scoring_result = self._score_insight(insight)

            # Add scoring metadata to insight
            insight.metadata.update({
                "priority_score": scoring_result["priority_score"],
                "priority_level": scoring_result["priority_level"],
                "novelty_rating": scoring_result["novelty_rating"],
                "impact_rating": scoring_result["impact_rating"],
                "actionability_rating": scoring_result["actionability_rating"],
                "novelty_score": scoring_result["novelty_score"],
                "impact_score": scoring_result["impact_score"],
                "actionability_score": scoring_result["actionability_score"],
                "received_at": datetime.now().isoformat(),
                "backfilled": backfilled
            })

            # Add to pending insights
            self.pending_insights.append(insight)
            received.append(insight)

            logger.info(
                f"Received insight {insight.id} with "
                f"priority_score={scoring_result['priority_score']:.3f}, "
                f"priority_level={scoring_result['priority_level'].value}"
            )

        return received

    def prioritize(self) -> List[Insight]:
        """
        Get prioritized insights sorted by priority_score (descending).

        P0_IMMEDIATE insights are returned first, then P1_PRIORITY, etc.
        Within each priority level, insights are sorted by priority_score.

        Returns:
            List of prioritized insights
        """
        if not self.pending_insights:
            return []

        # Sort by priority_score descending (highest first)
        prioritized = sorted(
            self.pending_insights,
            key=lambda i: i.metadata["priority_score"],
            reverse=True
        )

        return prioritized

    def _score_insight(self, insight: Insight) -> Dict[str, Any]:
        """
        Score an insight using PriorityScorer.

        Args:
            insight: Insight to score

        Returns:
            Scoring result dictionary
        """
        # Get ratings from insight metadata or use defaults
        novelty_rating = insight.metadata.get("novelty_rating", "moderate")
        impact_rating = insight.metadata.get("impact_rating", "medium")
        actionability_rating = insight.metadata.get("actionability_rating", "medium_term")

        # Score the insight
        result = self.scorer.score(
            novelty_rating=novelty_rating,
            impact_rating=impact_rating,
            actionability_rating=actionability_rating
        )

        return result

    def _priority_level_rank(self, level: PriorityLevel) -> int:
        """
        Get numeric rank for priority level (lower is higher priority).

        Args:
            level: PriorityLevel enum

        Returns:
            Integer rank (0 for P0, 1 for P1, etc.)
        """
        ranks = {
            PriorityLevel.P0_IMMEDIATE: 0,
            PriorityLevel.P1_PRIORITY: 1,
            PriorityLevel.P2_STANDARD: 2,
            PriorityLevel.P3_DEFERRED: 3
        }
        return ranks.get(level, 99)

    def clear_pending(self) -> None:
        """
        Clear all pending insights.

        Useful for testing or resetting state.
        """
        self.pending_insights.clear()

    def get_pending_count(self) -> int:
        """
        Get count of pending insights.

        Returns:
            Number of pending insights
        """
        return len(self.pending_insights)

    def get_insights_by_priority_level(self, level: PriorityLevel) -> List[Insight]:
        """
        Get all insights of a specific priority level.

        Args:
            level: PriorityLevel to filter by

        Returns:
            List of insights with the specified priority level
        """
        return [
            insight for insight in self.pending_insights
            if insight.metadata.get("priority_level") == level
        ]
