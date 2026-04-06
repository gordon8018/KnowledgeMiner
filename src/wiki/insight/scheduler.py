"""
Backfill scheduler for priority-based insight scheduling.
"""

import logging
import json
from collections import deque
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from src.wiki.insight.scorer import PriorityLevel

logger = logging.getLogger(__name__)


class BackfillScheduler:
    """
    Schedule insights into priority-based queues for backfill processing.

    Implements two queue types:
    - ImmediateQueue: For P0 insights (score >= 0.8), processed immediately
    - BatchQueue: For P1, P2, P3 insights, processed in priority order (P1 > P2 > P3)

    Queue persistence: Queue state is automatically saved to disk after each
    schedule() call and loaded on initialization if available.
    """

    PERSISTENCE_FILE = "scheduler_queue.json"

    def __init__(self, persistence_dir: str = None):
        """
        Initialize BackfillScheduler with empty queues.

        Args:
            persistence_dir: Directory for queue persistence file (default: current directory)
        """
        # Immediate queue for P0 insights
        self._immediate_queue: deque = deque()

        # Batch queues for P1, P2, P3 insights
        self._batch_queue_p1: deque = deque()
        self._batch_queue_p2: deque = deque()
        self._batch_queue_p3: deque = deque()

        # Setup persistence
        self._persistence_path = None
        if persistence_dir:
            self._persistence_path = Path(persistence_dir) / self.PERSISTENCE_FILE
            self._load_queue_state()

    def _serialize_queue(self, queue: deque) -> List[Dict[str, Any]]:
        """
        Serialize queue to list for JSON storage.

        Args:
            queue: Queue to serialize

        Returns:
            List of serializable items
        """
        serialized = []
        for item in queue:
            # Convert Insight object to dict
            insight_dict = {
                "id": item["insight"].id,
                "insight_type": item["insight"].insight_type.value,
                "title": item["insight"].title,
                "description": item["insight"].description,
                "significance": item["insight"].significance,
                "related_concepts": item["insight"].related_concepts,
                "related_patterns": item["insight"].related_patterns,
                "related_gaps": item["insight"].related_gaps,
                "evidence": [
                    {
                        "source_id": e.source_id,
                        "content": e.content,
                        "confidence": e.confidence
                    }
                    for e in item["insight"].evidence
                ],
                "actionable_suggestions": item["insight"].actionable_suggestions,
                "generated_at": item["insight"].generated_at.isoformat(),
                "metadata": item["insight"].metadata
            }

            serialized.append({
                "insight": insight_dict,
                "scores": item["scores"],
                "received_at": item["received_at"],
                "backfilled": item["backfilled"]
            })

        return serialized

    def _deserialize_queue(self, serialized: List[Dict[str, Any]]) -> deque:
        """
        Deserialize list from JSON storage back to queue.

        Args:
            serialized: List of serialized items

        Returns:
            Queue with deserialized items
        """
        from src.discovery.models.insight import Insight, InsightType
        from src.discovery.models.pattern import Evidence

        queue = deque()
        for item in serialized:
            # Reconstruct Evidence objects
            evidence_list = [
                Evidence(
                    source_id=e["source_id"],
                    content=e["content"],
                    confidence=e["confidence"]
                )
                for e in item["insight"]["evidence"]
            ]

            # Reconstruct Insight object
            insight = Insight(
                id=item["insight"]["id"],
                insight_type=InsightType(item["insight"]["insight_type"]),
                title=item["insight"]["title"],
                description=item["insight"]["description"],
                significance=item["insight"]["significance"],
                related_concepts=item["insight"]["related_concepts"],
                related_patterns=item["insight"]["related_patterns"],
                related_gaps=item["insight"]["related_gaps"],
                evidence=evidence_list,
                actionable_suggestions=item["insight"]["actionable_suggestions"],
                generated_at=datetime.fromisoformat(item["insight"]["generated_at"]),
                metadata=item["insight"]["metadata"]
            )

            queue.append({
                "insight": insight,
                "scores": item["scores"],
                "received_at": item["received_at"],
                "backfilled": item["backfilled"]
            })

        return queue

    def _save_queue_state(self) -> None:
        """
        Save current queue state to persistence file.

        Called automatically after each schedule() operation.
        """
        if not self._persistence_path:
            return

        try:
            state = {
                "immediate_queue": self._serialize_queue(self._immediate_queue),
                "batch_queue_p1": self._serialize_queue(self._batch_queue_p1),
                "batch_queue_p2": self._serialize_queue(self._batch_queue_p2),
                "batch_queue_p3": self._serialize_queue(self._batch_queue_p3),
                "saved_at": datetime.now().isoformat()
            }

            self._persistence_path.write_text(json.dumps(state, indent=2))
            logger.debug(f"Saved queue state to {self._persistence_path}")

        except Exception as e:
            logger.warning(f"Failed to save queue state: {e}")

    def _load_queue_state(self) -> None:
        """
        Load queue state from persistence file.

        Called automatically during initialization if persistence file exists.
        """
        if not self._persistence_path or not self._persistence_path.exists():
            return

        try:
            state = json.loads(self._persistence_path.read_text())

            self._immediate_queue = self._deserialize_queue(state["immediate_queue"])
            self._batch_queue_p1 = self._deserialize_queue(state["batch_queue_p1"])
            self._batch_queue_p2 = self._deserialize_queue(state["batch_queue_p2"])
            self._batch_queue_p3 = self._deserialize_queue(state["batch_queue_p3"])

            logger.info(
                f"Loaded queue state from {self._persistence_path} "
                f"(saved at {state.get('saved_at', 'unknown')})"
            )

        except Exception as e:
            logger.warning(f"Failed to load queue state: {e}. Starting with empty queues.")

    def schedule(self, insights_with_scores: List[Dict[str, Any]]) -> None:
        """
        Schedule scored insights to appropriate queues based on priority level.

        Automatically saves queue state to disk after scheduling.

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

        # Save queue state after scheduling
        self._save_queue_state()

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
