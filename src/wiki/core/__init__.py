"""WikiCore - Core components for Wiki storage and management."""

from src.wiki.core.models import WikiPage, WikiVersion, WikiUpdate, PageType, UpdateType
from src.wiki.core.storage import WikiStore
from src.wiki.core.graph import KnowledgeGraph
from src.wiki.core.query import QueryEngine


class WikiCore:
    """
    Facade for Wiki core functionality.

    Provides a unified interface to storage, graph, and query operations.
    """

    def __init__(self, storage_path: str):
        """
        Initialize WikiCore.

        Args:
            storage_path: Path to wiki storage directory
        """
        self.store = WikiStore(storage_path)
        self.graph = KnowledgeGraph()
        self.query = QueryEngine(self.store)

    def create_page(self, page: WikiPage) -> WikiPage:
        """Create a new Wiki page."""
        created = self.store.create_page(page)
        self.query.update_index(created)
        return created

    def get_page(self, page_id: str):
        """Get a page by ID."""
        return self.store.get_page(page_id)

    def update_page(self, page: WikiPage) -> WikiPage:
        """Update an existing Wiki page."""
        updated = self.store.update_page(page)
        self.query.update_index(updated)
        return updated

    def search(self, query_str: str, limit: int = 10):
        """Search Wiki content."""
        return self.query.search(query_str, limit)

    def add_relation(self, relation):
        """Add a relation to the knowledge graph."""
        self.graph.add_relations([relation])

    def get_related_concepts(self, concept: str):
        """Get concepts related to the given concept."""
        return self.graph.get_related_concepts(concept)

    def find_shortest_path(self, source: str, target: str):
        """Find shortest path between two concepts."""
        return self.graph.find_shortest_path(source, target)


__all__ = [
    "WikiCore",
    "WikiPage",
    "WikiVersion",
    "WikiUpdate",
    "PageType",
    "UpdateType",
    "WikiStore",
]
