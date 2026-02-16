"""Integration tests for feature toggle flow."""

from __future__ import annotations

from tool_router.core.features import FeatureFlags


class TestFeatureTogglesIntegration:
    """Integration tests for feature toggle system."""

    def test_feature_toggle_lifecycle(self, tmp_path):
        """Test complete feature toggle lifecycle."""
        config_file = tmp_path / "features.yaml"
        config_file.write_text("""
features:
  metrics:
    enabled: true
    category: observability
    description: Metrics collection
    requires_restart: false
  ai_routing:
    enabled: false
    category: ai
    description: AI-powered routing
    requires_restart: true
""")

        flags = FeatureFlags(config_file=config_file)
        flags._load_from_yaml()

        # Test initial state
        assert flags.is_enabled("metrics") is True
        assert flags.is_enabled("ai_routing") is False

        # Test toggle
        flags.update_feature("ai_routing", True)
        assert flags.is_enabled("ai_routing") is True

        # Test save and reload
        flags.save_to_yaml()
        new_flags = FeatureFlags(config_file=config_file)
        new_flags._load_from_yaml()
        assert new_flags.is_enabled("ai_routing") is True

    def test_feature_requires_restart_flag(self, tmp_path):
        """Test requires_restart flag is preserved."""
        config_file = tmp_path / "features.yaml"
        config_file.write_text("""
features:
  test_feature:
    enabled: false
    category: test
    description: Test
    requires_restart: true
""")

        flags = FeatureFlags(config_file=config_file)
        flags._load_from_yaml()
        feature = flags.get_feature("test_feature")

        assert feature is not None
        assert feature.requires_restart is True
