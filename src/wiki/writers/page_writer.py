"""
Wiki page writing functionality
"""

import os
from pathlib import Path
from src.wiki.models import WikiPage


class PageWriter:
    """
    Writes wiki pages to disk as markdown files
    """

    def write(self, page: WikiPage, directory: str) -> str:
        """
        Write a wiki page to disk

        Args:
            page: WikiPage instance
            directory: Directory to write to (e.g., "wiki/concepts/")

        Returns:
            Full path to written file
        """
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)

        # Generate filename
        filename = f"{page.id}.md"
        filepath = os.path.join(directory, filename)

        # Convert to markdown
        markdown_content = page.to_markdown()

        # Write to disk
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return filepath
