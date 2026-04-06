"""
Tests for InputProcessor and change detection functionality.
"""
import os
import json
import tempfile
import shutil
import threading
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from src.wiki.discovery.input import InputProcessor
from src.wiki.discovery.models import ChangeSet


class TestChangeSetModel:
    """Test the ChangeSet model."""

    def test_changeset_creation(self):
        """Test creating a ChangeSet."""
        changeset = ChangeSet(
            batch_id="test-batch-001",
            new_docs=["doc1", "doc2"],
            changed_docs=["doc3"],
            deleted_docs=["doc4"],
            impact_score=0.8
        )

        assert len(changeset.new_docs) == 2
        assert len(changeset.changed_docs) == 1
        assert len(changeset.deleted_docs) == 1
        assert changeset.batch_id == "test-batch-001"
        assert changeset.impact_score == 0.8
        assert isinstance(changeset.timestamp, datetime)

    def test_total_changes_property(self):
        """Test total_changes property."""
        changeset = ChangeSet(
            batch_id="test-001",
            new_docs=["a", "b"],
            changed_docs=["c"],
            deleted_docs=["d"]
        )

        assert changeset.total_changes == 4

    def test_is_empty(self):
        """Test is_empty method."""
        # Non-empty changeset
        changeset = ChangeSet(
            batch_id="test-001",
            new_docs=["a"]
        )
        assert not changeset.is_empty()

        # Empty changeset
        empty_changeset = ChangeSet(batch_id="test-002")
        assert empty_changeset.is_empty()

    def test_impact_score_validation(self):
        """Test impact score validation."""
        # Valid scores
        ChangeSet(batch_id="test-001", impact_score=0.0)
        ChangeSet(batch_id="test-002", impact_score=1.0)
        ChangeSet(batch_id="test-003", impact_score=0.5)

        # Invalid scores
        with pytest.raises(ValueError):
            ChangeSet(batch_id="test-004", impact_score=-0.1)

        with pytest.raises(ValueError):
            ChangeSet(batch_id="test-005", impact_score=1.1)


class TestInputProcessor:
    """Test the InputProcessor class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def state_file(self, temp_dir):
        """Create a state file path."""
        return os.path.join(temp_dir, "state.json")

    @pytest.fixture
    def input_dir(self, temp_dir):
        """Create an input directory."""
        input_dir = os.path.join(temp_dir, "input")
        os.makedirs(input_dir)
        return input_dir

    @pytest.fixture
    def processor(self, input_dir, state_file):
        """Create an InputProcessor instance."""
        return InputProcessor(input_dir=input_dir, state_file=state_file)

    def test_detect_new_documents(self, processor, input_dir):
        """Test detecting new documents."""
        # Create initial state (empty)
        processor._save_state({})

        # Add new documents
        doc1 = os.path.join(input_dir, "doc1.md")
        doc2 = os.path.join(input_dir, "doc2.md")

        Path(doc1).write_text("# Document 1\nContent 1")
        Path(doc2).write_text("# Document 2\nContent 2")

        # Process changes
        changeset = processor.process_changes(batch_id="test-001")

        # Verify new documents detected
        assert len(changeset.new_docs) == 2
        assert "doc1.md" in changeset.new_docs
        assert "doc2.md" in changeset.new_docs
        assert len(changeset.changed_docs) == 0
        assert len(changeset.deleted_docs) == 0

    def test_detect_changed_documents(self, processor, input_dir):
        """Test detecting changed documents."""
        # Create initial documents
        doc1 = os.path.join(input_dir, "doc1.md")
        doc2 = os.path.join(input_dir, "doc2.md")

        Path(doc1).write_text("# Document 1\nOriginal content")
        Path(doc2).write_text("# Document 2\nStatic content")

        # Process initial state
        processor.process_changes(batch_id="test-001")

        # Modify doc1
        time.sleep(0.01)  # Ensure different timestamp
        Path(doc1).write_text("# Document 1\nModified content")

        # Process changes
        changeset = processor.process_changes(batch_id="test-002")

        # Verify changes detected
        assert len(changeset.changed_docs) == 1
        assert "doc1.md" in changeset.changed_docs
        assert len(changeset.new_docs) == 0

    def test_detect_deleted_documents(self, processor, input_dir):
        """Test detecting deleted documents."""
        # Create initial documents
        doc1 = os.path.join(input_dir, "doc1.md")
        doc2 = os.path.join(input_dir, "doc2.md")

        Path(doc1).write_text("# Document 1")
        Path(doc2).write_text("# Document 2")

        # Process initial state
        processor.process_changes(batch_id="test-001")

        # Delete doc1
        os.remove(doc1)

        # Process changes
        changeset = processor.process_changes(batch_id="test-002")

        # Verify deletion detected
        assert len(changeset.deleted_docs) == 1
        assert "doc1.md" in changeset.deleted_docs
        assert len(changeset.new_docs) == 0
        assert len(changeset.changed_docs) == 0

    def test_atomic_state_updates(self, processor, input_dir):
        """Test that state updates are atomic (write to temp, then rename)."""
        # Create a document
        doc1 = os.path.join(input_dir, "doc1.md")
        Path(doc1).write_text("# Document 1")

        # Mock os.replace to track calls (we use os.replace for atomic rename)
        original_replace = os.replace
        replace_calls = []

        def mock_replace(src, dst):
            replace_calls.append((src, dst))
            return original_replace(src, dst)

        with patch('os.replace', side_effect=mock_replace):
            processor.process_changes(batch_id="test-001")

        # Verify replace was called (temp file -> actual file)
        assert len(replace_calls) >= 1
        # Check that temp file was renamed to actual state file
        temp_src, final_dst = replace_calls[-1]
        assert final_dst == processor.state_file
        assert "temp" in temp_src or "tmp" in temp_src

    def test_concurrent_access_safety(self, processor, input_dir):
        """Test concurrent access safety with threading."""
        # Create documents
        for i in range(5):
            doc_path = os.path.join(input_dir, f"doc{i}.md")
            Path(doc_path).write_text(f"# Document {i}")

        # Track results
        results = []
        errors = []

        def process_batch(batch_num):
            try:
                changeset = processor.process_changes(batch_id=f"batch-{batch_num}")
                results.append((batch_num, changeset.total_changes))
            except Exception as e:
                errors.append((batch_num, e))

        # Run concurrent operations
        threads = []
        for i in range(10):
            t = threading.Thread(target=process_batch, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent access errors: {errors}"

        # Verify state file is consistent
        state = processor._load_state()
        assert state is not None
        assert "documents" in state

    def test_corrupted_state_recovery(self, processor, input_dir):
        """Test automatic recovery from corrupted state file."""
        # Create corrupted state file
        with open(processor.state_file, 'w') as f:
            f.write("{{ invalid json content")

        # Add documents
        doc1 = os.path.join(input_dir, "doc1.md")
        Path(doc1).write_text("# Document 1")

        # Should recover and process successfully
        changeset = processor.process_changes(batch_id="test-001")

        # Verify recovery worked
        assert changeset is not None
        assert len(changeset.new_docs) >= 1
        assert "doc1.md" in changeset.new_docs

        # Verify state file is now valid
        state = processor._load_state()
        assert state is not None
        assert "documents" in state

    def test_impact_score_calculation(self, processor, input_dir):
        """Test impact score calculation."""
        # Initial state
        processor._save_state({})

        # Create varying numbers of changes
        test_cases = [
            (5, 0.05),    # 5 changes -> 0.05 impact
            (25, 0.25),   # 25 changes -> 0.25 impact
            (50, 0.5),    # 50 changes -> 0.5 impact
            (100, 1.0),   # 100+ changes -> 1.0 impact
            (150, 1.0),   # Cap at 1.0
        ]

        for num_docs, expected_min_impact in test_cases:
            # Clear input dir
            for f in os.listdir(input_dir):
                os.remove(os.path.join(input_dir, f))

            # Create documents
            for i in range(num_docs):
                doc_path = os.path.join(input_dir, f"doc_{i}.md")
                Path(doc_path).write_text(f"# Document {i}")

            # Process changes
            changeset = processor.process_changes(batch_id=f"batch-{num_docs}")

            # Verify impact score
            assert changeset.impact_score >= expected_min_impact - 0.01, \
                f"Expected impact >= {expected_min_impact} for {num_docs} changes, got {changeset.impact_score}"
            assert changeset.impact_score <= 1.0

            # Reset state for next test
            processor._save_state({})

    def test_empty_directory(self, processor, input_dir):
        """Test processing an empty directory."""
        changeset = processor.process_changes(batch_id="test-empty")

        assert changeset.is_empty()
        assert changeset.total_changes == 0

    def test_missing_state_file(self, processor, input_dir):
        """Test processing when state file doesn't exist."""
        # Ensure state file doesn't exist
        if os.path.exists(processor.state_file):
            os.remove(processor.state_file)

        # Add documents
        doc1 = os.path.join(input_dir, "doc1.md")
        Path(doc1).write_text("# Document 1")

        # Should create new state file
        changeset = processor.process_changes(batch_id="test-001")

        assert changeset is not None
        assert os.path.exists(processor.state_file)

    def test_nested_directories(self, processor, input_dir):
        """Test handling of nested directories."""
        # Create nested structure
        nested_dir = os.path.join(input_dir, "subdir", "nested")
        os.makedirs(nested_dir, exist_ok=True)

        # Create documents at different levels
        Path(os.path.join(input_dir, "root.md")).write_text("Root doc")
        Path(os.path.join(input_dir, "subdir", "level1.md")).write_text("Level 1 doc")
        Path(os.path.join(nested_dir, "level2.md")).write_text("Level 2 doc")

        # Process changes
        changeset = processor.process_changes(batch_id="test-nested")

        # Should detect all documents
        assert changeset.total_changes == 3

    def test_non_markdown_files(self, processor, input_dir):
        """Test that only markdown files are processed."""
        # Create various file types
        Path(os.path.join(input_dir, "doc1.md")).write_text("# Markdown doc")
        Path(os.path.join(input_dir, "doc2.txt")).write_text("Text file")
        Path(os.path.join(input_dir, "doc3.pdf")).write_text("PDF file")
        Path(os.path.join(input_dir, "doc4.MD")).write_text("# Uppercase MD")

        # Process changes
        changeset = processor.process_changes(batch_id="test-filetypes")

        # Should only process .md files (case-insensitive)
        assert changeset.total_changes == 2
        assert "doc1.md" in changeset.new_docs
        assert "doc4.MD" in changeset.new_docs
