"""
Page reading functionality for wiki
"""

import os
from glob import glob
from typing import List


class PageReader:
    """
    Reads wiki pages from disk
    """

    def read(self, page_id: str) -> str:
        """
        Read a wiki page by ID

        Args:
            page_id: Page identifier (filename without .md)

        Returns:
            Page content as string

        Raises:
            FileNotFoundError: If page not found
        """
        # Search in common locations
        search_paths = [
            f"wiki/entities/{page_id}.md",
            f"wiki/concepts/{page_id}.md",
            f"wiki/sources/{page_id}.md",
            f"wiki/synthesis/{page_id}.md",
            f"wiki/comparisons/{page_id}.md"
        ]

        for path in search_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

        raise FileNotFoundError(f"Page not found: {page_id}")

    def list_all(self) -> List[str]:
        """
        List all wiki pages

        Returns:
            List of page IDs
        """
        patterns = [
            "wiki/entities/*.md",
            "wiki/concepts/*.md",
            "wiki/sources/*.md",
            "wiki/synthesis/*.md",
            "wiki/comparisons/*.md"
        ]

        page_ids = []
        for pattern in patterns:
            files = glob(pattern)
            for file in files:
                # Extract page ID from filename
                page_id = os.path.basename(file).replace(".md", "")
                page_ids.append(page_id)

        return page_ids
