"""
Index searching functionality for wiki
"""

import os
import re
from typing import List


class IndexSearcher:
    """
    Searches wiki index.md to find relevant pages
    """

    def search(self, keywords: str) -> List[str]:
        """
        Search index for keywords

        Args:
            keywords: Search keywords

        Returns:
            List of page IDs matching the search
        """
        results = []
        index_path = "wiki/index.md"

        if not os.path.exists(index_path):
            return results

        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple keyword matching (will be enhanced with embeddings)
        # Look for links containing keywords in both ID and display text
        pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?'
        matches = re.findall(pattern, content)

        keywords_lower = keywords.lower()
        for page_id, display_text in matches:
            # Search in both page ID and display text
            if keywords_lower in page_id.lower() or (display_text and keywords_lower in display_text.lower()):
                results.append(page_id)

        return results
