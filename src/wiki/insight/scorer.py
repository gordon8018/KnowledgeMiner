"""
Priority scoring with enhanced rubrics for insight management.
"""

from enum import Enum
from typing import Dict, Any


class PriorityLevel(str, Enum):
    """Priority levels for insights."""
    P0_IMMEDIATE = "P0_IMMEDIATE"      # score >= 0.8
    P1_PRIORITY = "P1_PRIORITY"        # 0.6 <= score < 0.8
    P2_STANDARD = "P2_STANDARD"        # 0.4 <= score < 0.6
    P3_DEFERRED = "P3_DEFERRED"        # score < 0.4


class PriorityScorer:
    """
    Score insights using enhanced rubrics for novelty, impact, and actionability.

    Scoring formula:
        priority_score = (novelty × 0.25) + (impact × 0.40) + (actionability × 0.35)
    """

    # Novelty rubrics: (min_score, max_score)
    NOVELTY_RUBRICS = {
        "breakthrough": (0.9, 1.0),   # weight 5.0
        "significant": (0.7, 0.9),    # weight 4.0
        "moderate": (0.5, 0.7),       # weight 3.0
        "incremental": (0.3, 0.5),    # weight 2.0
        "minimal": (0.0, 0.3)         # weight 1.0
    }

    # Impact rubrics: (min_score, max_score)
    IMPACT_RUBRICS = {
        "critical": (0.8, 1.0),       # weight 5.0
        "high": (0.6, 0.8),           # weight 4.0
        "medium": (0.4, 0.6),         # weight 3.0
        "low": (0.2, 0.4),            # weight 2.0
        "minimal": (0.0, 0.2)         # weight 1.0
    }

    # Actionability rubrics: (min_score, max_score)
    ACTIONABILITY_RUBRICS = {
        "immediate": (0.8, 1.0),      # weight 5.0
        "short_term": (0.6, 0.8),     # weight 4.0
        "medium_term": (0.4, 0.6),    # weight 3.0
        "long_term": (0.2, 0.4),      # weight 2.0
        "unclear": (0.0, 0.2)         # weight 1.0
    }

    # Scoring weights
    NOVELTY_WEIGHT = 0.25
    IMPACT_WEIGHT = 0.40
    ACTIONABILITY_WEIGHT = 0.35

    def score(
        self,
        novelty_rating: str,
        impact_rating: str,
        actionability_rating: str
    ) -> Dict[str, Any]:
        """
        Calculate priority score for an insight.

        Args:
            novelty_rating: Novelty rating (breakthrough, significant, moderate, incremental, minimal)
            impact_rating: Impact rating (critical, high, medium, low, minimal)
            actionability_rating: Actionability rating (immediate, short_term, medium_term, long_term, unclear)

        Returns:
            Dictionary with:
                - priority_score: float (0.0-1.0)
                - priority_level: PriorityLevel enum
                - novelty_rating: str
                - impact_rating: str
                - actionability_rating: str
        """
        # Score each dimension
        novelty_score = self._score_novelty(novelty_rating)
        impact_score = self._score_impact(impact_rating)
        actionability_score = self._score_actionability(actionability_rating)

        # Calculate weighted priority score
        priority_score = (
            novelty_score * self.NOVELTY_WEIGHT +
            impact_score * self.IMPACT_WEIGHT +
            actionability_score * self.ACTIONABILITY_WEIGHT
        )

        # Determine priority level
        priority_level = self._classify_priority_level(priority_score)

        return {
            "priority_score": round(priority_score, 3),
            "priority_level": priority_level,
            "novelty_rating": novelty_rating,
            "impact_rating": impact_rating,
            "actionability_rating": actionability_rating,
            "novelty_score": round(novelty_score, 3),
            "impact_score": round(impact_score, 3),
            "actionability_score": round(actionability_score, 3)
        }

    def _score_novelty(self, rating: str) -> float:
        """
        Score novelty rating.

        Args:
            rating: Novelty rating string

        Returns:
            Score between min and max for this rating (midpoint for determinism)
        """
        if rating not in self.NOVELTY_RUBRICS:
            raise ValueError(f"Invalid novelty rating: {rating}. Must be one of {list(self.NOVELTY_RUBRICS.keys())}")

        min_score, max_score = self.NOVELTY_RUBRICS[rating]
        # Return midpoint for deterministic scoring
        return (min_score + max_score) / 2.0

    def _score_impact(self, rating: str) -> float:
        """
        Score impact rating.

        Args:
            rating: Impact rating string

        Returns:
            Score between min and max for this rating (midpoint for determinism)
        """
        if rating not in self.IMPACT_RUBRICS:
            raise ValueError(f"Invalid impact rating: {rating}. Must be one of {list(self.IMPACT_RUBRICS.keys())}")

        min_score, max_score = self.IMPACT_RUBRICS[rating]
        # Return midpoint for deterministic scoring
        return (min_score + max_score) / 2.0

    def _score_actionability(self, rating: str) -> float:
        """
        Score actionability rating.

        Args:
            rating: Actionability rating string

        Returns:
            Score between min and max for this rating (midpoint for determinism)
        """
        if rating not in self.ACTIONABILITY_RUBRICS:
            raise ValueError(f"Invalid actionability rating: {rating}. Must be one of {list(self.ACTIONABILITY_RUBRICS.keys())}")

        min_score, max_score = self.ACTIONABILITY_RUBRICS[rating]
        # Return midpoint for deterministic scoring
        return (min_score + max_score) / 2.0

    def _classify_priority_level(self, score: float) -> PriorityLevel:
        """
        Classify score into priority level.

        Args:
            score: Priority score (0.0-1.0)

        Returns:
            PriorityLevel enum
        """
        if score >= 0.8:
            return PriorityLevel.P0_IMMEDIATE
        elif score >= 0.6:
            return PriorityLevel.P1_PRIORITY
        elif score >= 0.4:
            return PriorityLevel.P2_STANDARD
        else:
            return PriorityLevel.P3_DEFERRED
