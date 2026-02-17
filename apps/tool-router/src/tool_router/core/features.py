"""Feature toggle system for MCP Gateway.

This module provides a centralized feature flag system with:
- YAML configuration backend
- Environment variable overrides
- Runtime feature checking
- Web UI management support

Naming Convention: FEATURE_<CATEGORY>_<NAME>
Categories: CORE, API, TOOL, UI, SECURITY, OBSERVABILITY
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class Feature:
    """Individual feature toggle configuration."""

    name: str
    enabled: bool
    description: str
    category: str
    requires_restart: bool = False
    env_var: Optional[str] = None
    backward_compat: Optional[str] = None


@dataclass
class FeatureFlags:
    """Feature flags configuration manager."""

    features: dict[str, Feature] = field(default_factory=dict)
    config_file: Path = field(
        default_factory=lambda: Path(__file__).parent.parent.parent
        / "config"
        / "features.yaml"
    )

    @classmethod
    def load(cls) -> "FeatureFlags":
        """Load feature flags from YAML and environment variables.

        Precedence: ENV vars > YAML file > defaults
        """
        instance = cls()
        instance._load_from_yaml()
        instance._load_from_environment()
        return instance

    def _load_from_yaml(self) -> None:
        """Load feature flags from YAML configuration file."""
        if not self.config_file.exists():
            # Use defaults if config file doesn't exist
            return

        try:
            with open(self.config_file) as f:
                config = yaml.safe_load(f)

            if not config or "features" not in config:
                return

            for name, feature_config in config["features"].items():
                self.features[name] = Feature(
                    name=name,
                    enabled=feature_config.get("enabled", True),
                    description=feature_config.get("description", ""),
                    category=feature_config.get("category", "unknown"),
                    requires_restart=feature_config.get("requires_restart", False),
                    env_var=feature_config.get("env_var"),
                    backward_compat=feature_config.get("backward_compat"),
                )
        except Exception:
            # Log error but don't fail - use defaults
            pass

    def _load_from_environment(self) -> None:
        """Override feature flags from environment variables."""
        for feature in self.features.values():
            # Check primary env var
            if feature.env_var:
                env_value = os.getenv(feature.env_var)
                if env_value is not None:
                    feature.enabled = env_value.lower() in ("true", "1", "yes")

            # Check backward compatibility env var
            if feature.backward_compat:
                compat_value = os.getenv(feature.backward_compat)
                if compat_value is not None:
                    feature.enabled = compat_value.lower() in ("true", "1", "yes")

    def is_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled.

        Args:
            feature_name: Name of the feature (e.g., "core_ai_router")

        Returns:
            True if feature is enabled, False otherwise (defaults to False)
        """
        feature = self.features.get(feature_name)
        return feature.enabled if feature else False

    def get_feature(self, feature_name: str) -> Optional[Feature]:
        """Get feature configuration by name.

        Args:
            feature_name: Name of the feature

        Returns:
            Feature object or None if not found
        """
        return self.features.get(feature_name)

    def get_all_features(self) -> dict[str, Feature]:
        """Get all feature configurations.

        Returns:
            Dictionary of feature name to Feature object
        """
        return self.features.copy()

    def get_features_by_category(self, category: str) -> dict[str, Feature]:
        """Get all features in a specific category.

        Args:
            category: Category name (e.g., "core", "api", "tool", "ui")

        Returns:
            Dictionary of feature name to Feature object
        """
        return {
            name: feature
            for name, feature in self.features.items()
            if feature.category == category
        }

    def update_feature(self, feature_name: str, enabled: bool) -> bool:
        """Update a feature's enabled state.

        Args:
            feature_name: Name of the feature
            enabled: New enabled state

        Returns:
            True if update successful, False otherwise
        """
        feature = self.features.get(feature_name)
        if not feature:
            return False

        feature.enabled = enabled
        return True

    def save_to_yaml(self) -> bool:
        """Save current feature flags to YAML configuration file.

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Build YAML structure
            config = {
                "version": "1.0",
                "features": {},
            }

            for name, feature in self.features.items():
                feature_dict: dict[str, Any] = {
                    "enabled": feature.enabled,
                    "description": feature.description,
                    "category": feature.category,
                    "requires_restart": feature.requires_restart,
                    "env_var": feature.env_var,
                }

                if feature.backward_compat:
                    feature_dict["backward_compat"] = feature.backward_compat

                config["features"][name] = feature_dict

            # Write to file
            with open(self.config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            return True
        except Exception:
            return False

    def to_dict(self) -> dict[str, Any]:
        """Convert feature flags to dictionary for API responses.

        Returns:
            Dictionary representation of all features
        """
        return {
            name: {
                "enabled": feature.enabled,
                "description": feature.description,
                "category": feature.category,
                "requires_restart": feature.requires_restart,
                "env_var": feature.env_var,
                "backward_compat": feature.backward_compat,
            }
            for name, feature in self.features.items()
        }


# Global instance for application-wide access
_feature_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """Get the global feature flags instance.

    Returns:
        FeatureFlags instance (singleton)
    """
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags.load()
    return _feature_flags


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled (convenience function).

    Args:
        feature_name: Name of the feature

    Returns:
        True if feature is enabled, False otherwise
    """
    return get_feature_flags().is_enabled(feature_name)


def reload_feature_flags() -> FeatureFlags:
    """Reload feature flags from configuration.

    Returns:
        New FeatureFlags instance
    """
    global _feature_flags
    _feature_flags = FeatureFlags.load()
    return _feature_flags
