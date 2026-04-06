"""
Tests for ModeSelector with hybrid mode selection.
"""

import pytest
from datetime import datetime, timedelta
from src.wiki.discovery.mode_selector import ProcessingMode, ModeSelector


class TestModeSelector:
    """Test ModeSelector mode selection logic."""

    def test_select_full_mode_large_changeset(self):
        """Large changeset (>50 docs) should trigger FULL mode."""
        selector = ModeSelector(
            incremental_threshold=10,
            force_full_after_days=7,
            enable_smart_selection=True
        )

        # Create large changeset with 51 documents
        changeset = {
            'added': [f'doc_{i}.md' for i in range(51)],
            'modified': [],
            'deleted': []
        }

        mode = selector.select_mode(changeset)
        assert mode == ProcessingMode.FULL

    def test_select_incremental_mode_small_changeset(self):
        """Small changeset (<threshold) should trigger INCREMENTAL mode."""
        selector = ModeSelector(
            incremental_threshold=10,
            force_full_after_days=7,
            enable_smart_selection=False  # Use simple selection
        )

        # Create small changeset with 5 documents
        changeset = {
            'added': ['doc_1.md', 'doc_2.md'],
            'modified': ['doc_3.md', 'doc_4.md'],
            'deleted': ['doc_5.md']
        }

        mode = selector.select_mode(changeset)
        assert mode == ProcessingMode.INCREMENTAL

    def test_select_hybrid_mode_mixed_changeset(self):
        """Smart selection with heuristics should trigger HYBRID mode."""
        selector = ModeSelector(
            incremental_threshold=10,
            force_full_after_days=7,
            enable_smart_selection=True
        )

        # Create mixed changeset that should trigger HYBRID
        # Between threshold and large size, with moderate impact
        # Need impact score between 0.3 and 0.7
        # 20 additions (weight 0.5) + 15 modifications (weight 1.0) = 25 weighted
        # Total changes = 35, max weight if all deletions = 35 * 2.0 = 70
        # Impact score = 25 / 70 = 0.357 (moderate)
        changeset = {
            'added': [f'doc_{i}.md' for i in range(20)],
            'modified': [f'existing_{i}.md' for i in range(15)],
            'deleted': []  # No deletions
        }

        mode = selector.select_mode(changeset)
        assert mode == ProcessingMode.HYBRID

    def test_force_full_after_timeout(self):
        """Force FULL mode after timeout period has elapsed."""
        # Create selector with last full run 8 days ago
        last_run = datetime.now() - timedelta(days=8)
        selector = ModeSelector(
            incremental_threshold=10,
            force_full_after_days=7,
            enable_smart_selection=True,
            last_full_run=last_run
        )

        # Even small changeset should trigger FULL due to timeout
        changeset = {
            'added': ['doc_1.md'],
            'modified': [],
            'deleted': []
        }

        mode = selector.select_mode(changeset)
        assert mode == ProcessingMode.FULL

    def test_record_full_run(self):
        """record_full_run should update last_full_run timestamp."""
        selector = ModeSelector(
            incremental_threshold=10,
            force_full_after_days=7,
            enable_smart_selection=True,
            last_full_run=None
        )

        assert selector.last_full_run is None

        # Record full run
        selector.record_full_run()

        assert selector.last_full_run is not None
        assert isinstance(selector.last_full_run, datetime)

        # Should be within last second
        time_diff = datetime.now() - selector.last_full_run
        assert time_diff.total_seconds() < 1.0

    def test_should_force_full_never_run(self):
        """Should NOT force full run on first run - let normal selection decide."""
        selector = ModeSelector(
            incremental_threshold=10,
            force_full_after_days=7,
            enable_smart_selection=True,
            last_full_run=None
        )

        # On first run, don't force full - let selection logic decide based on changeset
        assert selector._should_force_full() is False

    def test_simple_selection_at_threshold(self):
        """Simple selection at exact threshold should use INCREMENTAL."""
        selector = ModeSelector(
            incremental_threshold=10,
            force_full_after_days=7,
            enable_smart_selection=False
        )

        # Exactly at threshold
        changeset = {
            'added': [f'doc_{i}.md' for i in range(10)],
            'modified': [],
            'deleted': []
        }

        mode = selector.select_mode(changeset)
        assert mode == ProcessingMode.INCREMENTAL

    def test_smart_selection_with_deletions(self):
        """Smart selection should trigger FULL when deletions present."""
        selector = ModeSelector(
            incremental_threshold=10,
            force_full_after_days=7,
            enable_smart_selection=True
        )

        # Changeset with deletions (above threshold to avoid simple INCREMENTAL)
        changeset = {
            'added': [f'doc_{i}.md' for i in range(11)],  # 11 additions
            'modified': [],
            'deleted': ['old_doc.md']  # Even one deletion triggers FULL
        }

        mode = selector.select_mode(changeset)
        assert mode == ProcessingMode.FULL
