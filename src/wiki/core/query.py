"""QueryEngine for Wiki content using Whoosh."""

from typing import List, Optional
from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser, MultifieldParser
from pathlib import Path

from src.wiki.core.storage import WikiStore
from src.wiki.core.models import WikiPage


class QueryEngine:
    """
    Query engine for Wiki content.

    Uses Whoosh for full-text search.
    Integrates with WikiStore for content retrieval.
    """

    def __init__(self, store: WikiStore):
        """
        Initialize QueryEngine.

        Args:
            store: WikiStore instance
        """
        self.store = store
        self.index_dir = store.storage_path / "meta" / "search_index"
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Define schema with title boosting
        self.schema = Schema(
            page_id=ID(stored=True),
            title=TEXT(field_boost=2.0),  # Boost title matches
            content=TEXT
        )

        # Create or open index
        if exists_in(str(self.index_dir)):
            self.index = open_dir(str(self.index_dir))
        else:
            self.index = create_in(str(self.index_dir), self.schema)

        # Build index from existing pages
        self._build_index()

    def _build_index(self):
        """Build search index from all Wiki pages."""
        writer = self.index.writer()

        # Index all topics
        for file_path in self.store.topics_dir.glob("*.md"):
            page_id = file_path.stem
            page = self.store.get_page(page_id)
            if page:
                writer.add_document(
                    page_id=page_id,
                    title=page.title,
                    content=page.content
                )

        # Index all concepts
        for file_path in self.store.concepts_dir.glob("*.md"):
            page_id = file_path.stem
            page = self.store.get_page(page_id)
            if page:
                writer.add_document(
                    page_id=page_id,
                    title=page.title,
                    content=page.content
                )

        writer.commit()

    def search(self, query_str: str, limit: int = 10) -> List[WikiPage]:
        """
        Search Wiki content.

        Args:
            query_str: Search query string
            limit: Maximum number of results

        Returns:
            List of WikiPage objects matching the query
        """
        with self.index.searcher() as searcher:
            # Use MultifieldParser to search both title and content
            # Title has higher boost, so title matches rank higher
            parser = MultifieldParser(
                ["title", "content"],
                self.index.schema,
                fieldboosts={"title": 2.0, "content": 1.0}
            )
            query = parser.parse(query_str)
            results = searcher.search(query, limit=limit)

            pages = []
            for hit in results:
                page = self.store.get_page(hit["page_id"])
                if page:
                    pages.append(page)

            return pages

    def get_page(self, page_id: str) -> Optional[WikiPage]:
        """
        Get a page by ID.

        Args:
            page_id: Page ID to retrieve

        Returns:
            WikiPage if found, None otherwise
        """
        return self.store.get_page(page_id)

    def update_index(self, page: WikiPage):
        """
        Update search index for a page.

        Args:
            page: WikiPage to update in index
        """
        writer = self.index.writer()
        writer.update_document(
            page_id=page.id,
            title=page.title,
            content=page.content
        )
        writer.commit()
