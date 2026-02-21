"""Test suite for SIMPLE_VALIDATION.sh script."""

from __future__ import annotations

import subprocess
import pytest
from pathlib import Path
from typing import Any


class TestSimpleValidationScript:
    """Test the SIMPLE_VALIDATION.sh script functionality."""

    @pytest.fixture
    def script_path(self) -> Path:
        """Get the path to the validation script."""
        return Path(__file__).parent.parent / "SIMPLE_VALIDATION.sh"

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def test_script_exists(self, script_path: Path) -> None:
        """Test that the validation script exists."""
        assert script_path.exists(), "SIMPLE_VALIDATION.sh should exist"
        assert script_path.is_file(), "SIMPLE_VALIDATION.sh should be a file"

    def test_script_is_executable(self, script_path: Path) -> None:
        """Test that the validation script has execute permissions."""
        # Check if file is executable by checking mode
        assert script_path.stat().st_mode & 0o111, "Script should be executable"

    def test_script_runs_successfully(self, script_path: Path, project_root: Path) -> None:
        """Test that the validation script runs without errors."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Script should exit successfully
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_script_output_contains_headers(self, script_path: Path, project_root: Path) -> None:
        """Test that the script output contains expected section headers."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Check for key section headers
        assert "MCP Gateway Validation Script" in output
        assert "Project Structure Validation:" in output
        assert "Key Files Validation:" in output
        assert "RAG Implementation Validation:" in output
        assert "Configuration Validation:" in output
        assert "Docker Configuration Validation:" in output

    def test_script_validates_project_structure(
        self, script_path: Path, project_root: Path
    ) -> None:
        """Test that the script validates project structure."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Should check for key directories
        assert "tool_router" in output
        assert "tests" in output
        assert "directory" in output.lower()

    def test_script_validates_key_files(
        self, script_path: Path, project_root: Path
    ) -> None:
        """Test that the script validates key files exist."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Should check for key files
        expected_files = [
            "CHANGELOG.md",
            "PROJECT_CONTEXT.md",
            "Makefile",
            "requirements.txt",
        ]

        for file in expected_files:
            assert file in output, f"{file} should be checked by validation script"

    def test_script_validates_docker_config(
        self, script_path: Path, project_root: Path
    ) -> None:
        """Test that the script validates Docker configuration."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Should check Docker files
        assert "Docker Configuration Validation:" in output
        assert "docker-compose.yml" in output or "Dockerfile" in output

    def test_script_provides_summary(
        self, script_path: Path, project_root: Path
    ) -> None:
        """Test that the script provides a validation summary."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Should provide summary
        assert "Validation Summary:" in output or "Summary" in output
        assert "Project Status:" in output or "Status:" in output

    def test_script_shows_success_indicators(
        self, script_path: Path, project_root: Path
    ) -> None:
        """Test that the script uses success/failure indicators."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Should use emoji or text indicators
        has_indicators = "✅" in output or "❌" in output or "exists" in output.lower()
        assert has_indicators, "Script should show success/failure indicators"

    def test_script_handles_missing_directories_gracefully(
        self, script_path: Path, tmp_path: Path
    ) -> None:
        """Test that the script handles missing directories gracefully."""
        # Run in empty temporary directory
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Script should still run and report missing items
        # It may have non-zero exit, but should not crash
        assert result.stderr == "" or "not found" in result.stderr.lower()

    def test_script_provides_next_steps(
        self, script_path: Path, project_root: Path
    ) -> None:
        """Test that the script provides next steps or recommendations."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Should provide next steps or recommendations
        has_guidance = (
            "Next Steps:" in output
            or "Recommendation:" in output
            or "Manual Testing Commands:" in output
        )
        assert has_guidance, "Script should provide guidance or next steps"

    def test_script_checks_web_admin(
        self, script_path: Path, project_root: Path
    ) -> None:
        """Test that the script checks web admin application."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Should check web admin
        assert "Web Admin" in output or "web-admin" in output

    def test_script_performance(self, script_path: Path, project_root: Path) -> None:
        """Test that the script completes in reasonable time."""
        import time

        start_time = time.time()
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        duration = time.time() - start_time

        # Should complete in under 10 seconds
        assert duration < 10, f"Script took {duration}s, should be faster"
        assert result.returncode == 0

    def test_script_bash_syntax(self, script_path: Path) -> None:
        """Test that the script has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0, f"Bash syntax error: {result.stderr}"

    def test_script_contains_shebang(self, script_path: Path) -> None:
        """Test that the script contains a proper shebang."""
        with open(script_path, "r") as f:
            first_line = f.readline().strip()

        assert first_line.startswith("#!"), "Script should have a shebang"
        assert "bash" in first_line.lower(), "Script should use bash"

    def test_script_validates_virtual_environment(
        self, script_path: Path, project_root: Path
    ) -> None:
        """Test that the script checks for virtual environment."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Should check for venv
        assert ".venv" in output or "virtual" in output.lower()

    def test_script_validates_scripts_directory(
        self, script_path: Path, project_root: Path
    ) -> None:
        """Test that the script validates scripts directory."""
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Should check scripts directory
        assert "scripts" in output.lower()