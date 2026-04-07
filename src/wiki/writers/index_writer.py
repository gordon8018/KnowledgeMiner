"""
Index writing functionality for wiki
"""

import os
from src.wiki.models import WikiIndex


class IndexWriter:
    """
    Writes wiki index to disk
    """

    def update(self, index: WikiIndex, filepath: str = "wiki/index.md") -> str:
        """
        Update wiki index file

        Args:
            index: WikiIndex instance
            filepath: Path to index file (default: wiki/index.md)

        Returns:
            Full path to written file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Convert to markdown
        markdown_content = index.to_markdown()

        # Write to disk
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return filepath
