"""
Feature flag management for gradual rollout and A/B testing.

Provides feature flag system with:
- Dynamic flag enabling/disabling
- User-based rollout (whitelist/blacklist)
- Percentage-based rollout
- A/B testing support
- Quick rollback capability
"""

import json
import hashlib
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import random


@dataclass
class FeatureFlag:
    """Feature flag definition."""
    name: str
    description: str
    enabled: bool = False
    rollout_percentage: float = 0.0  # 0.0 to 100.0
    whitelist: Set[str] = field(default_factory=set)  # User IDs always enabled
    blacklist: Set[str] = field(default_factory=set)  # User IDs never enabled
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class FeatureFlagManager:
    """
    Manage feature flags for gradual rollout and A/B testing.

    Features:
    - Dynamic flag enabling/disabling
    - User-based targeting (whitelist/blacklist)
    - Percentage-based rollout
    - A/B test variant assignment
    - Flag persistence
    - Rollback support

    Usage:
        manager = FeatureFlagManager()

        # Define feature flag
        manager.define_flag(
            name="new_insight_propagation",
            description="Enhanced insight propagation algorithm",
            enabled=True,
            rollout_percentage=10.0  # Roll out to 10% of users
        )

        # Check if flag is enabled for user
        if manager.is_enabled("new_insight_propagation", user_id="user_123"):
            # Use new feature
            pass

        # Quick rollback
        manager.disable_flag("new_insight_propagation")
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize FeatureFlagManager.

        Args:
            storage_path: Path to flag storage file (default: flags.json)
        """
        self.storage_path = storage_path or "flags.json"
        self.flags: Dict[str, FeatureFlag] = {}
        self._load_flags()

    def define_flag(
        self,
        name: str,
        description: str,
        enabled: bool = False,
        rollout_percentage: float = 0.0,
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeatureFlag:
        """
        Define a new feature flag.

        Args:
            name: Unique flag name
            description: Flag description
            enabled: Initial enabled state
            rollout_percentage: Rollout percentage (0.0-100.0)
            whitelist: List of user IDs always enabled
            blacklist: List of user IDs never enabled
            metadata: Additional metadata

        Returns:
            Created FeatureFlag
        """
        if name in self.flags:
            raise ValueError(f"Flag {name} already exists")

        flag = FeatureFlag(
            name=name,
            description=description,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            whitelist=set(whitelist or []),
            blacklist=set(blacklist or []),
            metadata=metadata or {}
        )

        self.flags[name] = flag
        self._save_flags()
        return flag

    def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if feature flag is enabled for user.

        Args:
            flag_name: Name of feature flag
            user_id: Optional user ID for targeting
            context: Additional context for evaluation

        Returns:
            True if flag is enabled, False otherwise
        """
        flag = self.flags.get(flag_name)
        if not flag:
            return False  # Unknown flags are disabled

        # Check if flag is globally enabled
        if not flag.enabled:
            return False

        # Check blacklist (explicit disable)
        if user_id and user_id in flag.blacklist:
            return False

        # Check whitelist (explicit enable)
        if user_id and user_id in flag.whitelist:
            return True

        # Check percentage-based rollout
        if flag.rollout_percentage < 100.0:
            if user_id:
                # Consistent hashing for user
                hash_value = self._hash_user(flag_name, user_id)
                return hash_value < flag.rollout_percentage
            else:
                # Random assignment for anonymous users
                return random.random() * 100.0 < flag.rollout_percentage

        # Flag is enabled for everyone
        return True

    def enable_flag(self, flag_name: str):
        """Enable feature flag globally."""
        flag = self.flags.get(flag_name)
        if not flag:
            raise ValueError(f"Flag {flag_name} not found")

        flag.enabled = True
        flag.updated_at = datetime.utcnow()
        self._save_flags()

    def disable_flag(self, flag_name: str):
        """Disable feature flag globally (quick rollback)."""
        flag = self.flags.get(flag_name)
        if not flag:
            raise ValueError(f"Flag {flag_name} not found")

        flag.enabled = False
        flag.updated_at = datetime.utcnow()
        self._save_flags()

    def set_rollout_percentage(self, flag_name: str, percentage: float):
        """Set rollout percentage for flag."""
        flag = self.flags.get(flag_name)
        if not flag:
            raise ValueError(f"Flag {flag_name} not found")

        if not 0.0 <= percentage <= 100.0:
            raise ValueError(f"Percentage must be between 0 and 100, got {percentage}")

        flag.rollout_percentage = percentage
        flag.updated_at = datetime.utcnow()
        self._save_flags()

    def add_to_whitelist(self, flag_name: str, user_id: str):
        """Add user to flag whitelist."""
        flag = self.flags.get(flag_name)
        if not flag:
            raise ValueError(f"Flag {flag_name} not found")

        flag.whitelist.add(user_id)
        flag.updated_at = datetime.utcnow()
        self._save_flags()

    def remove_from_whitelist(self, flag_name: str, user_id: str):
        """Remove user from flag whitelist."""
        flag = self.flags.get(flag_name)
        if not flag:
            raise ValueError(f"Flag {flag_name} not found")

        flag.whitelist.discard(user_id)
        flag.updated_at = datetime.utcnow()
        self._save_flags()

    def add_to_blacklist(self, flag_name: str, user_id: str):
        """Add user to flag blacklist."""
        flag = self.flags.get(flag_name)
        if not flag:
            raise ValueError(f"Flag {flag_name} not found")

        flag.blacklist.add(user_id)
        flag.updated_at = datetime.utcnow()
        self._save_flags()

    def remove_from_blacklist(self, flag_name: str, user_id: str):
        """Remove user from flag blacklist."""
        flag = self.flags.get(flag_name)
        if not flag:
            raise ValueError(f"Flag {flag_name} not found")

        flag.blacklist.discard(user_id)
        flag.updated_at = datetime.utcnow()
        self._save_flags()

    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get feature flag by name."""
        return self.flags.get(flag_name)

    def list_flags(self) -> List[FeatureFlag]:
        """List all feature flags."""
        return list(self.flags.values())

    def delete_flag(self, flag_name: str):
        """Delete feature flag."""
        if flag_name in self.flags:
            del self.flags[flag_name]
            self._save_flags()

    def _hash_user(self, flag_name: str, user_id: str) -> float:
        """
        Generate consistent hash value for user.

        Returns value between 0 and 100.
        """
        # Combine flag name and user ID
        combined = f"{flag_name}:{user_id}"
        hash_value = hashlib.md5(combined.encode()).hexdigest()

        # Convert to 0-100 range
        return int(hash_value[:8], 16) % 10000 / 100.0

    def _load_flags(self):
        """Load flags from storage."""
        path = Path(self.storage_path)
        if not path.exists():
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for flag_data in data.get("flags", []):
                flag = FeatureFlag(
                    name=flag_data["name"],
                    description=flag_data["description"],
                    enabled=flag_data["enabled"],
                    rollout_percentage=flag_data["rollout_percentage"],
                    whitelist=set(flag_data.get("whitelist", [])),
                    blacklist=set(flag_data.get("blacklist", [])),
                    metadata=flag_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(flag_data["created_at"]),
                    updated_at=datetime.fromisoformat(flag_data["updated_at"])
                )
                self.flags[flag.name] = flag

        except Exception as e:
            print(f"Warning: Failed to load flags: {e}")

    def _save_flags(self):
        """Save flags to storage."""
        data = {
            "flags": []
        }

        for flag in self.flags.values():
            flag_data = {
                "name": flag.name,
                "description": flag.description,
                "enabled": flag.enabled,
                "rollout_percentage": flag.rollout_percentage,
                "whitelist": list(flag.whitelist),
                "blacklist": list(flag.blacklist),
                "metadata": flag.metadata,
                "created_at": flag.created_at.isoformat(),
                "updated_at": flag.updated_at.isoformat()
            }
            data["flags"].append(flag_data)

        path = Path(self.storage_path)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save flags: {e}")


class ABTestManager:
    """
    Manage A/B testing experiments.

    Features:
    - Multiple variants (A, B, C, etc.)
    - Traffic splitting
    - Variant assignment consistency
    - Metrics tracking
    """

    def __init__(self, feature_flag_manager: FeatureFlagManager):
        """
        Initialize ABTestManager.

        Args:
            feature_flag_manager: FeatureFlagManager instance
        """
        self.flag_manager = feature_flag_manager

    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[str],
        traffic_split: Optional[List[float]] = None
    ) -> str:
        """
        Create A/B test experiment.

        Args:
            name: Experiment name
            description: Experiment description
            variants: List of variant names (e.g., ["control", "treatment"])
            traffic_split: Optional traffic split percentages (must sum to 100)

        Returns:
            Feature flag name for experiment
        """
        if traffic_split:
            if len(traffic_split) != len(variants):
                raise ValueError("Traffic split must match variants length")
            if abs(sum(traffic_split) - 100.0) > 0.01:
                raise ValueError("Traffic split must sum to 100")

        flag_name = f"ab_test_{name}"

        # Create flag with percentage-based rollout
        self.flag_manager.define_flag(
            name=flag_name,
            description=f"A/B Test: {description}",
            enabled=True,
            rollout_percentage=100.0,
            metadata={
                "experiment_name": name,
                "variants": variants,
                "traffic_split": traffic_split or [100.0 / len(variants)] * len(variants)
            }
        )

        return flag_name

    def get_variant(
        self,
        experiment_name: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Get assigned variant for user in experiment.

        Args:
            experiment_name: Name of experiment
            user_id: User ID
            context: Additional context

        Returns:
            Assigned variant name or None if experiment not active
        """
        flag_name = f"ab_test_{experiment_name}"
        flag = self.flag_manager.get_flag(flag_name)

        if not flag or not flag.enabled:
            return None

        variants = flag.metadata.get("variants", [])
        traffic_split = flag.metadata.get("traffic_split", [])

        if not variants:
            return None

        # Use consistent hashing to assign variant
        hash_value = self.flag_manager._hash_user(flag_name, user_id)
        cumulative = 0.0

        for i, (variant, split) in enumerate(zip(variants, traffic_split)):
            cumulative += split
            if hash_value < cumulative:
                return variant

        # Fallback to last variant
        return variants[-1]

    def is_control(
        self,
        experiment_name: str,
        user_id: str
    ) -> bool:
        """
        Check if user is in control group.

        Args:
            experiment_name: Name of experiment
            user_id: User ID

        Returns:
            True if user is in control group (first variant)
        """
        variant = self.get_variant(experiment_name, user_id)
        flag_name = f"ab_test_{experiment_name}"
        flag = self.flag_manager.get_flag(flag_name)

        if not flag or not variant:
            return False

        variants = flag.metadata.get("variants", [])
        return variant == variants[0] if variants else False

    def end_experiment(self, experiment_name: str, winning_variant: Optional[str] = None):
        """
        End A/B test experiment.

        Args:
            experiment_name: Name of experiment
            winning_variant: Optional winning variant to rollout to 100%
        """
        flag_name = f"ab_test_{experiment_name}"

        if winning_variant:
            # Update flag to enable winning variant for all
            # This would require custom logic in your application
            pass
        else:
            # Disable experiment
            self.flag_manager.disable_flag(flag_name)
