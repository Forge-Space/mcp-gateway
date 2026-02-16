"""Unit tests for core feature flags system."""

from __future__ import annotations

from tool_router.core.features import FeatureFlags


class TestFeatureFlags:
    """Tests for FeatureFlags manager."""

    def test_load_from_yaml_success(self, tmp_path):
        """Test loading features from YAML file."""
        config_file = tmp_path / "features.yaml"
        config_file.write_text("""
features:
  feature1:
    enabled: true
    category: core
    description: First feature
""")

        flags = FeatureFlags(config_file=config_file)
        flags._load_from_yaml()

        assert flags.is_enabled("feature1") is True

    def test_load_from_yaml_missing_file(self, tmp_path):
        """Test loading when YAML file doesn't exist."""
        config_file = tmp_path / "nonexistent.yaml"
        flags = FeatureFlags(config_file=config_file)
        flags._load_from_yaml()
        assert len(flags.features) == 0

    def test_load_from_environment(self, tmp_path, monkeypatch):
        """Test environment variable override."""
        config_file = tmp_path / "features.yaml"
        config_file.write_text("""
features:
  test_feature:
    enabled: false
    category: test
    description: Test
    env_var: TEST_FEATURE_ENABLED
""")

        monkeypatch.setenv("TEST_FEATURE_ENABLED", "true")
        flags = FeatureFlags(config_file=config_file)
        flags._load_from_yaml()
        flags._load_from_environment()

        assert flags.is_enabled("test_feature") is True

    def test_get_features_by_category(self, tmp_path):
        """Test filtering features by category."""
        config_file = tmp_path / "features.yaml"
        config_file.write_text("""
features:
  core_feature:
    enabled: true
    category: core
    description: Core
  api_feature:
    enabled: true
    category: api
    description: API
""")

        flags = FeatureFlags(config_file=config_file)
        flags._load_from_yaml()

        core_features = flags.get_features_by_category("core")
        assert len(core_features) == 1

    def test_update_feature_success(self, tmp_path):
        """Test updating feature state."""
        config_file = tmp_path / "features.yaml"
        config_file.write_text("""
features:
  test:
    enabled: false
    category: test
    description: Test
""")

        flags = FeatureFlags(config_file=config_file)
        flags._load_from_yaml()

        result = flags.update_feature("test", True)
        assert result is True
        assert flags.is_enabled("test") is True

    def test_update_feature_nonexistent(self):
        """Test updating nonexistent feature."""
        flags = FeatureFlags()
        result = flags.update_feature("nonexistent", True)
        assert result is False

    def test_save_to_yaml(self, tmp_path):
        """Test saving features to YAML."""
        config_file = tmp_path / "features.yaml"
        config_file.write_text("""
features:
  test:
    enabled: false
    category: test
    description: Test
""")

        flags = FeatureFlags(config_file=config_file)
        flags._load_from_yaml()
        flags.update_feature("test", True)
        flags.save_to_yaml()

        # Reload and verify
        new_flags = FeatureFlags(config_file=config_file)
        new_flags._load_from_yaml()
        assert new_flags.is_enabled("test") is True
