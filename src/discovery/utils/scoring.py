"""
Scoring utilities for insights and patterns.
"""

from typing import List, Dict, Any
import numpy as np


def compute_significance_score(
    novelty: float,
    impact: float,
    actionability: float,
    weights: Dict[str, float] = None
) -> float:
    """
    Compute significance score using weighted formula.

    Formula: significance = novelty × 0.25 + impact × 0.40 + actionability × 0.35

    Args:
        novelty: Novelty score (0.0-1.0)
        impact: Impact score (0.0-1.0)
        actionability: Actionability score (0.0-1.0)
        weights: Optional custom weights (default: novelty=0.25, impact=0.40, actionability=0.35)

    Returns:
        Significance score (0.0-1.0)
    """
    if weights is None:
        weights = {'novelty': 0.25, 'impact': 0.40, 'actionability': 0.35}

    significance = (
        novelty * weights['novelty'] +
        impact * weights['impact'] +
        actionability * weights['actionability']
    )

    return max(0.0, min(1.0, significance))


def normalize_scores(scores: List[float]) -> List[float]:
    """
    Normalize scores to 0-1 range using min-max normalization.

    Args:
        scores: List of raw scores

    Returns:
        List of normalized scores (0.0-1.0)
    """
    if not scores:
        return []

    scores_array = np.array(scores)
    min_score = np.min(scores_array)
    max_score = np.max(scores_array)

    if max_score == min_score:
        # All scores are the same
        return [1.0] * len(scores)

    normalized = (scores_array - min_score) / (max_score - min_score)
    return normalized.tolist()


def rank_by_score(items: List[Any], score_key: str, reverse: bool = True) -> List[Any]:
    """
    Rank items by their score.

    Args:
        items: List of items with score attribute
        score_key: Attribute name for score
        reverse: True for descending (highest first), False for ascending

    Returns:
        Sorted list of items
    """
    return sorted(items, key=lambda x: getattr(x, score_key, 0), reverse=reverse)
