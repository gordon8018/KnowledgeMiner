"""
Input processor for detecting document changes.

Scans input directory for markdown files, tracks state using MD5 hashes,
and detects new, changed, and deleted documents with atomic state updates
and concurrent access safety.
"""
import os
import json
import hashlib
import tempfile
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from filelock import FileLock

from src.wiki.discovery.models import ChangeSet


logger = logging.getLogger(__name__)


class InputProcessor:
    """
    Detects changes in input documents using MD5 hashing.

    Features:
    - Atomic state file updates (write to temp, then rename)
    - Concurrent access safety (file locking)
    - Automatic cleanup of corrupted state files
    - Impact score calculation (0-1 scale)
    """

    # Class constant for impact score normalization
    MAX_IMPACT_CHANGES = 100

    def __init__(self, input_dir: str, state_file: str):
        """
        Initialize InputProcessor.

        Args:
            input_dir: Directory containing markdown documents
            state_file: Path to state file for tracking changes
        """
        self.input_dir = Path(input_dir)
        self.state_file = state_file
        self.lock_file = f"{state_file}.lock"

        # Ensure input directory exists
        self.input_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"InputProcessor initialized: input_dir={input_dir}, state_file={state_file}")

    def process_changes(self, batch_id: str) -> ChangeSet:
        """
        Process input directory and detect changes.

        Args:
            batch_id: Unique identifier for this batch

        Returns:
            ChangeSet with detected changes
        """
        logger.info(f"Processing changes for batch: {batch_id}")

        # Acquire lock for concurrent access safety
        with FileLock(self.lock_file, timeout=10):
            # Load current state (handle corrupted files)
            state = self._load_state()

            # Scan current documents
            current_docs = self._scan_documents()

            # Detect changes
            new_docs, changed_docs, deleted_docs = self._detect_changes(
                state.get("documents", {}), current_docs
            )

            # Calculate impact score
            impact_score = self._calculate_impact_score(
                len(new_docs), len(changed_docs), len(deleted_docs)
            )

            # Update state
            new_state = {
                "documents": current_docs,
                "last_scan": datetime.now().isoformat()
            }
            self._save_state(new_state)

            # Create changeset
            changeset = ChangeSet(
                batch_id=batch_id,
                new_docs=new_docs,
                changed_docs=changed_docs,
                deleted_docs=deleted_docs,
                impact_score=impact_score
            )

            logger.info(
                f"Changes detected: {len(new_docs)} new, "
                f"{len(changed_docs)} changed, {len(deleted_docs)} deleted, "
                f"impact={impact_score:.2f}"
            )

            return changeset

    def _scan_documents(self) -> Dict[str, Dict]:
        """
        Scan input directory for markdown documents.

        Returns:
            Dictionary mapping document IDs to their metadata
        """
        documents = {}

        for root, dirs, files in os.walk(self.input_dir):
            for filename in files:
                # Only process markdown files (case-insensitive)
                if not filename.lower().endswith('.md'):
                    continue

                file_path = os.path.join(root, filename)

                # Calculate document ID (relative path from input_dir)
                rel_path = os.path.relpath(file_path, self.input_dir)
                doc_id = rel_path.replace('\\', '/')

                # Calculate MD5 hash
                file_hash = self._calculate_hash(file_path)

                # Store metadata
                documents[doc_id] = {
                    "hash": file_hash,
                    "path": file_path,
                    "last_seen": datetime.now().isoformat()
                }

        logger.debug(f"Scanned {len(documents)} documents")
        return documents

    def _calculate_hash(self, file_path: str) -> Optional[str]:
        """
        Calculate MD5 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            MD5 hash as hexadecimal string, or None if file cannot be read
        """
        md5_hash = hashlib.md5()

        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

        return md5_hash.hexdigest()

    def _detect_changes(
        self,
        old_docs: Dict[str, Dict],
        new_docs: Dict[str, Dict]
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Detect new, changed, and deleted documents.

        Args:
            old_docs: Previous state documents
            new_docs: Current scan documents

        Returns:
            Tuple of (new_doc_ids, changed_doc_ids, deleted_doc_ids)
        """
        old_ids = set(old_docs.keys())
        new_ids = set(new_docs.keys())

        # New documents: in new but not in old
        new_doc_ids = list(new_ids - old_ids)

        # Deleted documents: in old but not in new
        deleted_doc_ids = list(old_ids - new_ids)

        # Changed documents: in both but hash differs
        common_ids = old_ids & new_ids
        changed_doc_ids = [
            doc_id for doc_id in common_ids
            if old_docs[doc_id]["hash"] != new_docs[doc_id]["hash"]
        ]

        logger.debug(
            f"Changes: {len(new_doc_ids)} new, "
            f"{len(changed_doc_ids)} changed, "
            f"{len(deleted_doc_ids)} deleted"
        )

        return new_doc_ids, changed_doc_ids, deleted_doc_ids

    def _calculate_impact_score(
        self,
        new_count: int,
        changed_count: int,
        deleted_count: int
    ) -> float:
        """
        Calculate impact score based on number of changes.

        Normalizes total changes to 0-1 scale (max 100 changes = 1.0).

        Args:
            new_count: Number of new documents
            changed_count: Number of changed documents
            deleted_count: Number of deleted documents

        Returns:
            Impact score between 0.0 and 1.0
        """
        total_changes = new_count + changed_count + deleted_count

        # Normalize: MAX_IMPACT_CHANGES changes = 1.0 impact
        impact = min(total_changes / self.MAX_IMPACT_CHANGES, 1.0)

        logger.debug(f"Impact score: {impact:.2f} (based on {total_changes} changes)")
        return impact

    def _load_state(self) -> Dict:
        """
        Load state from file with automatic recovery from corruption.

        Returns:
            State dictionary, or empty dict if file doesn't exist
        """
        if not os.path.exists(self.state_file):
            logger.debug("State file does not exist, starting fresh")
            return {}

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            logger.debug("State loaded successfully")
            return state

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Corrupted state file detected: {e}. Recovering...")

            # Backup corrupted file
            backup_file = f"{self.state_file}.corrupted.{int(datetime.now().timestamp())}"
            try:
                shutil.copy(self.state_file, backup_file)
                logger.info(f"Backed up corrupted state to: {backup_file}")
            except Exception as backup_error:
                logger.error(f"Failed to backup corrupted state: {backup_error}")

            # Return empty state to recover
            return {}

    def _save_state(self, state: Dict) -> None:
        """
        Save state to file atomically (write to temp, then rename).

        Args:
            state: State dictionary to save
        """
        # Create temporary file in same directory as target
        temp_fd, temp_path = tempfile.mkstemp(
            prefix=os.path.basename(self.state_file),
            dir=os.path.dirname(self.state_file)
        )

        try:
            # Write to temp file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            # Atomic rename (overwrites existing file)
            os.replace(temp_path, self.state_file)

            logger.debug("State saved atomically")

        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except Exception:
                pass

            logger.error(f"Error saving state: {e}")
            raise
