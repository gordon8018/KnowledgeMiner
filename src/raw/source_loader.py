"""
Source loading functionality for Raw Sources layer
"""

import os
from pathlib import Path
from typing import Optional


class SourceLoadError(Exception):
    """Raised when source fails to load"""
    pass


class RawSource:
    """Represents a raw source document"""
    def __init__(self, content: str, path: str):
        self.content = content
        self.path = path
        self.filename = os.path.basename(path)


class SourceLoader:
    """
    Loads raw source documents from disk

    Raw sources are immutable - they are never modified by the system
    """

    def load(self, path: str) -> RawSource:
        """
        Load a raw source from disk

        Args:
            path: Path to the source file

        Returns:
            RawSource instance

        Raises:
            SourceLoadError: If file cannot be loaded
        """
        if not os.path.exists(path):
            raise SourceLoadError(f"File not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            return RawSource(content=content, path=path)

        except Exception as e:
            raise SourceLoadError(f"Failed to load {path}: {e}")
