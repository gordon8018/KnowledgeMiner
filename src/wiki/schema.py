# src/wiki/schema.py
from pathlib import Path
from typing import Dict, Any, Tuple, List

class SchemaManager:
    """
    Manager for WIKI_SCHEMA.md and metadata validation.

    WIKI_SCHEMA.md defines the structure and validation rules
    for Wiki metadata.
    """

    # Default class-level constants
    DEFAULT_REQUIRED_FIELDS = ["title", "type"]
    DEFAULT_VALID_TYPES = ["topic", "concept", "relation"]

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

        # Instance-level attributes to prevent cross-instance contamination
        self.required_fields = self.DEFAULT_REQUIRED_FIELDS.copy()
        self.valid_types = self.DEFAULT_VALID_TYPES.copy()

        # Create default schema if not exists
        if not self.schema_path.exists():
            self._create_default_schema()

    def _create_default_schema(self):
        """Create default WIKI_SCHEMA.md file."""
        # Build required fields section dynamically
        required_fields_text = "\n".join(
            f"- `{field}` (string): Required field"
            for field in self.required_fields
        )

        # Build optional fields section
        optional_fields = [
            "- `confidence` (float, 0-1): Confidence score for content",
            "- `evidence_count` (int): Number of supporting evidence items",
            "- `last_reviewed` (date): Last review date",
            "- `tags` (list of string): Tags for categorization"
        ]
        optional_fields_text = "\n".join(optional_fields)

        # Build validation rules
        validation_rules = [
            "1. All required fields must be present",
            f"2. Type must be one of: {', '.join(self.valid_types)}",
            "3. Confidence must be between 0 and 1 (if provided)",
            "4. Tags must be a list (if provided)",
            "5. Evidence count must be an integer (if provided)"
        ]
        validation_rules_text = "\n".join(validation_rules)

        schema_content = f"""# WIKI_SCHEMA

This document defines the metadata schema for Wiki pages.

## Required Fields

All Wiki pages must have the following metadata fields:

{required_fields_text}

## Optional Fields

{optional_fields_text}

## Validation Rules

{validation_rules_text}
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
        for field in self.required_fields:
            if field not in metadata:
                errors.append(f"Missing required field: {field}")

        # Validate type
        if "type" in metadata:
            if metadata["type"] not in self.valid_types:
                errors.append(f"Invalid type: {metadata['type']}. Must be one of {self.valid_types}")

        # Validate confidence
        if "confidence" in metadata:
            confidence = metadata["confidence"]
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                errors.append("Confidence must be a number between 0 and 1")

        # Validate tags is a list
        if "tags" in metadata:
            tags = metadata["tags"]
            if not isinstance(tags, list):
                errors.append("Tags must be a list")

        # Validate evidence_count is an integer
        if "evidence_count" in metadata:
            evidence_count = metadata["evidence_count"]
            if not isinstance(evidence_count, int):
                errors.append("Evidence count must be an integer")

        return (len(errors) == 0, errors)

    def update_schema(self, updates: Dict[str, Any]):
        """
        Update schema definition.

        Args:
            updates: Dictionary of schema updates
        """
        # Update required fields
        if "required_fields" in updates:
            self.required_fields = updates["required_fields"]

        # Update valid types
        if "valid_types" in updates:
            self.valid_types = updates["valid_types"]

        # Rebuild schema file with current values
        self._create_default_schema()
