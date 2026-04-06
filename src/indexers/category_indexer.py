from typing import List, Dict, Set
from src.models.document import Document


class CategoryIndexer:
    """Indexes and categorizes documents by tags and custom categories."""

    # Class-level constant for extension mapping
    EXTENSION_MAPPING = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'cpp': 'cpp',
        'c': 'c',
        'html': 'html',
        'css': 'css',
        'md': 'markdown',
        'yml': 'yaml',
        'yaml': 'yaml',
        'json': 'json',
        'xml': 'xml',
        'sql': 'sql',
        'tf': 'terraform',
        'sh': 'shell',
    }

    TYPE_TO_CATEGORY = {
        'python': 'programming',
        'javascript': 'programming',
        'typescript': 'programming',
        'java': 'programming',
        'cpp': 'programming',
        'c': 'programming',
        'go': 'programming',
        'rust': 'programming',
        'html': 'web',
        'css': 'web',
        'markdown': 'web',
        'yaml': 'config',
        'json': 'config',
        'xml': 'config',
        'dockerfile': 'devops',
        'terraform': 'devops',
        'shell': 'devops',
        'sql': 'database',
        'nosql': 'database',
        'tensorflow': 'ml',
        'pytorch': 'ml',
        'numpy': 'ml',
        'pandas': 'data',
        'matplotlib': 'visualization',
        'seaborn': 'visualization',
        'plotly': 'visualization',
        'pytest': 'testing',
        'unittest': 'testing',
        'jest': 'testing',
        'requirements': 'package',
        'setup': 'package',
        'readme': 'documentation',
        'api': 'documentation',
        'tutorial': 'documentation',
        'guide': 'documentation',
        'changelog': 'documentation'
    }

    def __init__(self):
        """Initialize the CategoryIndexer with an empty category dictionary."""
        self.categories: Dict[str, List[Document]] = {}

    def add_document_to_category(self, document: Document, category: str) -> None:
        """Add a document to a specific category.

        Args:
            document: Document to add
            category: Category name
        """
        if category not in self.categories:
            self.categories[category] = []

        if document not in self.categories[category]:
            self.categories[category].append(document)

    def get_documents_by_category(self, category: str) -> List[Document]:
        """Get all documents in a specific category.

        Args:
            category: Category name

        Returns:
            List of documents in the category
        """
        return self.categories.get(category, [])

    def get_categories(self) -> List[str]:
        """Get all category names.

        Returns:
            List of category names
        """
        return list(self.categories.keys())

    def remove_document_from_category(self, document: Document, category: str) -> bool:
        """Remove a document from a specific category.

        Args:
            document: Document to remove
            category: Category name

        Returns:
            True if document was removed, False if not found in category
        """
        if category not in self.categories:
            return False

        if document in self.categories[category]:
            self.categories[category].remove(document)
            return True

        return False

    def clear_category(self, category: str) -> None:
        """Clear all documents from a category.

        Args:
            category: Category name to clear
        """
        if category in self.categories:
            self.categories[category].clear()

    def clear_all_categories(self) -> None:
        """Clear all categories and their documents."""
        self.categories.clear()

    def get_category_document_count(self, category: str) -> int:
        """Get the number of documents in a category.

        Args:
            category: Category name

        Returns:
            Number of documents in the category
        """
        return len(self.categories.get(category, []))

    def has_category(self, category: str) -> bool:
        """Check if a category exists.

        Args:
            category: Category name to check

        Returns:
            True if category exists, False otherwise
        """
        return category in self.categories

    def auto_categorize_by_tags(self, document: Document) -> None:
        """Auto-categorize a document by its tags.

        Args:
            document: Document to categorize by its tags
        """
        for tag in document.tags:
            self.add_document_to_category(document, tag)

    def get_document_categories(self, document: Document) -> List[str]:
        """Get all categories that contain a specific document.

        Args:
            document: Document to find categories for

        Returns:
            List of category names containing the document
        """
        categories = []
        for category, docs in self.categories.items():
            if document in docs:
                categories.append(category)
        return categories

    def get_most_popular_categories(self, limit: int = 10) -> List[str]:
        """Get the most popular categories by document count.

        Args:
            limit: Maximum number of categories to return

        Returns:
            List of category names sorted by document count (descending)
        """
        sorted_categories = sorted(
            self.categories.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        return [category for category, _ in sorted_categories[:limit]]

    def get_category_from_file_extension(self, file_extension: str) -> str:
        """Get category from file extension using TYPE_TO_CATEGORY mapping.

        Args:
            file_extension: File extension with or without dot (e.g., 'py', '.py')

        Returns:
            Category name for the file extension
        """
        # Normalize extension (remove leading dot if present)
        normalized = file_extension.lstrip('.')
        # Use class-level extension mapping
        mapped_extension = self.EXTENSION_MAPPING.get(normalized, normalized)
        return self.TYPE_TO_CATEGORY.get(mapped_extension, 'unknown')

    def categorize_by_file_extension(self, document: Document) -> str:
        """Categorize a document by its file extension.

        Args:
            document: Document to categorize

        Returns:
            Category name based on file extension
        """
        # Extract file extension from path
        path_parts = document.path.split('.')
        if len(path_parts) > 1:
            extension = path_parts[-1]
            # Use class-level extension mapping
            mapped_extension = self.EXTENSION_MAPPING.get(extension, extension)
            return self.get_category_from_file_extension(mapped_extension)
        return 'unknown'

    def auto_categorize_by_type(self, document: Document) -> None:
        """Auto-categorize a document by its file type.

        Args:
            document: Document to categorize by its file type
        """
        category = self.categorize_by_file_extension(document)
        if category != 'unknown':
            self.add_document_to_category(document, category)

    def get_categories_by_type(self, file_type: str) -> List[str]:
        """Get all documents categorized by a specific file type.

        Args:
            file_type: File type (e.g., 'py', 'js', 'md')

        Returns:
            List of documents in the category corresponding to the file type
        """
        category = self.get_category_from_file_extension(file_type)
        return self.get_documents_by_category(category)

    def get_available_file_types(self) -> List[str]:
        """Get all file types available in the TYPE_TO_CATEGORY mapping.

        Returns:
            List of file extensions that have category mappings
        """
        return list(self.TYPE_TO_CATEGORY.keys())

    def get_category_mapping(self) -> Dict[str, str]:
        """Get the complete TYPE_TO_CATEGORY mapping.

        Returns:
            Dictionary mapping file extensions to categories
        """
        return self.TYPE_TO_CATEGORY.copy()