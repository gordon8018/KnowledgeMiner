"""Unit tests for base models."""

import pytest
from datetime import datetime
from src.core.base_models import BaseModel, SourceType, ProcessingStatus


def test_base_model_creation():
    """Test creating a base model with required fields"""
    model = BaseModel(
        id="test-123",
        created_at=datetime.now()
    )
    assert model.id == "test-123"
    assert isinstance(model.created_at, datetime)


def test_base_model_defaults():
    """Test base model with default timestamps"""
    model = BaseModel(id="test-456")
    assert isinstance(model.created_at, datetime)
    assert isinstance(model.updated_at, datetime)


def test_base_model_to_dict():
    """Test converting base model to dictionary"""
    model = BaseModel(id="test-789")
    model_dict = model.to_dict()
    assert isinstance(model_dict, dict)
    assert model_dict["id"] == "test-789"
    assert "created_at" in model_dict
    assert "updated_at" in model_dict


def test_base_model_update_timestamp():
    """Test updating the updated_at timestamp"""
    model = BaseModel(id="test-timestamp")
    original_updated_at = model.updated_at

    # Small delay to ensure timestamp difference
    import time
    time.sleep(0.01)

    model.update_timestamp()

    assert model.updated_at > original_updated_at
    # created_at should remain unchanged
    assert model.created_at == model.created_at


def test_base_model_datetime_serialization():
    """Test datetime serialization to ISO format"""
    from datetime import datetime as dt
    now = dt.now()
    model = BaseModel(id="test-serialization", created_at=now, updated_at=now)

    model_dict = model.to_dict()
    assert isinstance(model_dict["created_at"], str)
    assert isinstance(model_dict["updated_at"], str)

    # Verify ISO format
    parsed_created = dt.fromisoformat(model_dict["created_at"])
    parsed_updated = dt.fromisoformat(model_dict["updated_at"])

    assert parsed_created == now
    assert parsed_updated == now


def test_source_type_enum():
    """Test SourceType enum values"""
    assert SourceType.WEB_CLIPPER.value == "web_clipper"
    assert SourceType.PDF.value == "pdf"
    assert SourceType.MARKDOWN.value == "markdown"
    assert SourceType.TEXT.value == "text"
    assert SourceType.IMAGE.value == "image"


def test_processing_status_enum():
    """Test ProcessingStatus enum values"""
    assert ProcessingStatus.PENDING.value == "pending"
    assert ProcessingStatus.PROCESSING.value == "processing"
    assert ProcessingStatus.PROCESSED.value == "processed"
    assert ProcessingStatus.FAILED.value == "failed"
    assert ProcessingStatus.SKIPPED.value == "skipped"


def test_base_model_with_enum():
    """Test base model can be extended with enum fields"""
    from pydantic import Field

    class TestModel(BaseModel):
        source: SourceType = Field(default=SourceType.PDF)
        status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)

    model = TestModel(id="test-enum")
    assert model.source == SourceType.PDF
    assert model.status == ProcessingStatus.PENDING

    # Test enum serialization
    model_dict = model.to_dict()
    assert model_dict["source"] == "pdf"
    assert model_dict["status"] == "pending"


def test_base_model_validation_error():
    """Test that validation error is raised for invalid data"""
    from pydantic import ValidationError

    # Missing required id field
    with pytest.raises(ValidationError):
        BaseModel()

    # Invalid datetime type
    with pytest.raises(ValidationError):
        BaseModel(id="test", created_at="not-a-datetime")


def test_base_model_immutability_of_id():
    """Test that model id is properly set"""
    model = BaseModel(id="fixed-id")
    assert model.id == "fixed-id"

    # Create a new model with different id
    model2 = BaseModel(id="different-id")
    assert model2.id == "different-id"
    assert model.id == "fixed-id"  # Original unchanged


def test_base_model_copy():
    """Test creating a copy of the model"""
    model = BaseModel(id="original-id")
    model_copy = model.model_copy()

    assert model_copy.id == model.id
    assert model_copy.created_at == model.created_at

    # Update copy shouldn't affect original
    model_copy.update_timestamp()
    assert model_copy.updated_at > model.updated_at
