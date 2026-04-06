import hashlib
import json
import os
from typing import Dict, Optional
from datetime import datetime

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

class HashManager:
    def __init__(self, hash_file: str):
        self.hash_file = hash_file
        self.hashes: Dict[str, str] = {}
        self._load()

    def _load(self):
        """Load hashes from file."""
        if os.path.exists(self.hash_file):
            with open(self.hash_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.hashes = {k: v for k, v in data.items() if not k.startswith('_')}

    def save(self):
        """Save hashes to file."""
        data = {
            **self.hashes,
            "_metadata": {
                "lastUpdate": datetime.now().isoformat(),
                "totalFiles": len(self.hashes)
            }
        }
        with open(self.hash_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_hash(self, file_path: str, hash_value: str):
        """Save or update a file hash."""
        self.hashes[file_path] = hash_value

    def get_hash(self, file_path: str) -> Optional[str]:
        """Get hash for a file."""
        return self.hashes.get(file_path)

    def get_changed_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """
        Get files that have changed.
        Returns dict of {file_path: 'new'|'modified'|'deleted'}
        """
        changed = {}
        current_files = set(files.keys())

        for file_path in current_files:
            old_hash = self.get_hash(file_path)
            new_hash = files[file_path]
            if old_hash != new_hash:
                changed[file_path] = 'new' if old_hash is None else 'modified'

        # Check for deleted files
        for file_path in self.hashes.keys():
            if file_path not in current_files and not file_path.startswith('_'):
                changed[file_path] = 'deleted'

        return changed