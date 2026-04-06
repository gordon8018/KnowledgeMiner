"""Unit tests for StateManager."""

import pytest
import json
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from src.core.state_manager import StateManager
from src.core.base_models import ProcessingStatus


@pytest.fixture
def temp_state_file():
    """Create a temporary state file for testing."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def state_manager(temp_state_file):
    """Create a StateManager instance with a temporary state file."""
    manager = StateManager(state_file_path=temp_state_file)
    yield manager
    # Cleanup is handled by temp_state_file fixture


class TestStateManagerInitialization:
    """Test StateManager initialization and basic setup."""

    def test_initialization_with_path(self, temp_state_file):
        """Test creating StateManager with a specific file path."""
        manager = StateManager(state_file_path=temp_state_file)
        assert manager.state_file_path == temp_state_file
        assert manager._state == {}
        assert isinstance(manager._lock, type(threading.Lock()))

    def test_initialization_with_default_path(self):
        """Test creating StateManager with default path."""
        # Save original directory
        original_dir = os.getcwd()
        tmpdir = tempfile.mkdtemp()

        try:
            os.chdir(tmpdir)
            default_path = os.path.join(tmpdir, 'cache', 'state.json')

            manager = StateManager()
            # Default should use ./cache/state.json
            assert 'state.json' in manager.state_file_path
        finally:
            os.chdir(original_dir)
            # Cleanup
            import shutil
            try:
                shutil.rmtree(tmpdir, ignore_errors=True)
            except:
                pass

    def test_initialization_creates_directory(self):
        """Test that initialization creates cache directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, 'cache', 'state.json')
            manager = StateManager(state_file_path=state_file)

            # Directory should be created
            assert os.path.exists(os.path.dirname(state_file))

    def test_load_empty_state(self, state_manager):
        """Test loading from non-existent state file."""
        # Should initialize with empty state
        assert state_manager._state == {}
        assert len(state_manager._state) == 0

    def test_load_existing_state(self, temp_state_file):
        """Test loading from existing state file."""
        # Create a state file
        test_state = {
            "doc1": {
                "status": "processed",
                "last_updated": "2024-01-01T12:00:00",
                "metadata": {"test": "data"}
            }
        }
        with open(temp_state_file, 'w') as f:
            json.dump(test_state, f)

        # Load the state
        manager = StateManager(state_file_path=temp_state_file)
        assert "doc1" in manager._state
        assert manager._state["doc1"]["status"] == "processed"


class TestDocumentStateOperations:
    """Test document state operations."""

    def test_get_document_state_not_exists(self, state_manager):
        """Test getting state for non-existent document."""
        result = state_manager.get_document_state("nonexistent")
        assert result is None

    def test_get_document_state_exists(self, state_manager):
        """Test getting state for existing document."""
        state_manager._state["doc1"] = {
            "status": "processed",
            "last_updated": "2024-01-01T12:00:00"
        }

        result = state_manager.get_document_state("doc1")
        assert result is not None
        assert result["status"] == "processed"

    def test_set_document_state(self, state_manager):
        """Test setting document state."""
        state_data = {
            "status": "processing",
            "last_updated": "2024-01-01T12:00:00",
            "metadata": {"key": "value"}
        }

        state_manager.set_document_state("doc1", state_data)

        result = state_manager.get_document_state("doc1")
        assert result["status"] == "processing"
        assert result["metadata"]["key"] == "value"

    def test_set_document_state_overwrites(self, state_manager):
        """Test that set_document_state overwrites existing state."""
        # Set initial state
        state_manager.set_document_state("doc1", {"status": "pending"})

        # Overwrite with new state
        new_state = {
            "status": "processed",
            "last_updated": "2024-01-01T12:00:00"
        }
        state_manager.set_document_state("doc1", new_state)

        result = state_manager.get_document_state("doc1")
        assert result["status"] == "processed"

    def test_update_document_status(self, state_manager):
        """Test updating document status."""
        # Set initial state
        state_manager.set_document_state("doc1", {
            "status": ProcessingStatus.PENDING,
            "last_updated": "2024-01-01T12:00:00"
        })

        # Update status
        state_manager.update_document_status("doc1", ProcessingStatus.PROCESSED)

        result = state_manager.get_document_state("doc1")
        assert result["status"] == ProcessingStatus.PROCESSED
        # last_updated should be updated
        assert result["last_updated"] != "2024-01-01T12:00:00"

    def test_update_document_status_new_document(self, state_manager):
        """Test updating status for a new document."""
        state_manager.update_document_status("doc1", ProcessingStatus.PROCESSING)

        result = state_manager.get_document_state("doc1")
        assert result["status"] == ProcessingStatus.PROCESSING
        assert "last_updated" in result

    def test_update_document_status_with_metadata(self, state_manager):
        """Test updating status preserves existing metadata."""
        # Set initial state with metadata
        state_manager.set_document_state("doc1", {
            "status": ProcessingStatus.PENDING,
            "metadata": {"key": "value", "count": 42}
        })

        # Update status
        state_manager.update_document_status("doc1", ProcessingStatus.PROCESSED)

        result = state_manager.get_document_state("doc1")
        assert result["status"] == ProcessingStatus.PROCESSED
        assert result["metadata"]["key"] == "value"
        assert result["metadata"]["count"] == 42


class TestQueryOperations:
    """Test query operations for retrieving documents."""

    def test_get_all_pending_documents_empty(self, state_manager):
        """Test getting pending documents when state is empty."""
        pending = state_manager.get_all_pending_documents()
        assert pending == []

    def test_get_all_pending_documents(self, state_manager):
        """Test getting all pending documents."""
        # Add documents with different statuses
        state_manager.update_document_status("doc1", ProcessingStatus.PENDING)
        state_manager.update_document_status("doc2", ProcessingStatus.PROCESSED)
        state_manager.update_document_status("doc3", ProcessingStatus.PENDING)
        state_manager.update_document_status("doc4", ProcessingStatus.FAILED)

        pending = state_manager.get_all_pending_documents()
        assert len(pending) == 2
        assert "doc1" in pending
        assert "doc3" in pending

    def test_get_processed_since_empty(self, state_manager):
        """Test getting processed documents when state is empty."""
        cutoff = datetime.now()
        processed = state_manager.get_processed_since(cutoff)
        assert processed == []

    def test_get_processed_since(self, state_manager):
        """Test getting documents processed since a timestamp."""
        now = datetime.now()

        # Add documents with different timestamps
        old_time = now - timedelta(days=1)
        recent_time = now - timedelta(minutes=5)

        state_manager.set_document_state("old_doc", {
            "status": ProcessingStatus.PROCESSED,
            "last_updated": old_time.isoformat()
        })
        state_manager.set_document_state("recent_doc1", {
            "status": ProcessingStatus.PROCESSED,
            "last_updated": recent_time.isoformat()
        })
        state_manager.set_document_state("recent_doc2", {
            "status": ProcessingStatus.PROCESSED,
            "last_updated": (now - timedelta(minutes=1)).isoformat()
        })

        # Get documents processed in the last hour
        cutoff = now - timedelta(hours=1)
        processed = state_manager.get_processed_since(cutoff)

        assert len(processed) == 2
        assert "recent_doc1" in processed
        assert "recent_doc2" in processed
        assert "old_doc" not in processed

    def test_get_processed_since_only_processed(self, state_manager):
        """Test that get_processed_since only returns PROCESSED documents."""
        now = datetime.now()
        recent_time = now - timedelta(minutes=5)

        # Add documents with different statuses
        state_manager.set_document_state("processed_doc", {
            "status": ProcessingStatus.PROCESSED,
            "last_updated": recent_time.isoformat()
        })
        state_manager.set_document_state("pending_doc", {
            "status": ProcessingStatus.PENDING,
            "last_updated": recent_time.isoformat()
        })
        state_manager.set_document_state("failed_doc", {
            "status": ProcessingStatus.FAILED,
            "last_updated": recent_time.isoformat()
        })

        cutoff = now - timedelta(hours=1)
        processed = state_manager.get_processed_since(cutoff)

        assert len(processed) == 1
        assert "processed_doc" in processed


class TestPersistenceOperations:
    """Test state persistence to disk."""

    def test_save_creates_file(self, state_manager, temp_state_file):
        """Test that save creates state file."""
        state_manager.set_document_state("doc1", {
            "status": ProcessingStatus.PROCESSED
        })
        state_manager.save()

        assert os.path.exists(temp_state_file)

    def test_save_persists_state(self, state_manager, temp_state_file):
        """Test that save persists state to disk."""
        state_manager.set_document_state("doc1", {
            "status": ProcessingStatus.PROCESSED,
            "metadata": {"key": "value"}
        })
        state_manager.save()

        # Read file and verify
        with open(temp_state_file, 'r') as f:
            saved_state = json.load(f)

        assert "doc1" in saved_state
        assert saved_state["doc1"]["status"] == "processed"
        assert saved_state["doc1"]["metadata"]["key"] == "value"

    def test_load_retrieves_state(self, state_manager, temp_state_file):
        """Test that load retrieves state from disk."""
        # Create state file manually
        test_state = {
            "doc1": {
                "status": "processed",
                "last_updated": "2024-01-01T12:00:00"
            }
        }
        with open(temp_state_file, 'w') as f:
            json.dump(test_state, f)

        # Load state
        state_manager.load()

        assert "doc1" in state_manager._state
        assert state_manager._state["doc1"]["status"] == "processed"

    def test_save_and_load_cycle(self, state_manager, temp_state_file):
        """Test complete save and load cycle."""
        # Set up state
        state_manager.set_document_state("doc1", {
            "status": ProcessingStatus.PROCESSED,
            "metadata": {"count": 42}
        })
        state_manager.save()

        # Create new manager and load
        new_manager = StateManager(state_file_path=temp_state_file)
        new_manager.load()

        result = new_manager.get_document_state("doc1")
        assert result["status"] == ProcessingStatus.PROCESSED
        assert result["metadata"]["count"] == 42

    def test_clear(self, state_manager, temp_state_file):
        """Test clearing all state."""
        # Add some state
        state_manager.set_document_state("doc1", {"status": "processed"})
        state_manager.set_document_state("doc2", {"status": "pending"})

        # Clear
        state_manager.clear()

        assert len(state_manager._state) == 0

    def test_clear_deletes_state_file(self, state_manager, temp_state_file):
        """Test that clear removes state file."""
        # Save some state
        state_manager.set_document_state("doc1", {"status": "processed"})
        state_manager.save()

        # Clear
        state_manager.clear()

        # File should be deleted
        assert not os.path.exists(temp_state_file)


class TestErrorHandling:
    """Test error handling for various edge cases."""

    def test_load_from_corrupt_file(self, state_manager, temp_state_file):
        """Test loading from corrupt JSON file."""
        # Write invalid JSON
        with open(temp_state_file, 'w') as f:
            f.write("{ invalid json }")

        # Should handle gracefully and initialize empty state
        state_manager.load()
        assert state_manager._state == {}

    def test_load_from_empty_file(self, state_manager, temp_state_file):
        """Test loading from empty file."""
        # Create empty file
        with open(temp_state_file, 'w') as f:
            f.write("")

        # Should handle gracefully
        state_manager.load()
        assert state_manager._state == {}

    def test_save_with_invalid_path(self):
        """Test saving to invalid path."""
        # On Windows, use a path with invalid characters
        # On Unix, use a path in a location we can't access
        if os.name == 'nt':  # Windows
            # Use invalid characters for Windows filenames
            # This will fail during initialization
            invalid_path = "C:\\invalid<>path|?*:\\state.json"
            with pytest.raises((OSError, IOError)):
                manager = StateManager(state_file_path=invalid_path)
        else:  # Unix/Linux/Mac
            # Use root directory which we likely can't write to
            # This will fail during save
            invalid_path = "/state.json"
            manager = StateManager(state_file_path=invalid_path)
            manager.set_document_state("doc1", {"status": "processed"})
            with pytest.raises((OSError, IOError)):
                manager.save()

    def test_get_document_state_with_invalid_structure(self, state_manager):
        """Test getting document with invalid state structure."""
        # Set state with missing required fields
        state_manager._state["doc1"] = {"status": "processed"}

        # Should still return what's available
        result = state_manager.get_document_state("doc1")
        assert result["status"] == "processed"


class TestThreadSafety:
    """Test thread safety of StateManager operations."""

    def test_concurrent_set_document_state(self, state_manager):
        """Test concurrent set_document_state operations."""
        num_threads = 10
        documents_per_thread = 100
        threads = []
        errors = []

        def set_documents(thread_id):
            try:
                for i in range(documents_per_thread):
                    doc_id = f"doc_thread{thread_id}_item{i}"
                    state_manager.set_document_state(doc_id, {
                        "status": "processed",
                        "thread_id": thread_id
                    })
            except Exception as e:
                errors.append(e)

        # Create and start threads
        for i in range(num_threads):
            t = threading.Thread(target=set_documents, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check for errors
        assert len(errors) == 0

        # Verify all documents were added
        expected_count = num_threads * documents_per_thread
        assert len(state_manager._state) == expected_count

    def test_concurrent_update_status(self, state_manager):
        """Test concurrent update_document_status operations."""
        num_threads = 10
        threads = []
        errors = []

        # Initialize documents
        for i in range(100):
            state_manager.update_document_status(f"doc{i}", ProcessingStatus.PENDING)

        def update_status(thread_id):
            try:
                for i in range(100):
                    doc_id = f"doc{i}"
                    # Each thread updates status
                    state_manager.update_document_status(doc_id, ProcessingStatus.PROCESSING)
            except Exception as e:
                errors.append(e)

        # Create and start threads
        for i in range(num_threads):
            t = threading.Thread(target=update_status, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check for errors
        assert len(errors) == 0

        # Verify all documents have final status
        for i in range(100):
            doc_id = f"doc{i}"
            result = state_manager.get_document_state(doc_id)
            assert result["status"] == ProcessingStatus.PROCESSING

    def test_concurrent_save_and_load(self, state_manager, temp_state_file):
        """Test concurrent save and load operations."""
        num_threads = 5
        threads = []
        errors = []

        # Initialize some state
        for i in range(10):
            state_manager.update_document_status(f"doc{i}", ProcessingStatus.PROCESSED)

        def save_load_cycle(thread_id):
            try:
                for _ in range(10):
                    # Modify state
                    state_manager.update_document_status(
                        f"doc{thread_id}",
                        ProcessingStatus.PROCESSING
                    )
                    # Save
                    state_manager.save()
                    # Small delay
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Create and start threads
        for i in range(num_threads):
            t = threading.Thread(target=save_load_cycle, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check for errors
        assert len(errors) == 0

        # Final state should be consistent
        state_manager.load()
        assert len(state_manager._state) >= 10

    def test_concurrent_query_operations(self, state_manager):
        """Test concurrent query operations."""
        num_threads = 10
        threads = []
        errors = []
        results = []

        # Initialize state
        for i in range(50):
            state_manager.update_document_status(f"doc{i}", ProcessingStatus.PROCESSED)

        def query_documents():
            try:
                for _ in range(100):
                    pending = state_manager.get_all_pending_documents()
                    results.append(len(pending))
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Create and start threads
        for i in range(num_threads):
            t = threading.Thread(target=query_documents)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check for errors
        assert len(errors) == 0

        # All queries should return consistent results
        assert all(r == 0 for r in results)


class TestIncrementalProcessing:
    """Test incremental processing support."""

    def test_track_processing_progress(self, state_manager):
        """Test tracking progress of document processing."""
        # Start processing
        state_manager.update_document_status("doc1", ProcessingStatus.PENDING)
        assert state_manager.get_document_state("doc1")["status"] == ProcessingStatus.PENDING

        # Mark as processing
        state_manager.update_document_status("doc1", ProcessingStatus.PROCESSING)
        assert state_manager.get_document_state("doc1")["status"] == ProcessingStatus.PROCESSING

        # Mark as processed
        state_manager.update_document_status("doc1", ProcessingStatus.PROCESSED)
        assert state_manager.get_document_state("doc1")["status"] == ProcessingStatus.PROCESSED

    def test_filter_unprocessed_documents(self, state_manager):
        """Test filtering documents that need processing."""
        # Add mixed documents
        state_manager.update_document_status("doc1", ProcessingStatus.PROCESSED)
        state_manager.update_document_status("doc2", ProcessingStatus.PENDING)
        state_manager.update_document_status("doc3", ProcessingStatus.FAILED)
        state_manager.update_document_status("doc4", ProcessingStatus.PROCESSED)

        pending = state_manager.get_all_pending_documents()
        assert len(pending) == 1
        assert "doc2" in pending

    def test_resume_after_failure(self, state_manager):
        """Test resuming processing after failure."""
        # Mark some as failed
        state_manager.update_document_status("doc1", ProcessingStatus.FAILED)
        state_manager.update_document_status("doc2", ProcessingStatus.PROCESSED)

        # Get failed documents
        failed = [
            doc_id for doc_id, state in state_manager._state.items()
            if state.get("status") == ProcessingStatus.FAILED
        ]

        assert "doc1" in failed
        assert "doc2" not in failed

        # Can retry failed documents
        state_manager.update_document_status("doc1", ProcessingStatus.PENDING)
        assert state_manager.get_document_state("doc1")["status"] == ProcessingStatus.PENDING
