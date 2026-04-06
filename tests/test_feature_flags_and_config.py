"""
Tests for Feature Flags and Configuration Validation (Tasks 5.4 and 5.5).
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from src.features.flags import FeatureFlag, FeatureFlagManager, ABTestManager
from src.config.validator import (
    ConfigValidator,
    ConfigProfileTester,
    ValidationError,
    ValidationResult
)


@pytest.fixture
def temp_flag_manager():
    """Create isolated FeatureFlagManager for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_flags.json"
        manager = FeatureFlagManager(storage_path=str(storage_path))
        yield manager


class TestFeatureFlag:
    """Test FeatureFlag dataclass."""

    def test_feature_flag_creation(self):
        """Test creating a feature flag."""
        flag = FeatureFlag(
            name="test_flag",
            description="Test flag description"
        )

        assert flag.name == "test_flag"
        assert flag.description == "Test flag description"
        assert flag.enabled is False
        assert flag.rollout_percentage == 0.0
        assert flag.whitelist == set()
        assert flag.blacklist == set()

    def test_feature_flag_with_options(self):
        """Test creating feature flag with options."""
        flag = FeatureFlag(
            name="test_flag",
            description="Test flag",
            enabled=True,
            rollout_percentage=50.0,
            whitelist={"user1", "user2"},
            blacklist={"user3"}
        )

        assert flag.enabled is True
        assert flag.rollout_percentage == 50.0
        assert flag.whitelist == {"user1", "user2"}
        assert flag.blacklist == {"user3"}


class TestFeatureFlagManager:
    """Test FeatureFlagManager."""

    def test_define_flag(self):
        """Test defining a new feature flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_flags.json"
            manager = FeatureFlagManager(storage_path=str(storage_path))

            flag = manager.define_flag(
                name="test_flag",
                description="Test flag"
            )

            assert flag.name == "test_flag"
            assert flag in manager.list_flags()

    def test_define_duplicate_flag(self, temp_flag_manager):
        """Test defining duplicate flag raises error."""
        temp_flag_manager.define_flag(name="test_flag", description="Test")

        with pytest.raises(ValueError, match="already exists"):
            temp_flag_manager.define_flag(name="test_flag", description="Test")

    def test_is_enabled_globally_disabled(self, temp_flag_manager):
        """Test is_enabled when flag is globally disabled."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test",
            enabled=False
        )

        assert temp_flag_manager.is_enabled("test_flag") is False

    def test_is_enabled_globally_enabled(self, temp_flag_manager):
        """Test is_enabled when flag is globally enabled."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test",
            enabled=True
        )

        assert temp_flag_manager.is_enabled("test_flag") is True

    def test_is_enabled_whitelist(self, temp_flag_manager):
        """Test is_enabled with whitelist."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test",
            enabled=True,
            whitelist={"user1", "user2"}
        )

        assert temp_flag_manager.is_enabled("test_flag", user_id="user1") is True
        assert temp_flag_manager.is_enabled("test_flag", user_id="user2") is True
        assert temp_flag_manager.is_enabled("test_flag", user_id="user3") is False

    def test_is_enabled_blacklist(self, temp_flag_manager):
        """Test is_enabled with blacklist."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test",
            enabled=True,
            blacklist={"user1"}
        )

        assert temp_flag_manager.is_enabled("test_flag", user_id="user1") is False
        assert temp_flag_manager.is_enabled("test_flag", user_id="user2") is True

    def test_is_enabled_percentage_rollout(self, temp_flag_manager):
        """Test is_enabled with percentage rollout."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test",
            enabled=True,
            rollout_percentage=50.0
        )

        # Due to consistent hashing, same user should get same result
        result1 = temp_flag_manager.is_enabled("test_flag", user_id="test_user")
        result2 = temp_flag_manager.is_enabled("test_flag", user_id="test_user")
        assert result1 == result2

    def test_enable_flag(self, temp_flag_manager):
        """Test enabling a flag."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test",
            enabled=False
        )

        temp_flag_manager.enable_flag("test_flag")
        assert temp_flag_manager.is_enabled("test_flag") is True

    def test_disable_flag(self, temp_flag_manager):
        """Test disabling a flag (quick rollback)."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test",
            enabled=True
        )

        temp_flag_manager.disable_flag("test_flag")
        assert temp_flag_manager.is_enabled("test_flag") is False

    def test_set_rollout_percentage(self, temp_flag_manager):
        """Test setting rollout percentage."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test"
        )

        temp_flag_manager.set_rollout_percentage("test_flag", 75.0)
        flag = temp_flag_manager.get_flag("test_flag")
        assert flag.rollout_percentage == 75.0

    def test_set_rollout_percentage_invalid(self, temp_flag_manager):
        """Test setting invalid rollout percentage."""
        temp_flag_manager.define_flag(name="test_flag", description="Test")

        with pytest.raises(ValueError, match="between 0 and 100"):
            temp_flag_manager.set_rollout_percentage("test_flag", 150.0)

    def test_add_to_whitelist(self, temp_flag_manager):
        """Test adding user to whitelist."""
        temp_flag_manager.define_flag(name="test_flag", description="Test", enabled=True)
        temp_flag_manager.add_to_whitelist("test_flag", "user1")

        assert temp_flag_manager.is_enabled("test_flag", user_id="user1") is True

    def test_remove_from_whitelist(self, temp_flag_manager):
        """Test removing user from whitelist."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test",
            enabled=True,
            whitelist={"user1"}
        )

        temp_flag_manager.remove_from_whitelist("test_flag", "user1")
        assert temp_flag_manager.is_enabled("test_flag", user_id="user1") is False

    def test_add_to_blacklist(self, temp_flag_manager):
        """Test adding user to blacklist."""
        temp_flag_manager.define_flag(name="test_flag", description="Test", enabled=True)
        temp_flag_manager.add_to_blacklist("test_flag", "user1")

        assert temp_flag_manager.is_enabled("test_flag", user_id="user1") is False

    def test_remove_from_blacklist(self, temp_flag_manager):
        """Test removing user from blacklist."""
        temp_flag_manager.define_flag(
            name="test_flag",
            description="Test",
            enabled=True,
            blacklist={"user1"}
        )

        temp_flag_manager.remove_from_blacklist("test_flag", "user1")
        assert temp_flag_manager.is_enabled("test_flag", user_id="user1") is True

    def test_get_flag(self, temp_flag_manager):
        """Test getting flag by name."""
        flag = temp_flag_manager.define_flag(name="test_flag", description="Test")
        retrieved = temp_flag_manager.get_flag("test_flag")

        assert retrieved is flag
        assert retrieved.name == "test_flag"

    def test_get_nonexistent_flag(self, temp_flag_manager):
        """Test getting non-existent flag."""
        flag = temp_flag_manager.get_flag("nonexistent")
        assert flag is None

    def test_list_flags(self, temp_flag_manager):
        """Test listing all flags."""
        temp_flag_manager.define_flag(name="flag1", description="Test 1")
        temp_flag_manager.define_flag(name="flag2", description="Test 2")

        flags = temp_flag_manager.list_flags()
        assert len(flags) == 2
        flag_names = {f.name for f in flags}
        assert flag_names == {"flag1", "flag2"}

    def test_delete_flag(self, temp_flag_manager):
        """Test deleting a flag."""
        temp_flag_manager.define_flag(name="test_flag", description="Test")
        temp_flag_manager.delete_flag("test_flag")

        assert temp_flag_manager.get_flag("test_flag") is None

    def test_flag_persistence(self):
        """Test flag persistence to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_flags.json"
            manager = FeatureFlagManager(storage_path=str(storage_path))

            # Create flag
            manager.define_flag(
                name="test_flag",
                description="Test",
                enabled=True,
                rollout_percentage=50.0
            )

            # Create new manager instance (should load from file)
            manager2 = FeatureFlagManager(storage_path=str(storage_path))
            flag = manager2.get_flag("test_flag")

            assert flag is not None
            assert flag.enabled is True
            assert flag.rollout_percentage == 50.0


class TestABTestManager:
    """Test ABTestManager."""

    @pytest.fixture
    def ab_manager(self, temp_flag_manager):
        """Create ABTestManager with isolated flag manager."""
        return ABTestManager(temp_flag_manager)

    def test_create_experiment(self, ab_manager):
        """Test creating A/B test experiment."""
        flag_name = ab_manager.create_experiment(
            name="test_experiment",
            description="Test experiment",
            variants=["control", "treatment"]
        )

        assert flag_name == "ab_test_test_experiment"
        flag = ab_manager.flag_manager.get_flag(flag_name)
        assert flag is not None
        assert flag.enabled is True

    def test_create_experiment_with_traffic_split(self, ab_manager):
        """Test creating experiment with custom traffic split."""
        flag_name = ab_manager.create_experiment(
            name="test_experiment",
            description="Test",
            variants=["control", "treatment"],
            traffic_split=[70.0, 30.0]
        )

        flag = ab_manager.flag_manager.get_flag(flag_name)
        assert flag.metadata["traffic_split"] == [70.0, 30.0]

    def test_create_experiment_invalid_traffic_split(self, ab_manager):
        """Test creating experiment with invalid traffic split."""
        with pytest.raises(ValueError, match="must sum to 100"):
            ab_manager.create_experiment(
                name="test_experiment",
                description="Test",
                variants=["control", "treatment"],
                traffic_split=[50.0, 50.0, 10.0]  # Sums to 110
            )

    def test_get_variant(self, ab_manager):
        """Test getting variant for user."""
        ab_manager.create_experiment(
            name="test_experiment",
            description="Test",
            variants=["control", "treatment"]
        )

        variant = ab_manager.get_variant("test_experiment", "user123")
        assert variant in ["control", "treatment"]

    def test_get_variant_consistency(self, ab_manager):
        """Test that same user gets same variant consistently."""
        ab_manager.create_experiment(
            name="test_experiment",
            description="Test",
            variants=["control", "treatment"]
        )

        variant1 = ab_manager.get_variant("test_experiment", "user123")
        variant2 = ab_manager.get_variant("test_experiment", "user123")

        assert variant1 == variant2

    def test_get_variant_no_experiment(self, ab_manager):
        """Test getting variant from non-existent experiment."""
        variant = ab_manager.get_variant("nonexistent", "user123")
        assert variant is None

    def test_is_control(self, ab_manager):
        """Test checking if user is in control group."""
        ab_manager.create_experiment(
            name="test_experiment",
            description="Test",
            variants=["control", "treatment"]
        )

        # For some users, this will be True
        is_control = ab_manager.is_control("test_experiment", "user123")
        assert isinstance(is_control, bool)

    def test_end_experiment(self, ab_manager):
        """Test ending experiment."""
        ab_manager.create_experiment(
            name="test_experiment",
            description="Test",
            variants=["control", "treatment"]
        )

        ab_manager.end_experiment("test_experiment")

        flag = ab_manager.flag_manager.get_flag("ab_test_test_experiment")
        assert flag.enabled is False


class TestConfigValidator:
    """Test ConfigValidator."""

    def test_validate_missing_required_field(self):
        """Test validation with missing required field."""
        validator = ConfigValidator()
        config = {}  # Missing source_dir and target_dir

        result = validator.validate(config)

        assert result.valid is False
        assert len(result.errors) == 2
        error_fields = {e.field for e in result.errors}
        assert "source_dir" in error_fields
        assert "target_dir" in error_fields

    def test_validate_invalid_type(self):
        """Test validation with invalid field type."""
        validator = ConfigValidator()
        config = {
            "source_dir": 123,  # Should be string
            "target_dir": "/path/to/wiki"
        }

        result = validator.validate(config)

        assert result.valid is False
        assert any(e.field == "source_dir" for e in result.errors)

    def test_validate_relative_path_warning(self):
        """Test validation warns on relative paths."""
        validator = ConfigValidator()
        config = {
            "source_dir": "./documents",  # Relative path
            "target_dir": "./wiki"
        }

        result = validator.validate(config)

        # Should be valid but with warnings
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("relative" in w.message.lower() for w in result.warnings)

    def test_validate_extraction_min_confidence(self):
        """Test extraction min_confidence validation."""
        validator = ConfigValidator()

        # Invalid range
        config = {
            "source_dir": "/path",
            "target_dir": "/path",
            "extraction": {
                "min_confidence": 1.5  # Invalid, must be 0.0-1.0
            }
        }

        result = validator.validate(config)
        assert result.valid is False
        assert any("min_confidence" in e.field for e in result.errors)

    def test_validate_extraction_max_concepts(self):
        """Test extraction max_concepts validation."""
        validator = ConfigValidator()

        config = {
            "source_dir": "/path",
            "target_dir": "/path",
            "extraction": {
                "max_concepts": 0  # Invalid, must be >= 1
            }
        }

        result = validator.validate(config)
        assert result.valid is False
        assert any("max_concepts" in e.field for e in result.errors)

    def test_validate_performance_max_workers(self):
        """Test performance max_workers validation."""
        validator = ConfigValidator()

        config = {
            "source_dir": "/path",
            "target_dir": "/path",
            "performance": {
                "max_workers": 0  # Invalid, must be >= 1
            }
        }

        result = validator.validate(config)
        assert result.valid is False
        assert any("max_workers" in e.field for e in result.errors)

    def test_validate_performance_max_workers_warning(self):
        """Test performance max_workers warning for high values."""
        validator = ConfigValidator()

        config = {
            "source_dir": "/path",
            "target_dir": "/path",
            "performance": {
                "max_workers": 20  # High, should warn
            }
        }

        result = validator.validate(config)
        assert result.valid is True  # Should still be valid
        assert any("max_workers" in w.field for w in result.warnings)

    def test_validate_monitoring_log_level(self):
        """Test monitoring log_level validation."""
        validator = ConfigValidator()

        config = {
            "source_dir": "/path",
            "target_dir": "/path",
            "monitoring": {
                "log_level": "INVALID"  # Invalid log level
            }
        }

        result = validator.validate(config)
        assert result.valid is False
        assert any("log_level" in e.field for e in result.errors)

    def test_validate_monitoring_metrics_port(self):
        """Test monitoring metrics_port validation."""
        validator = ConfigValidator()

        config = {
            "source_dir": "/path",
            "target_dir": "/path",
            "monitoring": {
                "metrics_port": 100  # Invalid, must be 1024-65535
            }
        }

        result = validator.validate(config)
        assert result.valid is False
        assert any("metrics_port" in e.field for e in result.errors)

    def test_format_errors(self):
        """Test formatting validation errors."""
        validator = ConfigValidator()
        config = {
            "source_dir": "/path",
            "target_dir": "/path"
        }

        result = validator.validate(config)
        formatted = validator.format_errors(result)

        assert "✓ Configuration is valid" in formatted

    def test_format_errors_with_issues(self):
        """Test formatting errors with actual issues."""
        validator = ConfigValidator()
        config = {}  # Missing required fields

        result = validator.validate(config)
        formatted = validator.format_errors(result)

        assert "✗ Configuration has errors" in formatted
        assert "Configuration Errors:" in formatted


class TestConfigProfileTester:
    """Test ConfigProfileTester."""

    def test_list_profiles(self):
        """Test listing available profiles."""
        tester = ConfigProfileTester()
        profiles = tester.list_profiles()

        assert "development" in profiles
        assert "production" in profiles
        assert "testing" in profiles

    def test_get_profile(self):
        """Test getting profile configuration."""
        tester = ConfigProfileTester()
        profile = tester.get_profile("development")

        assert profile is not None
        assert "source_dir" in profile
        assert "target_dir" in profile

    def test_get_profile_description(self):
        """Test getting profile description."""
        tester = ConfigProfileTester()
        description = tester.get_profile_description("development")

        assert description is not None
        assert "Development" in description

    def test_test_profile(self):
        """Test testing a profile."""
        import platform
        tester = ConfigProfileTester()
        result = tester.test_profile("production")

        # Production profile should be valid on Unix systems
        # On Windows, paths will fail validation since they use Linux paths
        if platform.system() == "Windows":
            # On Windows, we expect path validation errors
            # but the configuration structure itself should be valid
            assert len(result.errors) > 0  # Path errors expected
            # All errors should be path-related
            assert all("path" in e.field.lower() or "dir" in e.field.lower() for e in result.errors)
        else:
            # On Unix, should be fully valid
            assert result.valid is True

    def test_test_invalid_profile(self):
        """Test testing non-existent profile."""
        tester = ConfigProfileTester()
        result = tester.test_profile("nonexistent")

        assert result.valid is False
        assert len(result.errors) == 1
        assert "Unknown profile" in result.errors[0].message

    def test_test_all_profiles(self):
        """Test testing all profiles."""
        tester = ConfigProfileTester()
        results = tester.test_all_profiles()

        assert "development" in results
        assert "production" in results
        assert "testing" in results

        # All profiles should be valid
        for profile_name, result in results.items():
            assert result.valid, f"Profile {profile_name} should be valid"


class TestIntegration:
    """Integration tests for feature flags and config."""

    def test_feature_flag_with_config(self, temp_flag_manager):
        """Test using feature flags with configuration."""
        # Define feature flag
        temp_flag_manager.define_flag(
            name="experimental_extraction",
            description="Experimental extraction algorithm",
            enabled=True,
            rollout_percentage=10.0
        )

        # Use in application
        if temp_flag_manager.is_enabled("experimental_extraction", user_id="user123"):
            # Use experimental algorithm
            pass
        else:
            # Use standard algorithm
            pass

    def test_ab_test_with_config_validation(self, temp_flag_manager):
        """Test A/B testing with config validation."""
        ab_manager = ABTestManager(temp_flag_manager)
        validator = ConfigValidator()

        # Create A/B test
        ab_manager.create_experiment(
            name="extraction_algorithm",
            description="Test new extraction algorithm",
            variants=["standard", "experimental"],
            traffic_split=[80.0, 20.0]
        )

        # Get variant for user
        variant = ab_manager.get_variant("extraction_algorithm", "user123")

        # Configure based on variant
        config = {
            "source_dir": "./path",
            "target_dir": "./path",
            "extraction": {
                "algorithm": variant
            }
        }

        # Validate config
        result = validator.validate(config)
        assert result.valid is True

    def test_gradual_rollout_workflow(self, temp_flag_manager):
        """Test gradual rollout workflow."""
        # Start with 10% rollout
        temp_flag_manager.define_flag(
            name="new_feature",
            description="New feature",
            enabled=True,
            rollout_percentage=10.0
        )

        # Gradually increase
        for percentage in [25.0, 50.0, 75.0, 100.0]:
            temp_flag_manager.set_rollout_percentage("new_feature", percentage)
            flag = temp_flag_manager.get_flag("new_feature")
            assert flag.rollout_percentage == percentage

        # Quick rollback if needed
        temp_flag_manager.disable_flag("new_feature")
        assert temp_flag_manager.is_enabled("new_feature") is False
