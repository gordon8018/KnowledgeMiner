from typing import List, Optional
from src.models.document import Document


class FileIndexer:
    """Indexes and manages documents by file path for quick lookup."""

    def __init__(self):
        """Initialize the FileIndexer with an empty document list."""
        self.documents: List[Document] = []

    def add_document(self, document: Document) -> bool:
        """Add a document to the index.

        Args:
            document: Document to add

        Returns:
            True if document was added, False if it already exists
        """
        if self.has_document(document.path):
            return False

        self.documents.append(document)
        return True

    def get_document_by_path(self, path: str) -> Optional[Document]:
        """Retrieve a document by its path.

        Args:
            path: File path of the document

        Returns:
            Document if found, None otherwise
        """
        for doc in self.documents:
            if doc.path == path:
                return doc
        return None

    def remove_document_by_path(self, path: str) -> Optional[Document]:
        """Remove a document by its path.

        Args:
            path: File path of the document to remove

        Returns:
            Removed document if found, None otherwise
        """
        for i, doc in enumerate(self.documents):
            if doc.path == path:
                return self.documents.pop(i)
        return None

    def get_all_documents(self) -> List[Document]:
        """Get all documents in the index.

        Returns:
            List of all documents
        """
        return self.documents.copy()

    def get_document_count(self) -> int:
        """Get the number of documents in the index.

        Returns:
            Count of documents
        """
        return len(self.documents)

    def clear_index(self) -> None:
        """Clear all documents from the index."""
        self.documents.clear()

    def get_document_paths(self) -> List[str]:
        """Get all document paths in the index.

        Returns:
            List of document paths
        """
        return [doc.path for doc in self.documents]

    def has_document(self, path: str) -> bool:
        """Check if a document exists in the index.

        Args:
            path: File path to check

        Returns:
            True if document exists, False otherwise
        """
        return any(doc.path == path for doc in self.documents)