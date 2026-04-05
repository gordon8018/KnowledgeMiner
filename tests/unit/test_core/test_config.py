"""Unit tests for configuration system."""

import pytest
import os
from pathlib import Path
from src.core.config import Config, get_config


def test_config_loading():
    """Test loading configuration from file"""
    config_path = Path("config/default.yaml")
    config = Config.from_yaml(config_path)
    assert config.llm.provider == "anthropic"
    assert config.llm.model == "claude-sonnet-4-6"


def test_config_environment_override():
    """Test environment variable override"""
    # Set environment variable
    original_key = os.environ.get("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = "test-key-123"

    try:
        config = Config()
        assert config.llm.api_key == "test-key-123"
    finally:
        # Restore original value
        if original_key is not None:
            os.environ["ANTHROPIC_API_KEY"] = original_key
        else:
            os.environ.pop("ANTHROPIC_API_KEY", None)


def test_config_default_values():
    """Test configuration default values"""
    config = Config()
    assert config.llm.provider == "anthropic"
    assert config.llm.model == "claude-sonnet-4-6"
    assert config.storage.raw_dir == "./raw"
    assert config.processing.max_file_size == 10485760
    assert config.quality.min_document_quality == 0.6
    assert config.logging.level == "INFO"


def test_config_to_dict():
    """Test converting configuration to dictionary"""
    config = Config()
    config_dict = config.to_dict()
    assert "llm" in config_dict
    assert "storage" in config_dict
    assert "processing" in config_dict
    assert "quality" in config_dict
    assert "logging" in config_dict
