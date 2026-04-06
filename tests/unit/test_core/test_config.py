"""Unit tests for configuration system."""

import pytest
import os
import tempfile
from pathlib import Path
from src.core.config import Config, get_config


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    config_content = """
knowledge_compiler:
  llm:
    provider: anthropic
    model: claude-sonnet-4-6
    temperature: 0.3
  storage:
    raw_dir: ./raw
    wiki_dir: ./wiki
  processing:
    max_file_size: 10485760
    batch_size: 10
  quality:
    min_document_quality: 0.6
  logging:
    level: INFO
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def malformed_config_file():
    """Create a malformed YAML file for error testing"""
    config_content = """
knowledge_compiler:
  llm:
    provider: anthropic
  model: [invalid yaml syntax
    # This is malformed - unclosed bracket
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def empty_config_file():
    """Create an empty config file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_config_loading(temp_config_file):
    """Test loading configuration from file"""
    config = Config.from_yaml(temp_config_file)
    assert config.llm.provider == "anthropic"
    assert config.llm.model == "claude-sonnet-4-6"
    assert config.llm.temperature == 0.3


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


def test_config_missing_environment_variable():
    """Test config when required environment variable is missing"""
    # Ensure the environment variable is not set
    original_key = os.environ.get("ANTHROPIC_API_KEY")
    os.environ.pop("ANTHROPIC_API_KEY", None)

    try:
        config = Config()
        # Should return empty string when env var is missing
        assert config.llm.api_key == ""
    finally:
        # Restore original value
        if original_key is not None:
            os.environ["ANTHROPIC_API_KEY"] = original_key


def test_config_from_yaml_file_not_found():
    """Test loading config from non-existent file"""
    nonexistent_path = Path("/nonexistent/path/config.yaml")
    with pytest.raises(FileNotFoundError):
        Config.from_yaml(nonexistent_path)


def test_config_from_yaml_malformed(malformed_config_file):
    """Test loading config from malformed YAML file"""
    import yaml
    with pytest.raises(yaml.YAMLError):
        Config.from_yaml(malformed_config_file)


def test_config_from_empty_yaml(empty_config_file):
    """Test loading config from empty YAML file"""
    # Should not raise error, should use defaults
    config = Config.from_yaml(empty_config_file)
    assert config.llm.provider == "anthropic"  # Default value


def test_get_config_singleton():
    """Test that get_config returns singleton instance"""
    # Clear any existing config
    import src.core.config
    src.core.config._config = None

    config1 = get_config()
    config2 = get_config()
    assert config1 is config2


def test_get_config_with_path(temp_config_file):
    """Test get_config with a config file path"""
    # Clear any existing config
    import src.core.config
    src.core.config._config = None

    config = get_config(temp_config_file)
    assert config.llm.provider == "anthropic"
    assert config.llm.model == "claude-sonnet-4-6"
