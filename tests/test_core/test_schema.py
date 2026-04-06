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
    """Test metadata validation."""
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
