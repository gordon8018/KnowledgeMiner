"""
Mode selector for determining processing strategy based on changeset characteristics.

This module provides intelligent selection between FULL, INCREMENTAL, and HYBRID
processing modes based on changeset size, impact, and type.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List


class ProcessingMode(str, Enum):
    """Processing mode for wiki compilation."""

    FULL = "full"
    INCREMENTAL = "incremental"
    HYBRID = "hybrid"


class ModeSelector:
    """
    Selects the appropriate processing mode based on changeset characteristics.

    Uses smart heuristics to balance between processing speed and completeness.
    """

    def __init__(
        self,
        incremental_threshold: int = 10,
        force_full_after_days: int = 7,
        enable_smart_selection: bool = True,
        last_full_run: Optional[datetime] = None
    ):
        """
        Initialize the ModeSelector.

        Args:
            incremental_threshold: Maximum changes for simple INCREMENTAL mode
            force_full_after_days: Days before forcing a FULL run
            enable_smart_selection: Whether to use smart selection heuristics
            last_full_run: Timestamp of the last FULL processing run
        """
        self.incremental_threshold = incremental_threshold
        self.force_full_after_days = force_full_after_days
        self.enable_smart_selection = enable_smart_selection
        self.last_full_run = last_full_run

    def select_mode(self, changeset: Dict[str, List[str]]) -> ProcessingMode:
        """
        Select the appropriate processing mode for the given changeset.

        Args:
            changeset: Dictionary with 'added', 'modified', and 'deleted' file lists

        Returns:
            ProcessingMode: The selected processing mode
        """
        # Check if we should force a full run
        if self._should_force_full():
            return ProcessingMode.FULL

        # Use smart or simple selection based on configuration
        if self.enable_smart_selection:
            return self._smart_selection(changeset)
        else:
            return self._simple_selection(changeset)

    def _should_force_full(self) -> bool:
        """
        Determine if a FULL run should be forced.

        Returns:
            bool: True if FULL mode should be forced
        """
        # Don't force on first run - let normal selection logic handle it
        if self.last_full_run is None:
            return False

        # Force if timeout has elapsed
        days_since_last = (datetime.now() - self.last_full_run).days
        return days_since_last >= self.force_full_after_days

    def _simple_selection(self, changeset: Dict[str, List[str]]) -> ProcessingMode:
        """
        Simple selection strategy based on change size only.

        Args:
            changeset: Dictionary with 'added', 'modified', and 'deleted' file lists

        Returns:
            ProcessingMode: INCREMENTAL if small changeset, FULL otherwise
        """
        total_changes = (
            len(changeset.get('added', [])) +
            len(changeset.get('modified', [])) +
            len(changeset.get('deleted', []))
        )

        if total_changes <= self.incremental_threshold:
            return ProcessingMode.INCREMENTAL
        else:
            return ProcessingMode.FULL

    def _smart_selection(self, changeset: Dict[str, List[str]]) -> ProcessingMode:
        """
        Smart selection strategy using multiple heuristics.

        Heuristics:
        1. Change size: >50 → FULL, <=threshold → INCREMENTAL
        2. Change type: deletions → FULL
        3. Impact score: >0.7 → FULL, <0.3 → INCREMENTAL

        Args:
            changeset: Dictionary with 'added', 'modified', and 'deleted' file lists

        Returns:
            ProcessingMode: FULL, INCREMENTAL, or HYBRID
        """
        added = changeset.get('added', [])
        modified = changeset.get('modified', [])
        deleted = changeset.get('deleted', [])

        total_changes = len(added) + len(modified) + len(deleted)

        # Heuristic 1: Change size
        if total_changes > 50:
            return ProcessingMode.FULL
        elif total_changes <= self.incremental_threshold:
            return ProcessingMode.INCREMENTAL

        # Heuristic 2: Change type (deletions have highest priority)
        if deleted:
            return ProcessingMode.FULL

        # Heuristic 3: Impact score
        impact_score = self._calculate_impact_score(added, modified, deleted)
        if impact_score > 0.7:
            return ProcessingMode.FULL
        elif impact_score < 0.3:
            return ProcessingMode.INCREMENTAL

        # Default to HYBRID for moderate changesets
        return ProcessingMode.HYBRID

    def _calculate_impact_score(
        self,
        added: List[str],
        modified: List[str],
        deleted: List[str]
    ) -> float:
        """
        Calculate impact score based on change types.

        Higher impact = more disruptive changes.

        Args:
            added: List of added files
            modified: List of modified files
            deleted: List of deleted files

        Returns:
            float: Impact score between 0.0 and 1.0
        """
        total_changes = len(added) + len(modified) + len(deleted)

        if total_changes == 0:
            return 0.0

        # Weight different change types
        # Deletions have highest impact, modifications medium, additions low
        deletion_weight = 2.0
        modification_weight = 1.0
        addition_weight = 0.5

        weighted_sum = (
            len(added) * addition_weight +
            len(modified) * modification_weight +
            len(deleted) * deletion_weight
        )

        # Normalize by max possible weight (all deletions)
        max_weight = total_changes * deletion_weight
        impact_score = weighted_sum / max_weight if max_weight > 0 else 0.0

        return min(impact_score, 1.0)

    def record_full_run(self) -> None:
        """Record that a FULL processing run has been executed."""
        self.last_full_run = datetime.now()
