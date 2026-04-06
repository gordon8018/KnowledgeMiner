# src/wiki/schema.py
from pathlib import Path
from typing import Dict, Any, Tuple, List

class SchemaManager:
    """
    Manager for WIKI_SCHEMA.md and metadata validation.

    WIKI_SCHEMA.md defines the structure and validation rules
    for Wiki metadata.
    """

    REQUIRED_FIELDS = ["title", "type"]
    VALID_TYPES = ["topic", "concept", "relation"]

    def __init__(self, storage_path: str):
        """
        Initialize SchemaManager.

        Args:
            storage_path: Path to wiki storage directory
        """
        self.storage_path = Path(storage_path)
        self.schema_dir = self.storage_path / "schema"
        self.schema_dir.mkdir(parents=True, exist_ok=True)
        self.schema_path = self.schema_dir / "WIKI_SCHEMA.md"

        # Create default schema if not exists
        if not self.schema_path.exists():
            self._create_default_schema()

    def _create_default_schema(self):
        """Create default WIKI_SCHEMA.md file."""
        schema_content = """# WIKI_SCHEMA

This document defines the metadata schema for Wiki pages.

## Required Fields

All Wiki pages must have the following metadata fields:

- `title` (string): Page title
- `type` (string): One of "topic", "concept", or "relation"

## Optional Fields

- `confidence` (float, 0-1): Confidence score for content
- `evidence_count` (int): Number of supporting evidence items
- `last_reviewed` (date): Last review date
- `tags` (list of string): Tags for categorization

## Validation Rules

1. All required fields must be present
2. Type must be one of the valid types
3. Confidence must be between 0 and 1 (if provided)
4. Tags must be a list (if provided)
"""
        self.schema_path.write_text(schema_content)

    def validate_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate page metadata against schema.

        Args:
            metadata: Metadata dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in metadata:
                errors.append(f"Missing required field: {field}")

        # Validate type
        if "type" in metadata:
            if metadata["type"] not in self.VALID_TYPES:
                errors.append(f"Invalid type: {metadata['type']}. Must be one of {self.VALID_TYPES}")

        # Validate confidence
        if "confidence" in metadata:
            confidence = metadata["confidence"]
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                errors.append("Confidence must be a number between 0 and 1")

        return (len(errors) == 0, errors)

    def update_schema(self, updates: Dict[str, Any]):
        """
        Update schema definition.

        Args:
            updates: Dictionary of schema updates
        """
        # Update required fields
        if "required_fields" in updates:
            self.REQUIRED_FIELDS = updates["required_fields"]

        # Update valid types
        if "valid_types" in updates:
            self.VALID_TYPES = updates["valid_types"]

        # Rebuild schema file
        self._create_default_schema()
