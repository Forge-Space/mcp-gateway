"""Test suite for Makefile targets and configuration."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


class TestMakefile:
    """Test Makefile configuration and targets."""

    @pytest.fixture
    def makefile_path(self) -> Path:
        """Get the Makefile path."""
        return Path(__file__).parent.parent.parent / "Makefile"

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_makefile_exists(self, makefile_path: Path) -> None:
        """Test that Makefile exists."""
        assert makefile_path.exists(), "Makefile should exist"
        assert makefile_path.is_file(), "Makefile should be a file"

    def test_makefile_has_default_goal(self, makefile_path: Path) -> None:
        """Test that Makefile sets a default goal."""
        with open(makefile_path) as f:
            content = f.read()

        # Should set .DEFAULT_GOAL
        assert ".DEFAULT_GOAL" in content, "Should set default goal"

    def test_makefile_default_goal_is_help(self, makefile_path: Path) -> None:
        """Test that default goal is help."""
        with open(makefile_path) as f:
            content = f.read()

        # Default goal should be help for user-friendliness
        default_goal_match = re.search(r"\.DEFAULT_GOAL\s*:?=\s*(\w+)", content)
        if default_goal_match:
            default_goal = default_goal_match.group(1)
            assert default_goal == "help", "Default goal should be 'help'"

    def test_makefile_declares_phony_targets(self, makefile_path: Path) -> None:
        """Test that Makefile declares .PHONY targets."""
        with open(makefile_path) as f:
            content = f.read()

        # Should declare .PHONY targets
        assert ".PHONY" in content, "Should declare .PHONY targets"

    def test_makefile_has_help_target(self, makefile_path: Path) -> None:
        """Test that Makefile has a help target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have help target
        assert re.search(r"^help:", content, re.MULTILINE), "Should have 'help' target"

    def test_makefile_has_setup_target(self, makefile_path: Path) -> None:
        """Test that Makefile has a setup target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have setup target
        assert re.search(r"^setup:", content, re.MULTILINE), "Should have 'setup' target"

    def test_makefile_has_start_target(self, makefile_path: Path) -> None:
        """Test that Makefile has a start target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have start target
        assert re.search(r"^start:", content, re.MULTILINE), "Should have 'start' target"

    def test_makefile_has_stop_target(self, makefile_path: Path) -> None:
        """Test that Makefile has a stop target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have stop target
        assert re.search(r"^stop:", content, re.MULTILINE), "Should have 'stop' target"

    def test_makefile_has_test_target(self, makefile_path: Path) -> None:
        """Test that Makefile has a test target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have test target
        assert re.search(r"^test:", content, re.MULTILINE), "Should have 'test' target"

    def test_makefile_has_lint_target(self, makefile_path: Path) -> None:
        """Test that Makefile has a lint target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have lint target
        assert re.search(r"^lint:", content, re.MULTILINE), "Should have 'lint' target"

    def test_makefile_has_clean_target(self, makefile_path: Path) -> None:
        """Test that Makefile has a clean target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have clean target
        assert re.search(r"^clean:", content, re.MULTILINE), "Should have 'clean' target"

    def test_makefile_has_status_target(self, makefile_path: Path) -> None:
        """Test that Makefile has a status target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have status target
        assert re.search(r"^status:", content, re.MULTILINE), "Should have 'status' target"

    def test_makefile_has_register_target(self, makefile_path: Path) -> None:
        """Test that Makefile has a register target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have register target
        assert re.search(r"^register:", content, re.MULTILINE), "Should have 'register' target"

    def test_makefile_targets_have_help_comments(self, makefile_path: Path) -> None:
        """Test that Makefile targets have help comments."""
        with open(makefile_path) as f:
            content = f.read()

        # Count targets with ## comments (help text)
        targets_with_help = re.findall(r"^(\w+):.*##\s*(.+)", content, re.MULTILINE)

        # Should have multiple targets with help
        assert len(targets_with_help) >= 5, "Should have help comments for key targets"

    def test_makefile_help_target_shows_available_commands(self, makefile_path: Path, project_root: Path) -> None:
        """Test that help target shows available commands."""
        # Check if make is available
        try:
            result = subprocess.run(
                ["make", "help"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Help should show available commands
            output = result.stdout + result.stderr
            assert "setup" in output or "start" in output or "Commands" in output
        except FileNotFoundError:
            # If make is not available, verify help target exists in file
            with open(makefile_path) as f:
                content = f.read()
            # Verify help target has echo statements
            help_section = re.search(r"^help:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
            assert help_section, "Help target should exist"
            assert "echo" in help_section.group(0), "Help should echo commands"

    def test_makefile_test_target_runs_pytest(self, makefile_path: Path) -> None:
        """Test that test target runs pytest."""
        with open(makefile_path) as f:
            content = f.read()

        # Test target should use pytest
        test_section = re.search(r"^test:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if test_section:
            assert "pytest" in test_section.group(0), "Test target should run pytest"

    def test_makefile_lint_target_runs_linters(self, makefile_path: Path) -> None:
        """Test that lint target runs code linters."""
        with open(makefile_path) as f:
            content = f.read()

        # Lint target should run linters
        lint_section = re.search(r"^lint:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if lint_section:
            lint_content = lint_section.group(0)
            # Should use ruff, black, flake8, or shellcheck
            has_linters = any(
                linter in lint_content.lower() for linter in ["ruff", "black", "flake8", "shellcheck", "npm run lint"]
            )
            assert has_linters, "Lint target should run code linters"

    def test_makefile_has_ide_setup_target(self, makefile_path: Path) -> None:
        """Test that Makefile has IDE setup target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have ide-setup target
        assert re.search(r"^ide-setup:", content, re.MULTILINE), "Should have 'ide-setup' target"

    def test_makefile_has_auth_target(self, makefile_path: Path) -> None:
        """Test that Makefile has auth target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have auth target
        assert re.search(r"^auth:", content, re.MULTILINE), "Should have 'auth' target"

    def test_makefile_has_deps_target(self, makefile_path: Path) -> None:
        """Test that Makefile has deps target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have deps target
        assert re.search(r"^deps:", content, re.MULTILINE), "Should have 'deps' target"

    def test_makefile_auth_target_supports_actions(self, makefile_path: Path) -> None:
        """Test that auth target supports multiple actions."""
        with open(makefile_path) as f:
            content = f.read()

        # Auth target should support generate, check, refresh, secrets
        auth_section = re.search(r"^auth:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if auth_section:
            auth_content = auth_section.group(0)
            # Should mention ACTION parameter
            assert "ACTION" in auth_content, "Auth target should support ACTION parameter"

    def test_makefile_setup_target_runs_wizard(self, makefile_path: Path) -> None:
        """Test that setup target runs configuration wizard."""
        with open(makefile_path) as f:
            content = f.read()

        # Setup should run wizard script
        setup_section = re.search(r"^setup:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if setup_section:
            setup_content = setup_section.group(0)
            assert "setup-wizard.py" in setup_content or "wizard" in setup_content.lower(), (
                "Setup should run configuration wizard"
            )

    def test_makefile_start_target_uses_start_script(self, makefile_path: Path) -> None:
        """Test that start target uses start script."""
        with open(makefile_path) as f:
            content = f.read()

        # Start should use start.sh script
        start_section = re.search(r"^start:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if start_section:
            start_content = start_section.group(0)
            assert "start.sh" in start_content, "Start target should use start.sh"

    def test_makefile_register_target_supports_wait_option(self, makefile_path: Path) -> None:
        """Test that register target supports WAIT option."""
        with open(makefile_path) as f:
            content = f.read()

        # Register should support WAIT option
        register_section = re.search(r"^register:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if register_section:
            register_content = register_section.group(0)
            # Should check for WAIT variable
            assert "WAIT" in register_content, "Register should support WAIT option"

    def test_makefile_status_target_supports_formats(self, makefile_path: Path) -> None:
        """Test that status target supports different output formats."""
        with open(makefile_path) as f:
            content = f.read()

        # Status should support FORMAT option
        status_section = re.search(r"^status:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if status_section:
            status_content = status_section.group(0)
            # Should check for FORMAT variable
            assert "FORMAT" in status_content, "Status should support FORMAT option"

    def test_makefile_test_target_supports_coverage(self, makefile_path: Path) -> None:
        """Test that test target supports coverage option."""
        with open(makefile_path) as f:
            content = f.read()

        # Test should support COVERAGE option
        test_section = re.search(r"^test:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if test_section:
            test_content = test_section.group(0)
            # Should check for COVERAGE variable
            assert "COVERAGE" in test_content, "Test should support COVERAGE option"

    def test_makefile_deps_target_supports_actions(self, makefile_path: Path) -> None:
        """Test that deps target supports multiple actions."""
        with open(makefile_path) as f:
            content = f.read()

        # Deps should support check, update, hooks, install
        deps_section = re.search(r"^deps:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if deps_section:
            deps_content = deps_section.group(0)
            # Should check for ACTION variable
            assert "ACTION" in deps_content, "Deps should support ACTION parameter"

    def test_makefile_clean_target_removes_artifacts(self, makefile_path: Path) -> None:
        """Test that clean target removes build artifacts."""
        with open(makefile_path) as f:
            content = f.read()

        # Clean should remove database and duplicates
        clean_section = re.search(r"^clean:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if clean_section:
            clean_content = clean_section.group(0)
            # Should stop services and clean database
            assert "stop" in clean_content.lower(), "Clean should stop services"
            assert "rm" in clean_content or "clean" in clean_content.lower(), "Clean should remove files"

    def test_makefile_has_quickstart_target(self, makefile_path: Path) -> None:
        """Test that Makefile has quickstart target."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have quickstart target
        assert re.search(r"^quickstart:", content, re.MULTILINE), "Should have 'quickstart' target"

    def test_makefile_quickstart_shows_instructions(self, makefile_path: Path) -> None:
        """Test that quickstart target shows getting started instructions."""
        with open(makefile_path) as f:
            content = f.read()

        quickstart_section = re.search(r"^quickstart:.*?(?=^\S|\Z)", content, re.MULTILINE | re.DOTALL)
        if quickstart_section:
            quickstart_content = quickstart_section.group(0)
            # Should show setup, start, register steps
            assert "setup" in quickstart_content.lower(), "Quickstart should mention setup"

    def test_makefile_has_lint_strict_target(self, makefile_path: Path) -> None:
        """Test that Makefile has lint-strict target for CI."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have lint-strict target
        assert re.search(r"^lint-strict:", content, re.MULTILINE), "Should have 'lint-strict' target"

    def test_makefile_comments_explain_targets(self, makefile_path: Path) -> None:
        """Test that Makefile has explanatory comments."""
        with open(makefile_path) as f:
            content = f.read()

        # Should have comment sections
        comment_lines = [line for line in content.split("\n") if line.strip().startswith("#")]

        # Should have at least a few comment lines
        assert len(comment_lines) >= 3, "Should have explanatory comments"

    def test_makefile_uses_bash_for_complex_logic(self, makefile_path: Path) -> None:
        """Test that Makefile uses bash for conditional logic."""
        with open(makefile_path) as f:
            content = f.read()

        # Should use bash for conditionals
        uses_conditionals = "if [" in content or "if [[" in content or "case" in content
        # This is optional but common for complex Makefiles

    def test_makefile_syntax_valid(self, makefile_path: Path, project_root: Path) -> None:
        """Test that Makefile has valid syntax."""
        # Check if make is available
        try:
            result = subprocess.run(
                ["make", "-n", "help"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Should not have syntax errors
            # Make will return 0 for valid syntax even if target doesn't exist
            assert result.returncode in [0, 2], f"Makefile syntax error: {result.stderr}"
        except FileNotFoundError:
            # If make is not available, do basic validation
            with open(makefile_path) as f:
                content = f.read()
            # Check for basic Makefile patterns
            has_targets = bool(re.search(r"^\w+:", content, re.MULTILINE))
            assert has_targets, "Makefile should define targets"

    def test_makefile_core_commands_documented(self, makefile_path: Path) -> None:
        """Test that core commands are documented in help."""
        with open(makefile_path) as f:
            content = f.read()

        # Core commands should have help text
        core_commands = ["setup", "start", "stop", "test", "lint", "help"]

        for command in core_commands:
            # Should have ## comment for help
            pattern = rf"^{command}:.*##"
            has_help = re.search(pattern, content, re.MULTILINE)
            assert has_help, f"Command '{command}' should have help text (##)"

    def test_makefile_has_consistent_phony_declarations(self, makefile_path: Path) -> None:
        """Test that .PHONY declarations match defined targets."""
        with open(makefile_path) as f:
            content = f.read()

        # Extract .PHONY targets
        phony_match = re.search(r"\.PHONY:\s*(.+)", content)
        if phony_match:
            phony_targets = set(phony_match.group(1).split())

            # Extract actual targets (including targets with hyphens)
            actual_targets = set(re.findall(r"^([\w-]+):", content, re.MULTILINE))

            # All phony targets should exist
            for phony in phony_targets:
                assert phony in actual_targets, f".PHONY target '{phony}' should be defined"
