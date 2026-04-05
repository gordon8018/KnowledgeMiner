"""Configuration management system."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """LLM provider configuration"""

    model_config = SettingsConfigDict(
        env_prefix="KC_LLM_",
        extra="ignore"
    )

    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key_env: str = "ANTHROPIC_API_KEY"
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: int = 60
    max_retries: int = 3

    @property
    def api_key(self) -> str:
        """Get API key from environment"""
        return os.getenv(self.api_key_env, "")


class StorageConfig(BaseSettings):
    """Storage configuration"""

    model_config = SettingsConfigDict(
        env_prefix="KC_STORAGE_",
        extra="ignore"
    )

    raw_dir: str = "./raw"
    wiki_dir: str = "./wiki"
    cache_dir: str = "./cache"
    database_url: str = "sqlite:///./knowledge.db"
    enable_backups: bool = True


class ProcessingConfig(BaseSettings):
    """Processing configuration"""

    model_config = SettingsConfigDict(
        env_prefix="KC_PROCESSING_",
        extra="ignore"
    )

    max_file_size: int = 10485760  # 10MB
    batch_size: int = 10
    parallel_workers: int = 4
    incremental_updates: bool = True
    cache_embeddings: bool = True


class QualityConfig(BaseSettings):
    """Quality threshold configuration"""

    model_config = SettingsConfigDict(
        env_prefix="KC_QUALITY_",
        extra="ignore"
    )

    min_document_quality: float = 0.6
    min_concept_confidence: float = 0.7
    min_relation_confidence: float = 0.6


class LoggingConfig(BaseSettings):
    """Logging configuration"""

    model_config = SettingsConfigDict(
        env_prefix="KC_LOGGING_",
        extra="ignore"
    )

    level: str = "INFO"
    format: str = "structured"
    file: str = "./logs/compiler.log"
    rotation: str = "daily"


class Config:
    """Main configuration class"""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration"""
        if config_dict:
            self.llm = LLMConfig(**config_dict.get("llm", {}))
            self.storage = StorageConfig(**config_dict.get("storage", {}))
            self.processing = ProcessingConfig(**config_dict.get("processing", {}))
            self.quality = QualityConfig(**config_dict.get("quality", {}))
            self.logging = LoggingConfig(**config_dict.get("logging", {}))
        else:
            self.llm = LLMConfig()
            self.storage = StorageConfig()
            self.processing = ProcessingConfig()
            self.quality = QualityConfig()
            self.logging = LoggingConfig()

    @classmethod
    def from_yaml(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file"""
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

        # Handle empty YAML files
        if config_dict is None:
            config_dict = {}

        return cls(config_dict.get("knowledge_compiler", {}))

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "llm": self.llm.model_dump(),
            "storage": self.storage.model_dump(),
            "processing": self.processing.model_dump(),
            "quality": self.quality.model_dump(),
            "logging": self.logging.model_dump(),
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config(config_path: Optional[Path] = None) -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        if config_path and config_path.exists():
            _config = Config.from_yaml(config_path)
        else:
            _config = Config()
    return _config
