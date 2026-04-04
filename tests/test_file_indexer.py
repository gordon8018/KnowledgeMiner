import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from src.models.document import Document
from src.indexers.file_indexer import FileIndexer


class TestFileIndexer:
    def setup_method(self):
        self.indexer = FileIndexer()

    def test_init(self):
        """Test FileIndexer initialization."""
        assert hasattr(self.indexer, 'documents')
        assert isinstance(self.indexer.documents, list)
        assert len(self.indexer.documents) == 0

    def test_add_document(self):
        """Test adding a document to the index."""
        doc = Mock(spec=Document)
        doc.path = "test.md"

        self.indexer.add_document(doc)
        assert len(self.indexer.documents) == 1
        assert self.indexer.documents[0] == doc

    def test_add_duplicate_document(self):
        """Test that duplicate documents are not added."""
        doc = Mock(spec=Document)
        doc.path = "test.md"

        self.indexer.add_document(doc)
        self.indexer.add_document(doc)
        assert len(self.indexer.documents) == 1

    def test_get_document_by_path(self):
        """Test retrieving a document by path."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        self.indexer.add_document(doc)

        result = self.indexer.get_document_by_path("test.md")
        assert result == doc

    def test_get_document_by_path_not_found(self):
        """Test retrieving non-existent document."""
        result = self.indexer.get_document_by_path("nonexistent.md")
        assert result is None

    def test_remove_document_by_path(self):
        """Test removing a document by path."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        self.indexer.add_document(doc)

        result = self.indexer.remove_document_by_path("test.md")
        assert result == doc
        assert len(self.indexer.documents) == 0

    def test_remove_document_by_path_not_found(self):
        """Test removing non-existent document."""
        result = self.indexer.remove_document_by_path("nonexistent.md")
        assert result is None

    def test_get_all_documents(self):
        """Test getting all documents."""
        doc1 = Mock(spec=Document)
        doc1.path = "test1.md"
        doc2 = Mock(spec=Document)
        doc2.path = "test2.md"

        self.indexer.add_document(doc1)
        self.indexer.add_document(doc2)

        result = self.indexer.get_all_documents()
        assert len(result) == 2
        assert doc1 in result
        assert doc2 in result

    def test_get_document_count(self):
        """Test getting document count."""
        assert self.indexer.get_document_count() == 0

        doc = Mock(spec=Document)
        doc.path = "test.md"
        self.indexer.add_document(doc)

        assert self.indexer.get_document_count() == 1

    def test_clear_index(self):
        """Test clearing the index."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        self.indexer.add_document(doc)

        assert len(self.indexer.documents) == 1
        self.indexer.clear_index()
        assert len(self.indexer.documents) == 0

    def test_get_document_paths(self):
        """Test getting all document paths."""
        doc1 = Mock(spec=Document)
        doc1.path = "test1.md"
        doc2 = Mock(spec=Document)
        doc2.path = "test2.md"

        self.indexer.add_document(doc1)
        self.indexer.add_document(doc2)

        result = self.indexer.get_document_paths()
        assert set(result) == {"test1.md", "test2.md"}

    def test_has_document(self):
        """Test checking if document exists."""
        doc = Mock(spec=Document)
        doc.path = "test.md"

        assert not self.indexer.has_document("test.md")
        self.indexer.add_document(doc)
        assert self.indexer.has_document("test.md")