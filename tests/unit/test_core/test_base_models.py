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


def test_source_type_enum():
    """Test SourceType enum values"""
    assert SourceType.WEB_CLIPPER.value == "web_clipper"
    assert SourceType.PDF.value == "pdf"
    assert SourceType.MARKDOWN.value == "markdown"


def test_processing_status_enum():
    """Test ProcessingStatus enum values"""
    assert ProcessingStatus.PENDING.value == "pending"
    assert ProcessingStatus.PROCESSED.value == "processed"
    assert ProcessingStatus.FAILED.value == "failed"
