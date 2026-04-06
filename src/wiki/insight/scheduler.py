"""
Backfill scheduler for priority-based insight scheduling.
"""

import logging
from collections import deque
from typing import List, Dict, Any

from src.wiki.insight.scorer import PriorityLevel

logger = logging.getLogger(__name__)


class BackfillScheduler:
    """
    Schedule insights into priority-based queues for backfill processing.

    Implements two queue types:
    - ImmediateQueue: For P0 insights (score >= 0.8), processed immediately
    - BatchQueue: For P1, P2, P3 insights, processed in priority order (P1 > P2 > P3)
    """

    def __init__(self):
        """Initialize BackfillScheduler with empty queues."""
        # Immediate queue for P0 insights
        self._immediate_queue: deque = deque()

        # Batch queues for P1, P2, P3 insights
        self._batch_queue_p1: deque = deque()
        self._batch_queue_p2: deque = deque()
        self._batch_queue_p3: deque = deque()

    def schedule(self, insights_with_scores: List[Dict[str, Any]]) -> None:
        """
        Schedule scored insights to appropriate queues based on priority level.

        Args:
            insights_with_scores: List of dicts with keys:
                - insight: Insight object
                - scores: Dict with priority_score and priority_level
                - received_at: ISO timestamp
                - backfilled: bool
        """
        for item in insights_with_scores:
            priority_level = item["scores"]["priority_level"]

            # Route to appropriate queue based on priority level
            if priority_level == PriorityLevel.P0_IMMEDIATE:
                self._immediate_queue.append(item)
                logger.debug(f"Scheduled P0 insight {item['insight'].id} to immediate queue")
            elif priority_level == PriorityLevel.P1_PRIORITY:
                self._batch_queue_p1.append(item)
                logger.debug(f"Scheduled P1 insight {item['insight'].id} to batch queue")
            elif priority_level == PriorityLevel.P2_STANDARD:
                self._batch_queue_p2.append(item)
                logger.debug(f"Scheduled P2 insight {item['insight'].id} to batch queue")
            elif priority_level == PriorityLevel.P3_DEFERRED:
                self._batch_queue_p3.append(item)
                logger.debug(f"Scheduled P3 insight {item['insight'].id} to batch queue")
            else:
                logger.warning(f"Unknown priority level {priority_level} for insight {item['insight'].id}")

    def get_immediate_batch(self, max_size: int = 10) -> List[Dict[str, Any]]:
        """
        Get next batch from immediate queue (P0 insights only).

        Args:
            max_size: Maximum number of insights to return (default: 10)

        Returns:
            List of insight dicts from immediate queue
        """
        batch = []

        # Get up to max_size items from immediate queue
        for _ in range(max_size):
            if not self._immediate_queue:
                break
            batch.append(self._immediate_queue.popleft())

        if batch:
            logger.debug(f"Retrieved {len(batch)} insights from immediate queue")

        return batch

    def get_batch(self, max_size: int = 50) -> List[Dict[str, Any]]:
        """
        Get next batch from batch queue, prioritizing P1 > P2 > P3.

        Args:
            max_size: Maximum number of insights to return (default: 50)

        Returns:
            List of insight dicts from batch queues in priority order
        """
        batch = []

        # Prioritize P1 > P2 > P3
        priority_queues = [
            self._batch_queue_p1,
            self._batch_queue_p2,
            self._batch_queue_p3
        ]

        # Fill batch from queues in priority order
        for queue in priority_queues:
            while len(batch) < max_size and queue:
                batch.append(queue.popleft())

            if len(batch) >= max_size:
                break

        if batch:
            logger.debug(f"Retrieved {len(batch)} insights from batch queues")

        return batch

    def get_queue_sizes(self) -> Dict[str, int]:
        """
        Get statistics about queue sizes.

        Returns:
            Dictionary with keys:
                - immediate_queue: Count of P0 insights
                - batch_queue_p1: Count of P1 insights
                - batch_queue_p2: Count of P2 insights
                - batch_queue_p3: Count of P3 insights
                - total: Total count across all queues
        """
        immediate_count = len(self._immediate_queue)
        p1_count = len(self._batch_queue_p1)
        p2_count = len(self._batch_queue_p2)
        p3_count = len(self._batch_queue_p3)
        total = immediate_count + p1_count + p2_count + p3_count

        return {
            "immediate_queue": immediate_count,
            "batch_queue_p1": p1_count,
            "batch_queue_p2": p2_count,
            "batch_queue_p3": p3_count,
            "total": total
        }

    def clear_all(self) -> None:
        """
        Empty all queues.

        Useful for testing or resetting state.
        """
        self._immediate_queue.clear()
        self._batch_queue_p1.clear()
        self._batch_queue_p2.clear()
        self._batch_queue_p3.clear()
        logger.debug("Cleared all queues")
