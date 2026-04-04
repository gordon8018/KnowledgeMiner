import pytest
import tempfile
import os
from src.analyzers.hash_calculator import calculate_file_hash, HashManager

def test_calculate_file_hash():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("Test content")
        f.flush()
        temp_path = f.name

    try:
        hash_value = calculate_file_hash(temp_path)
        assert len(hash_value) == 64  # SHA256 produces 64 hex characters
        assert isinstance(hash_value, str)
    finally:
        os.unlink(temp_path)

def test_hash_manager_save_and_load():
    with tempfile.TemporaryDirectory() as temp_dir:
        hash_file = os.path.join(temp_dir, ".hashes.json")
        manager = HashManager(hash_file)

        # Save hashes
        manager.save_hash("test.md", "abc123")
        manager.save_hash("test2.md", "def456")
        manager.save()

        # Load new instance
        manager2 = HashManager(hash_file)
        assert manager2.get_hash("test.md") == "abc123"
        assert manager2.get_hash("test2.md") == "def456"
        assert manager2.get_hash("nonexistent.md") is None

def test_get_changed_files():
    """Test detection of new, modified, and deleted files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        hash_file = os.path.join(temp_dir, ".hashes.json")
        manager = HashManager(hash_file)

        # Initial state
        manager.save_hash("existing.md", "old_hash")
        manager.save()

        # Create new manager and check changes
        manager2 = HashManager(hash_file)
        files = {
            "existing.md": "old_hash",  # unchanged
            "new.md": "new_hash",        # new file
            "modified.md": "different_hash"  # will be marked as modified (old_hash is None)
        }

        # Simulate having old hash for modified.md
        manager2.save_hash("modified.md", "old_hash")

        changes = manager2.get_changed_files(files)

        # Only new.md should be 'new' (no previous hash)
        # existing.md should not be in changes (same hash)
        # modified.md should be 'modified' (hash changed)
        # deleted.md should be 'deleted' (exists in hashes but not in files)

        # Add a deleted file to hashes and re-check
        manager2.save_hash("deleted.md", "deleted_hash")
        changes = manager2.get_changed_files(files)

        assert "new.md" in changes
        assert changes["new.md"] == "new"
        assert "existing.md" not in changes  # unchanged
        assert "deleted.md" in changes
        assert changes["deleted.md"] == "deleted"