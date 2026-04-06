"""
Configuration validation for Knowledge Compiler.

Provides comprehensive configuration validation with:
- Schema validation
- Type checking
- Range validation
- Dependency validation
- Clear error messages
- Profile testing
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class ValidationError:
    """Configuration validation error."""
    field: str
    message: str
    severity: str  # "error", "warning"
    value: Any = None


@dataclass
class ValidationResult:
    """Configuration validation result."""
    valid: bool
    errors: List[ValidationError] = None
    warnings: List[ValidationError] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ConfigValidator:
    """
    Validate Knowledge Compiler configuration.

    Features:
    - Schema validation
    - Type checking
    - Range validation
    - Path validation
    - Dependency validation
    - Clear error messages
    - Configuration profiles
    """

    def __init__(self):
        """Initialize ConfigValidator."""
        self.schema = self._get_schema()

    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate configuration against schema.

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(valid=True)

        # Validate required top-level fields
        self._validate_required_fields(config, result)

        # Validate paths
        self._validate_paths(config, result)

        # Validate extraction settings
        self._validate_extraction(config, result)

        # Validate insight settings
        self._validate_insights(config, result)

        # Validate quality settings
        self._validate_quality(config, result)

        # Validate performance settings
        self._validate_performance(config, result)

        # Validate monitoring settings
        self._validate_monitoring(config, result)

        # Validate feature flags
        self._validate_feature_flags(config, result)

        # Check for validity
        result.valid = len(result.errors) == 0

        return result

    def _validate_required_fields(self, config: Dict[str, Any], result: ValidationResult):
        """Validate required top-level fields."""
        required_fields = {
            "source_dir": str,
            "target_dir": str
        }

        for field, field_type in required_fields.items():
            if field not in config:
                result.errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing",
                    severity="error"
                ))
            elif not isinstance(config[field], field_type):
                result.errors.append(ValidationError(
                    field=field,
                    message=f"Field '{field}' must be {field_type.__name__}, got {type(config[field]).__name__}",
                    severity="error",
                    value=config[field]
                ))

    def _validate_paths(self, config: Dict[str, Any], result: ValidationResult):
        """Validate file system paths."""
        path_fields = ["source_dir", "target_dir"]

        for field in path_fields:
            if field in config:
                path_str = config[field]
                if not isinstance(path_str, str):
                    result.errors.append(ValidationError(
                        field=field,
                        message=f"Path must be string, got {type(path_str).__name__}",
                        severity="error",
                        value=path_str
                    ))
                    continue

                # Check if path is absolute
                if not os.path.isabs(path_str):
                    result.warnings.append(ValidationError(
                        field=field,
                        message=f"Path '{path_str}' is relative, absolute path recommended",
                        severity="warning",
                        value=path_str
                    ))

                # Check if parent directory exists
                parent_dir = os.path.dirname(path_str)
                if parent_dir and not os.path.exists(parent_dir):
                    result.errors.append(ValidationError(
                        field=field,
                        message=f"Parent directory does not exist: {parent_dir}",
                        severity="error",
                        value=path_str
                    ))

    def _validate_extraction(self, config: Dict[str, Any], result: ValidationResult):
        """Validate extraction settings."""
        if "extraction" not in config:
            return

        extraction = config["extraction"]
        if not isinstance(extraction, dict):
            result.errors.append(ValidationError(
                field="extraction",
                message="Extraction settings must be a dictionary",
                severity="error",
                value=extraction
            ))
            return

        # Validate min_confidence
        if "min_confidence" in extraction:
            min_conf = extraction["min_confidence"]
            if not isinstance(min_conf, (int, float)):
                result.errors.append(ValidationError(
                    field="extraction.min_confidence",
                    message="min_confidence must be a number",
                    severity="error",
                    value=min_conf
                ))
            elif not 0.0 <= min_conf <= 1.0:
                result.errors.append(ValidationError(
                    field="extraction.min_confidence",
                    message="min_confidence must be between 0.0 and 1.0",
                    severity="error",
                    value=min_conf
                ))

        # Validate max_concepts
        if "max_concepts" in extraction:
            max_concepts = extraction["max_concepts"]
            if not isinstance(max_concepts, int):
                result.errors.append(ValidationError(
                    field="extraction.max_concepts",
                    message="max_concepts must be an integer",
                    severity="error",
                    value=max_concepts
                ))
            elif max_concepts < 1:
                result.errors.append(ValidationError(
                    field="extraction.max_concepts",
                    message="max_concepts must be at least 1",
                    severity="error",
                    value=max_concepts
                ))

    def _validate_insights(self, config: Dict[str, Any], result: ValidationResult):
        """Validate insight settings."""
        if "insights" not in config:
            return

        insights = config["insights"]
        if not isinstance(insights, dict):
            result.errors.append(ValidationError(
                field="insights",
                message="Insight settings must be a dictionary",
                severity="error",
                value=insights
            ))
            return

        # Validate max_hops
        if "max_hops" in insights:
            max_hops = insights["max_hops"]
            if not isinstance(max_hops, int):
                result.errors.append(ValidationError(
                    field="insights.max_hops",
                    message="max_hops must be an integer",
                    severity="error",
                    value=max_hops
                ))
            elif max_hops < 1 or max_hops > 5:
                result.warnings.append(ValidationError(
                    field="insights.max_hops",
                    message="max_hops should be between 1 and 5 for optimal performance",
                    severity="warning",
                    value=max_hops
                ))

    def _validate_quality(self, config: Dict[str, Any], result: ValidationResult):
        """Validate quality settings."""
        if "quality" not in config:
            return

        quality = config["quality"]
        if not isinstance(quality, dict):
            result.errors.append(ValidationError(
                field="quality",
                message="Quality settings must be a dictionary",
                severity="error",
                value=quality
            ))
            return

        # Validate min_quality_score
        if "min_quality_score" in quality:
            min_score = quality["min_quality_score"]
            if not isinstance(min_score, (int, float)):
                result.errors.append(ValidationError(
                    field="quality.min_quality_score",
                    message="min_quality_score must be a number",
                    severity="error",
                    value=min_score
                ))
            elif not 0.0 <= min_score <= 1.0:
                result.errors.append(ValidationError(
                    field="quality.min_quality_score",
                    message="min_quality_score must be between 0.0 and 1.0",
                    severity="error",
                    value=min_score
                ))

        # Validate max_stale_days
        if "max_stale_days" in quality:
            max_stale = quality["max_stale_days"]
            if not isinstance(max_stale, int):
                result.errors.append(ValidationError(
                    field="quality.max_stale_days",
                    message="max_stale_days must be an integer",
                    severity="error",
                    value=max_stale
                ))
            elif max_stale < 1:
                result.errors.append(ValidationError(
                    field="quality.max_stale_days",
                    message="max_stale_days must be at least 1",
                    severity="error",
                    value=max_stale
                ))

    def _validate_performance(self, config: Dict[str, Any], result: ValidationResult):
        """Validate performance settings."""
        if "performance" not in config:
            return

        performance = config["performance"]
        if not isinstance(performance, dict):
            result.errors.append(ValidationError(
                field="performance",
                message="Performance settings must be a dictionary",
                severity="error",
                value=performance
            ))
            return

        # Validate max_workers
        if "max_workers" in performance:
            max_workers = performance["max_workers"]
            if not isinstance(max_workers, int):
                result.errors.append(ValidationError(
                    field="performance.max_workers",
                    message="max_workers must be an integer",
                    severity="error",
                    value=max_workers
                ))
            elif max_workers < 1:
                result.errors.append(ValidationError(
                    field="performance.max_workers",
                    message="max_workers must be at least 1",
                    severity="error",
                    value=max_workers
                ))
            elif max_workers > 16:
                result.warnings.append(ValidationError(
                    field="performance.max_workers",
                    message="max_workers > 16 may cause performance issues",
                    severity="warning",
                    value=max_workers
                ))

        # Validate cache_ttl
        if "cache_ttl" in performance:
            cache_ttl = performance["cache_ttl"]
            if not isinstance(cache_ttl, int):
                result.errors.append(ValidationError(
                    field="performance.cache_ttl",
                    message="cache_ttl must be an integer",
                    severity="error",
                    value=cache_ttl
                ))
            elif cache_ttl < 0:
                result.errors.append(ValidationError(
                    field="performance.cache_ttl",
                    message="cache_ttl must be non-negative",
                    severity="error",
                    value=cache_ttl
                ))

    def _validate_monitoring(self, config: Dict[str, Any], result: ValidationResult):
        """Validate monitoring settings."""
        if "monitoring" not in config:
            return

        monitoring = config["monitoring"]
        if not isinstance(monitoring, dict):
            result.errors.append(ValidationError(
                field="monitoring",
                message="Monitoring settings must be a dictionary",
                severity="error",
                value=monitoring
            ))
            return

        # Validate log_level
        if "log_level" in monitoring:
            log_level = monitoring["log_level"]
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if log_level not in valid_levels:
                result.errors.append(ValidationError(
                    field="monitoring.log_level",
                    message=f"log_level must be one of {valid_levels}",
                    severity="error",
                    value=log_level
                ))

        # Validate metrics_port
        if "metrics_port" in monitoring:
            metrics_port = monitoring["metrics_port"]
            if not isinstance(metrics_port, int):
                result.errors.append(ValidationError(
                    field="monitoring.metrics_port",
                    message="metrics_port must be an integer",
                    severity="error",
                    value=metrics_port
                ))
            elif metrics_port < 1024 or metrics_port > 65535:
                result.errors.append(ValidationError(
                    field="monitoring.metrics_port",
                    message="metrics_port must be between 1024 and 65535",
                    severity="error",
                    value=metrics_port
                ))

    def _validate_feature_flags(self, config: Dict[str, Any], result: ValidationResult):
        """Validate feature flag settings."""
        if "feature_flags" not in config:
            return

        feature_flags = config["feature_flags"]
        if not isinstance(feature_flags, dict):
            result.errors.append(ValidationError(
                field="feature_flags",
                message="Feature flags must be a dictionary",
                severity="error",
                value=feature_flags
            ))
            return

        for flag_name, flag_config in feature_flags.items():
            if not isinstance(flag_config, dict):
                result.errors.append(ValidationError(
                    field=f"feature_flags.{flag_name}",
                    message="Feature flag config must be a dictionary",
                    severity="error",
                    value=flag_config
                ))
                continue

            # Validate enabled field
            if "enabled" in flag_config and not isinstance(flag_config["enabled"], bool):
                result.errors.append(ValidationError(
                    field=f"feature_flags.{flag_name}.enabled",
                    message="enabled must be a boolean",
                    severity="error",
                    value=flag_config["enabled"]
                ))

    def _get_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "type": "object",
            "required": ["source_dir", "target_dir"],
            "properties": {
                "source_dir": {"type": "string"},
                "target_dir": {"type": "string"},
                "categories": {"type": "array", "items": {"type": "string"}},
                "extraction": {
                    "type": "object",
                    "properties": {
                        "min_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "max_concepts": {"type": "integer", "minimum": 1}
                    }
                }
            }
        }

    def format_errors(self, result: ValidationResult) -> str:
        """
        Format validation errors as readable string.

        Args:
            result: ValidationResult

        Returns:
            Formatted error messages
        """
        lines = []

        if result.errors:
            lines.append("Configuration Errors:")
            for error in result.errors:
                lines.append(f"  ✗ {error.field}: {error.message}")
                if error.value is not None:
                    lines.append(f"    Value: {error.value}")

        if result.warnings:
            if lines:
                lines.append("")
            lines.append("Configuration Warnings:")
            for warning in result.warnings:
                lines.append(f"  ⚠ {warning.field}: {warning.message}")
                if warning.value is not None:
                    lines.append(f"    Value: {warning.value}")

        if result.valid:
            lines.insert(0, "✓ Configuration is valid")
        else:
            lines.insert(0, "✗ Configuration has errors")

        return "\n".join(lines)


class ConfigProfileTester:
    """
    Test configuration profiles against different scenarios.

    Provides predefined configuration profiles for common use cases
    and validates them against expected constraints.
    """

    # Predefined configuration profiles
    PROFILES = {
        "development": {
            "description": "Development environment configuration",
            "config": {
                "source_dir": "./documents",
                "target_dir": "./wiki",
                "extraction": {
                    "min_confidence": 0.5,
                    "max_concepts": 50
                },
                "performance": {
                    "cache_enabled": True,
                    "cache_ttl": 3600,
                    "max_workers": 2
                },
                "monitoring": {
                    "log_level": "DEBUG",
                    "metrics_enabled": False
                }
            }
        },
        "production": {
            "description": "Production environment configuration",
            "config": {
                "source_dir": "/var/lib/knowledge-compiler/documents",
                "target_dir": "/var/lib/knowledge-compiler/wiki",
                "extraction": {
                    "min_confidence": 0.7,
                    "max_concepts": 100
                },
                "insights": {
                    "enabled": True,
                    "max_hops": 2
                },
                "quality": {
                    "enabled": True,
                    "min_quality_score": 0.8
                },
                "performance": {
                    "cache_enabled": True,
                    "cache_ttl": 7200,
                    "max_workers": 8
                },
                "monitoring": {
                    "log_level": "INFO",
                    "metrics_enabled": True,
                    "metrics_port": 9090,
                    "alert_enabled": True
                }
            }
        },
        "testing": {
            "description": "Testing environment configuration",
            "config": {
                "source_dir": "/tmp/test/documents",
                "target_dir": "/tmp/test/wiki",
                "extraction": {
                    "min_confidence": 0.3,
                    "max_concepts": 20
                },
                "performance": {
                    "cache_enabled": False,
                    "max_workers": 1
                },
                "monitoring": {
                    "log_level": "DEBUG",
                    "metrics_enabled": False
                },
                "feature_flags": {
                    "experimental_features": {
                        "enabled": True
                    }
                }
            }
        }
    }

    def __init__(self):
        """Initialize ConfigProfileTester."""
        self.validator = ConfigValidator()

    def test_profile(self, profile_name: str) -> ValidationResult:
        """
        Test configuration profile.

        Args:
            profile_name: Name of profile to test

        Returns:
            ValidationResult
        """
        if profile_name not in self.PROFILES:
            result = ValidationResult(valid=False)
            result.errors.append(ValidationError(
                field="profile",
                message=f"Unknown profile: {profile_name}",
                severity="error"
            ))
            return result

        profile = self.PROFILES[profile_name]
        return self.validator.validate(profile["config"])

    def list_profiles(self) -> List[str]:
        """List available configuration profiles."""
        return list(self.PROFILES.keys())

    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration profile."""
        profile = self.PROFILES.get(profile_name)
        return profile["config"] if profile else None

    def get_profile_description(self, profile_name: str) -> Optional[str]:
        """Get profile description."""
        profile = self.PROFILES.get(profile_name)
        return profile["description"] if profile else None

    def test_all_profiles(self) -> Dict[str, ValidationResult]:
        """Test all configuration profiles."""
        results = {}
        for profile_name in self.PROFILES:
            results[profile_name] = self.test_profile(profile_name)
        return results
