"""
Discovery configuration with environment variable support.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DiscoveryConfig(BaseSettings):
    """Knowledge discovery engine configuration."""

    model_config = SettingsConfigDict(
        env_prefix="KC_DISCOVERY_",
        extra="ignore"
    )

    # Relation mining settings
    enable_explicit_mining: bool = True
    enable_implicit_mining: bool = True
    enable_statistical_mining: bool = True
    enable_semantic_mining: bool = True
    min_relation_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    max_relations_per_concept: int = Field(default=50, ge=1)

    # Pattern detection settings
    enable_temporal_detection: bool = True
    enable_causal_detection: bool = True
    enable_evolutionary_detection: bool = True
    enable_conflict_detection: bool = True
    min_pattern_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Gap analysis settings
    enable_concept_gap_analysis: bool = True
    enable_relation_gap_analysis: bool = True
    enable_evidence_analysis: bool = True
    min_evidence_confidence: float = Field(default=0.4, ge=0.0, le=1.0)

    # Insight generation settings
    max_insights: int = Field(default=100, ge=1)
    insight_significance_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    enable_actionable_suggestions: bool = True

    # Performance settings
    batch_size: int = Field(default=10, ge=1)
    parallel_workers: int = Field(default=2, ge=1)
    cache_intermediate_results: bool = True
