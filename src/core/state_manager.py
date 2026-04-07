"""State Manager for tracking processing state."""

import json
import os
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.core.base_models import ProcessingStatus


class StateManager:
    """Manager for tracking and persisting document processing state.

    Provides thread-safe operations for tracking document processing status,
    supporting incremental processing and state persistence to disk.
    """

    def __init__(self, state_file_path: Optional[str] = None):
        """Initialize the StateManager.

        Args:
            state_file_path: Path to the state file. If None, uses default
                           ./cache/state.json
        """
        if state_file_path is None:
            # Create cache directory if it doesn't exist
            cache_dir = "./cache"
            os.makedirs(cache_dir, exist_ok=True)
            state_file_path = os.path.join(cache_dir, "state.json")

        self.state_file_path = state_file_path

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)

        # Initialize state storage
        self._state: Dict[str, Dict[str, Any]] = {}

        # Thread safety lock
        self._lock = threading.Lock()

        # Try to load existing state
        try:
            self.load()
        except Exception:
            # If load fails, start with empty state
            self._state = {}

    def get_document_state(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get state for a document.

        Args:
            document_id: Unique identifier for the document

        Returns:
            Document state dict or None if not found
        """
        with self._lock:
            return self._state.get(document_id)

    def set_document_state(self, document_id: str, state: Dict[str, Any]) -> None:
        """Set state for a document.

        Args:
            document_id: Unique identifier for the document
            state: State dictionary to set
        """
        with self._lock:
            # Add timestamp if not present
            if "last_updated" not in state:
                state["last_updated"] = datetime.now().isoformat()

            self._state[document_id] = state

    def update_document_status(
        self,
        document_id: str,
        status: ProcessingStatus
    ) -> None:
        """Update document status.

        Args:
            document_id: Unique identifier for the document
            status: New processing status
        """
        with self._lock:
            # Get existing state or create new
            current_state = self._state.get(document_id, {})

            # Update status and timestamp
            current_state["status"] = status
            current_state["last_updated"] = datetime.now().isoformat()

            # Preserve any existing metadata
            if "metadata" not in current_state:
                current_state["metadata"] = {}

            self._state[document_id] = current_state

    def get_all_pending_documents(self) -> List[str]:
        """Get all documents with PENDING status.

        Returns:
            List of document IDs with PENDING status
        """
        with self._lock:
            return [
                doc_id
                for doc_id, state in self._state.items()
                if state.get("status") == ProcessingStatus.PENDING
            ]

    def get_processed_since(self, since: datetime) -> List[str]:
        """Get documents processed since a given timestamp.

        Args:
            since: Timestamp to filter by

        Returns:
            List of document IDs processed after the timestamp
        """
        with self._lock:
            processed_docs = []

            for doc_id, state in self._state.items():
                if state.get("status") != ProcessingStatus.PROCESSED:
                    continue

                last_updated = state.get("last_updated")
                if not last_updated:
                    continue

                try:
                    # Parse the timestamp
                    doc_time = datetime.fromisoformat(last_updated)
                    if doc_time >= since:
                        processed_docs.append(doc_id)
                except (ValueError, TypeError):
                    # Skip documents with invalid timestamps
                    continue

            return processed_docs

    def save(self) -> None:
        """Persist state to disk.

        Raises:
            OSError: If unable to write to state file
            IOError: If unable to write to state file
        """
        with self._lock:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)

            # Write state to file
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, indent=2)

    def load(self) -> None:
        """Load state from disk.

        If the file doesn't exist or is corrupted, initializes empty state.
        """
        with self._lock:
            if not os.path.exists(self.state_file_path):
                self._state = {}
                return

            try:
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not content:
                    self._state = {}
                    return

                self._state = json.loads(content)

            except (json.JSONDecodeError, ValueError):
                # Corrupted file, initialize empty state
                self._state = {}

    def clear(self) -> None:
        """Clear all state and remove state file."""
        with self._lock:
            self._state = {}

            # Remove state file if it exists
            if os.path.exists(self.state_file_path):
                os.remove(self.state_file_path)

    def __enter__(self):
        """Enter context manager (BUGFIX: MEDIUM - add context manager support).

        Returns:
            Self for context manager usage
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager with automatic save (BUGFIX: MEDIUM).

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised

        Returns:
            False to indicate exceptions should not be suppressed
        """
        # Save state on exit (even if an exception occurred)
        try:
            self.save()
        except Exception:
            # Don't raise exceptions during cleanup
            pass

        return False  # Don't suppress exceptions

