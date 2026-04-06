import pytest
from unittest.mock import Mock, patch
from src.models.document import Document
from src.models.concept import Concept
from src.indexers.category_indexer import CategoryIndexer


class TestCategoryIndexer:
    def setup_method(self):
        self.indexer = CategoryIndexer()

    def test_init(self):
        """Test CategoryIndexer initialization."""
        assert hasattr(self.indexer, 'categories')
        assert isinstance(self.indexer.categories, dict)
        assert len(self.indexer.categories) == 0

    def test_add_document_to_category(self):
        """Test adding a document to a category."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.tags = ["machine-learning", "ai"]
        doc.title = "Test Document"

        self.indexer.add_document_to_category(doc, "tutorial")
        assert "tutorial" in self.indexer.categories
        assert len(self.indexer.categories["tutorial"]) == 1
        assert doc in self.indexer.categories["tutorial"]

    def test_add_document_to_multiple_categories(self):
        """Test adding a document to multiple categories."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.tags = ["python", "beginner"]
        doc.title = "Python Tutorial"

        self.indexer.add_document_to_category(doc, "python")
        self.indexer.add_document_to_category(doc, "beginner")
        self.indexer.add_document_to_category(doc, "tutorial")

        assert len(self.indexer.categories["python"]) == 1
        assert len(self.indexer.categories["beginner"]) == 1
        assert len(self.indexer.categories["tutorial"]) == 1

    def test_add_document_to_existing_category(self):
        """Test adding multiple documents to same category."""
        doc1 = Mock(spec=Document)
        doc1.path = "test1.md"
        doc1.tags = ["python"]
        doc1.title = "Python Basics"

        doc2 = Mock(spec=Document)
        doc2.path = "test2.md"
        doc2.tags = ["python", "advanced"]
        doc2.title = "Python Advanced"

        self.indexer.add_document_to_category(doc1, "python")
        self.indexer.add_document_to_category(doc2, "python")

        assert len(self.indexer.categories["python"]) == 2
        assert doc1 in self.indexer.categories["python"]
        assert doc2 in self.indexer.categories["python"]

    def test_get_documents_by_category(self):
        """Test getting documents by category."""
        doc1 = Mock(spec=Document)
        doc1.path = "test1.md"
        doc1.tags = ["python"]
        doc1.title = "Python Basics"

        doc2 = Mock(spec=Document)
        doc2.path = "test2.md"
        doc2.tags = ["python", "advanced"]
        doc2.title = "Python Advanced"

        self.indexer.add_document_to_category(doc1, "python")
        self.indexer.add_document_to_category(doc2, "python")

        result = self.indexer.get_documents_by_category("python")
        assert len(result) == 2
        assert doc1 in result
        assert doc2 in result

    def test_get_documents_by_nonexistent_category(self):
        """Test getting documents from non-existent category."""
        result = self.indexer.get_documents_by_category("nonexistent")
        assert result == []

    def test_get_categories(self):
        """Test getting all categories."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.tags = ["python"]
        doc.title = "Python Tutorial"

        self.indexer.add_document_to_category(doc, "python")
        self.indexer.add_document_to_category(doc, "tutorial")

        result = self.indexer.get_categories()
        assert set(result) == {"python", "tutorial"}

    def test_remove_document_from_category(self):
        """Test removing a document from a category."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.tags = ["python"]
        doc.title = "Python Tutorial"

        self.indexer.add_document_to_category(doc, "python")
        result = self.indexer.remove_document_from_category(doc, "python")

        assert result == True
        assert len(self.indexer.categories["python"]) == 0

    def test_remove_document_from_nonexistent_category(self):
        """Test removing document from non-existent category."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.title = "Test"

        result = self.indexer.remove_document_from_category(doc, "nonexistent")
        assert result == False

    def test_remove_document_from_category_where_not_present(self):
        """Test removing document from category where it's not present."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.title = "Test"

        self.indexer.add_document_to_category(doc, "python")
        result = self.indexer.remove_document_from_category(doc, "other")

        assert result == False
        assert len(self.indexer.categories["python"]) == 1

    def test_clear_category(self):
        """Test clearing a category."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.tags = ["python"]
        doc.title = "Python Tutorial"

        self.indexer.add_document_to_category(doc, "python")
        self.indexer.add_document_to_category(doc, "tutorial")

        self.indexer.clear_category("python")
        assert len(self.indexer.categories["python"]) == 0
        assert len(self.indexer.categories["tutorial"]) == 1

    def test_clear_nonexistent_category(self):
        """Test clearing non-existent category."""
        self.indexer.clear_category("nonexistent")
        assert "nonexistent" not in self.indexer.categories

    def test_clear_all_categories(self):
        """Test clearing all categories."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.tags = ["python"]
        doc.title = "Python Tutorial"

        self.indexer.add_document_to_category(doc, "python")
        self.indexer.add_document_to_category(doc, "tutorial")

        self.indexer.clear_all_categories()
        assert len(self.indexer.categories) == 0

    def test_get_category_document_count(self):
        """Test getting document count for a category."""
        doc1 = Mock(spec=Document)
        doc1.path = "test1.md"
        doc1.tags = ["python"]
        doc1.title = "Python Basics"

        doc2 = Mock(spec=Document)
        doc2.path = "test2.md"
        doc2.tags = ["python", "advanced"]
        doc2.title = "Python Advanced"

        self.indexer.add_document_to_category(doc1, "python")
        self.indexer.add_document_to_category(doc2, "python")

        assert self.indexer.get_category_document_count("python") == 2

    def test_get_category_document_count_nonexistent(self):
        """Test getting document count for non-existent category."""
        assert self.indexer.get_category_document_count("nonexistent") == 0

    def test_has_category(self):
        """Test checking if category exists."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.tags = ["python"]
        doc.title = "Python Tutorial"

        assert not self.indexer.has_category("python")
        self.indexer.add_document_to_category(doc, "python")
        assert self.indexer.has_category("python")

    def test_auto_categorize_by_tags(self):
        """Test auto-categorizing documents by their tags."""
        doc1 = Mock(spec=Document)
        doc1.path = "test1.md"
        doc1.tags = ["python", "tutorial"]
        doc1.title = "Python Basics"

        doc2 = Mock(spec=Document)
        doc2.path = "test2.md"
        doc2.tags = ["python", "advanced"]
        doc2.title = "Python Advanced"

        self.indexer.auto_categorize_by_tags(doc1)
        self.indexer.auto_categorize_by_tags(doc2)

        assert len(self.indexer.categories["python"]) == 2
        assert len(self.indexer.categories["tutorial"]) == 1
        assert len(self.indexer.categories["advanced"]) == 1

    def test_auto_categorize_empty_tags(self):
        """Test auto-categorizing document with no tags."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.tags = []
        doc.title = "No Tags"

        self.indexer.auto_categorize_by_tags(doc)
        assert len(self.indexer.categories) == 0

    def test_get_category_from_file_extension(self):
        """Test getting category from file extension."""
        assert self.indexer.get_category_from_file_extension("python") == "programming"
        assert self.indexer.get_category_from_file_extension(".js") == "programming"
        assert self.indexer.get_category_from_file_extension("markdown") == "web"
        assert self.indexer.get_category_from_file_extension("dockerfile") == "devops"
        assert self.indexer.get_category_from_file_extension("unknown") == "unknown"

    def test_categorize_by_file_extension(self):
        """Test categorizing document by file extension."""
        doc = Mock(spec=Document)
        doc.path = "script.py"
        doc.title = "Python Script"

        category = self.indexer.categorize_by_file_extension(doc)
        assert category == "programming"

        doc2 = Mock(spec=Document)
        doc2.path = "README.md"
        doc2.title = "Readme"

        category2 = self.indexer.categorize_by_file_extension(doc2)
        assert category2 == "web"

        # Test with explicit extension match
        doc3 = Mock(spec=Document)
        doc3.path = "file.python"
        doc3.title = "Python File"

        category3 = self.indexer.categorize_by_file_extension(doc3)
        assert category3 == "programming"

    def test_categorize_by_file_extension_no_extension(self):
        """Test categorizing document without file extension."""
        doc = Mock(spec=Document)
        doc.path = "README"
        doc.title = "No Extension"

        category = self.indexer.categorize_by_file_extension(doc)
        assert category == "unknown"

    def test_auto_categorize_by_type(self):
        """Test auto-categorizing by file type."""
        doc = Mock(spec=Document)
        doc.path = "script.py"
        doc.title = "Python Script"

        self.indexer.auto_categorize_by_type(doc)
        assert len(self.indexer.categories["programming"]) == 1
        assert doc in self.indexer.categories["programming"]

    def test_get_categories_by_type(self):
        """Test getting documents by file type."""
        doc1 = Mock(spec=Document)
        doc1.path = "script.py"
        doc1.title = "Python Script"

        doc2 = Mock(spec=Document)
        doc2.path = "main.js"
        doc2.title = "JavaScript Main"

        self.indexer.auto_categorize_by_type(doc1)
        self.indexer.auto_categorize_by_type(doc2)

        # Both should be categorized under 'programming'
        programming_docs = self.indexer.get_categories_by_type("python")
        assert len(programming_docs) == 2  # Both py and js files go to programming
        assert doc1 in programming_docs
        assert doc2 in programming_docs

        # JavaScript files also map to programming category
        js_docs = self.indexer.get_categories_by_type("javascript")
        assert len(js_docs) == 2  # Both py and js files go to programming
        assert doc1 in js_docs
        assert doc2 in js_docs

        # Test with a different category
        doc3 = Mock(spec=Document)
        doc3.path = "README.md"
        doc3.title = "Readme"
        self.indexer.auto_categorize_by_type(doc3)

        markdown_docs = self.indexer.get_categories_by_type("markdown")
        assert len(markdown_docs) == 1
        assert doc3 in markdown_docs

    def test_get_available_file_types(self):
        """Test getting available file types."""
        file_types = self.indexer.get_available_file_types()
        assert "python" in file_types
        assert "javascript" in file_types
        assert "markdown" in file_types
        assert "dockerfile" in file_types
        assert "unknown" not in file_types  # Should not be in available types

    def test_get_category_mapping(self):
        """Test getting the category mapping."""
        mapping = self.indexer.get_category_mapping()
        assert isinstance(mapping, dict)
        assert mapping["python"] == "programming"
        assert mapping["markdown"] == "web"
        assert mapping["dockerfile"] == "devops"
        assert len(mapping) > 0

    def test_combined_categorization(self):
        """Test combining tag-based and type-based categorization."""
        doc = Mock(spec=Document)
        doc.path = "tutorial.py"
        doc.tags = ["tutorial", "beginner"]
        doc.title = "Python Tutorial"

        # Tag-based categorization
        self.indexer.auto_categorize_by_tags(doc)
        # Type-based categorization
        self.indexer.auto_categorize_by_type(doc)

        # Should have categories from both tags and file type
        assert "tutorial" in self.indexer.categories
        assert "beginner" in self.indexer.categories
        assert "programming" in self.indexer.categories

        # Document should be in all three categories
        assert doc in self.indexer.categories["tutorial"]
        assert doc in self.indexer.categories["beginner"]
        assert doc in self.indexer.categories["programming"]