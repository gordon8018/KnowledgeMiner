# tests/test_core/test_schema.py
import pytest
import tempfile
import shutil
from src.wiki.schema import SchemaManager


@pytest.fixture
def schema_manager():
    """Create a SchemaManager for testing."""
    temp_dir = tempfile.mkdtemp()
    manager = SchemaManager(storage_path=temp_dir)
    yield manager
    shutil.rmtree(temp_dir)


def test_schema_manager_initialization(schema_manager):
    """Test schema manager initialization."""
    assert schema_manager.schema_path.exists()
    assert schema_manager.schema_path.name == "WIKI_SCHEMA.md"


def test_validate_metadata(schema_manager):
    """Test metadata validation with valid data."""
    valid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "confidence": 0.9
    }

    is_valid, errors = schema_manager.validate_metadata(valid_metadata)
    assert is_valid
    assert len(errors) == 0


def test_validate_metadata_missing_field(schema_manager):
    """Test metadata validation with missing required field."""
    invalid_metadata = {
        "type": "topic"
        # Missing "title"
    }

    is_valid, errors = schema_manager.validate_metadata(invalid_metadata)
    assert not is_valid
    assert "title" in str(errors).lower()


def test_validate_metadata_invalid_type(schema_manager):
    """Test metadata validation with invalid type."""
    invalid_metadata = {
        "title": "Test Page",
        "type": "invalid_type"
    }

    is_valid, errors = schema_manager.validate_metadata(invalid_metadata)
    assert not is_valid
    assert "invalid type" in str(errors).lower()


def test_validate_metadata_invalid_confidence_negative(schema_manager):
    """Test metadata validation with negative confidence."""
    invalid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "confidence": -0.5
    }

    is_valid, errors = schema_manager.validate_metadata(invalid_metadata)
    assert not is_valid
    assert "confidence" in str(errors).lower()


def test_validate_metadata_invalid_confidence_high(schema_manager):
    """Test metadata validation with confidence > 1."""
    invalid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "confidence": 1.5
    }

    is_valid, errors = schema_manager.validate_metadata(invalid_metadata)
    assert not is_valid
    assert "confidence" in str(errors).lower()


def test_validate_metadata_invalid_tags_not_list(schema_manager):
    """Test metadata validation with tags as string instead of list."""
    invalid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "tags": "single_tag"  # Should be a list
    }

    is_valid, errors = schema_manager.validate_metadata(invalid_metadata)
    assert not is_valid
    assert "tags must be a list" in str(errors).lower()


def test_validate_metadata_valid_tags_list(schema_manager):
    """Test metadata validation with valid tags list."""
    valid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "tags": ["tag1", "tag2", "tag3"]
    }

    is_valid, errors = schema_manager.validate_metadata(valid_metadata)
    assert is_valid
    assert len(errors) == 0


def test_validate_metadata_invalid_evidence_count_not_int(schema_manager):
    """Test metadata validation with evidence_count as string."""
    invalid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "evidence_count": "five"  # Should be an integer
    }

    is_valid, errors = schema_manager.validate_metadata(invalid_metadata)
    assert not is_valid
    assert "evidence count must be an integer" in str(errors).lower()


def test_validate_metadata_valid_evidence_count(schema_manager):
    """Test metadata validation with valid evidence_count."""
    valid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "evidence_count": 5
    }

    is_valid, errors = schema_manager.validate_metadata(valid_metadata)
    assert is_valid
    assert len(errors) == 0


def test_validate_metadata_multiple_errors(schema_manager):
    """Test metadata validation with multiple errors simultaneously."""
    invalid_metadata = {
        "type": "invalid_type",
        "confidence": 2.5,
        "tags": "not_a_list",
        "evidence_count": "ten"
        # Missing "title"
    }

    is_valid, errors = schema_manager.validate_metadata(invalid_metadata)
    assert not is_valid
    assert len(errors) == 5  # title, type, confidence, tags, evidence_count


def test_validate_metadata_both_required_fields_missing(schema_manager):
    """Test metadata validation with both required fields missing."""
    invalid_metadata = {
        "confidence": 0.5
        # Missing both "title" and "type"
    }

    is_valid, errors = schema_manager.validate_metadata(invalid_metadata)
    assert not is_valid
    assert len(errors) == 2
    assert any("title" in error for error in errors)
    assert any("type" in error for error in errors)


def test_update_schema_required_fields(schema_manager):
    """Test updating schema required fields."""
    new_required_fields = ["title", "type", "category"]
    schema_manager.update_schema({"required_fields": new_required_fields})

    # Check that the instance attribute was updated
    assert schema_manager.required_fields == new_required_fields

    # Check that validation uses new required fields
    valid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "category": "test"
    }
    is_valid, errors = schema_manager.validate_metadata(valid_metadata)
    assert is_valid
    assert len(errors) == 0

    # Check that old metadata (without category) now fails
    old_metadata = {
        "title": "Test Page",
        "type": "topic"
    }
    is_valid, errors = schema_manager.validate_metadata(old_metadata)
    assert not is_valid
    assert "category" in str(errors).lower()


def test_update_schema_valid_types(schema_manager):
    """Test updating schema valid types."""
    new_valid_types = ["topic", "concept", "relation", "article"]
    schema_manager.update_schema({"valid_types": new_valid_types})

    # Check that the instance attribute was updated
    assert schema_manager.valid_types == new_valid_types

    # Check that validation accepts new type
    valid_metadata = {
        "title": "Test Page",
        "type": "article"
    }
    is_valid, errors = schema_manager.validate_metadata(valid_metadata)
    assert is_valid
    assert len(errors) == 0


def test_update_schema_regenerates_documentation(schema_manager):
    """Test that updating schema regenerates WIKI_SCHEMA.md with current values."""
    # Update schema
    new_required_fields = ["title", "type", "author"]
    new_valid_types = ["topic", "concept", "article"]
    schema_manager.update_schema({
        "required_fields": new_required_fields,
        "valid_types": new_valid_types
    })

    # Read the regenerated schema file
    schema_content = schema_manager.schema_path.read_text()

    # Check that it contains the new values
    assert "author" in schema_content
    assert "article" in schema_content
    assert "relation" not in schema_content  # Old type should be gone


def test_instance_isolation():
    """Test that multiple SchemaManager instances don't share state."""
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    try:
        manager1 = SchemaManager(storage_path=temp_dir1)
        manager2 = SchemaManager(storage_path=temp_dir2)

        # Update manager1
        manager1.update_schema({"required_fields": ["title", "type", "custom"]})

        # Check that manager2 is not affected
        assert manager2.required_fields == SchemaManager.DEFAULT_REQUIRED_FIELDS
        assert "custom" not in manager2.required_fields
        assert manager1.required_fields != manager2.required_fields

    finally:
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)


def test_validate_metadata_boundary_confidence_values(schema_manager):
    """Test metadata validation with boundary confidence values (0 and 1)."""
    # Test confidence = 0 (valid)
    metadata_zero = {
        "title": "Test Page",
        "type": "topic",
        "confidence": 0
    }
    is_valid, errors = schema_manager.validate_metadata(metadata_zero)
    assert is_valid
    assert len(errors) == 0

    # Test confidence = 1 (valid)
    metadata_one = {
        "title": "Test Page",
        "type": "topic",
        "confidence": 1
    }
    is_valid, errors = schema_manager.validate_metadata(metadata_one)
    assert is_valid
    assert len(errors) == 0


def test_validate_metadata_all_optional_fields(schema_manager):
    """Test metadata validation with all optional fields present and valid."""
    valid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "confidence": 0.85,
        "evidence_count": 10,
        "tags": ["ai", "machine-learning", "nlp"],
        "last_reviewed": "2026-04-06"
    }

    is_valid, errors = schema_manager.validate_metadata(valid_metadata)
    assert is_valid
    assert len(errors) == 0

