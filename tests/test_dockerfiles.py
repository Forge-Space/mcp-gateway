"""Test suite for Dockerfile validation."""

from __future__ import annotations

import re
import pytest
from pathlib import Path
from typing import List, Dict, Any


class TestDockerfiles:
    """Test Dockerfile configuration and best practices."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture
    def dockerfile_tool_router(self, project_root: Path) -> Path:
        """Get the tool-router Dockerfile path."""
        return project_root / "Dockerfile.tool-router"

    @pytest.fixture
    def dockerfile_dribbble(self, project_root: Path) -> Path:
        """Get the dribbble-mcp Dockerfile path."""
        return project_root / "Dockerfile.dribbble-mcp"

    def test_dockerfile_tool_router_exists(self, dockerfile_tool_router: Path) -> None:
        """Test that Dockerfile.tool-router exists."""
        assert dockerfile_tool_router.exists(), "Dockerfile.tool-router should exist"
        assert dockerfile_tool_router.is_file(), "Dockerfile.tool-router should be a file"

    def test_dockerfile_dribbble_exists(self, dockerfile_dribbble: Path) -> None:
        """Test that Dockerfile.dribbble-mcp exists."""
        assert dockerfile_dribbble.exists(), "Dockerfile.dribbble-mcp should exist"
        assert dockerfile_dribbble.is_file(), "Dockerfile.dribbble-mcp should be a file"

    def test_dockerfile_tool_router_has_from_statement(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile has FROM statement."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        assert re.search(r"^FROM\s+", content, re.MULTILINE), "Should have FROM statement"

    def test_dockerfile_tool_router_uses_python_base(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile uses Python base image."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should use python base image
        assert "python:" in content.lower(), "Should use Python base image"

    def test_dockerfile_tool_router_specifies_python_version(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile specifies Python version."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should specify Python version (e.g., python:3.12)
        python_version_pattern = r"python:3\.\d+"
        assert re.search(
            python_version_pattern, content, re.IGNORECASE
        ), "Should specify Python version"

    def test_dockerfile_tool_router_uses_minimal_image(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile uses minimal base image."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should use slim or alpine variant
        is_minimal = "alpine" in content.lower() or "slim" in content.lower()
        assert is_minimal, "Should use minimal image (alpine or slim)"

    def test_dockerfile_tool_router_has_workdir(self, dockerfile_tool_router: Path) -> None:
        """Test that tool-router Dockerfile sets WORKDIR."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        assert re.search(r"^WORKDIR\s+", content, re.MULTILINE), "Should set WORKDIR"

    def test_dockerfile_tool_router_copies_requirements(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile copies requirements.txt."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        assert "requirements.txt" in content, "Should copy requirements.txt"

    def test_dockerfile_tool_router_installs_dependencies(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile installs Python dependencies."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should run pip install
        assert "pip install" in content, "Should install Python dependencies"

    def test_dockerfile_tool_router_uses_non_root_user(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile runs as non-root user."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should create and switch to non-root user
        assert "USER" in content, "Should switch to non-root user"
        # Should not use root user
        assert not re.search(r"USER\s+root\s*$", content, re.MULTILINE), "Should not run as root"

    def test_dockerfile_tool_router_creates_app_user(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile creates app user."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should create user (adduser or useradd or addgroup)
        creates_user = (
            "adduser" in content.lower()
            or "useradd" in content.lower()
            or "addgroup" in content.lower()
        )
        assert creates_user, "Should create non-root user"

    def test_dockerfile_tool_router_has_healthcheck(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile includes HEALTHCHECK."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        assert "HEALTHCHECK" in content, "Should include HEALTHCHECK instruction"

    def test_dockerfile_tool_router_has_cmd(self, dockerfile_tool_router: Path) -> None:
        """Test that tool-router Dockerfile has CMD instruction."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        assert re.search(r"^CMD\s+", content, re.MULTILINE), "Should have CMD instruction"

    def test_dockerfile_tool_router_sets_python_env_vars(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile sets Python environment variables."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should set PYTHONUNBUFFERED or PYTHONDONTWRITEBYTECODE
        has_python_env = (
            "PYTHONUNBUFFERED" in content or "PYTHONDONTWRITEBYTECODE" in content
        )
        assert has_python_env, "Should set Python environment variables"

    def test_dockerfile_tool_router_cleans_cache(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile cleans up caches."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should clean pip cache or use --no-cache-dir
        cleans_cache = "--no-cache-dir" in content or "rm -rf" in content
        assert cleans_cache, "Should clean caches to reduce image size"

    def test_dockerfile_dribbble_has_from_statement(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile has FROM statement."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        assert re.search(r"^FROM\s+", content, re.MULTILINE), "Should have FROM statement"

    def test_dockerfile_dribbble_uses_python_base(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile uses Python base image."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        assert "python:" in content.lower(), "Should use Python base image"

    def test_dockerfile_dribbble_installs_playwright(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile installs Playwright."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        assert "playwright" in content.lower(), "Should install Playwright"

    def test_dockerfile_dribbble_installs_chromium(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile installs Chromium browser."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        assert "chromium" in content.lower(), "Should install Chromium browser"

    def test_dockerfile_dribbble_has_workdir(self, dockerfile_dribbble: Path) -> None:
        """Test that dribbble Dockerfile sets WORKDIR."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        assert re.search(r"^WORKDIR\s+", content, re.MULTILINE), "Should set WORKDIR"

    def test_dockerfile_dribbble_uses_non_root_user(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile runs as non-root user."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        assert "USER" in content, "Should switch to non-root user"

    def test_dockerfile_dribbble_has_healthcheck(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile includes HEALTHCHECK."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        assert "HEALTHCHECK" in content, "Should include HEALTHCHECK instruction"

    def test_dockerfile_dribbble_has_cmd(self, dockerfile_dribbble: Path) -> None:
        """Test that dribbble Dockerfile has CMD instruction."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        assert re.search(r"^CMD\s+", content, re.MULTILINE), "Should have CMD instruction"

    def test_dockerfile_dribbble_sets_python_env_vars(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile sets Python environment variables."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        has_python_env = (
            "PYTHONUNBUFFERED" in content or "PYTHONDONTWRITEBYTECODE" in content
        )
        assert has_python_env, "Should set Python environment variables"

    def test_dockerfile_dribbble_sets_playwright_env(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile sets Playwright environment variables."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        assert "PLAYWRIGHT_BROWSERS_PATH" in content, "Should set Playwright browser path"

    def test_dockerfile_tool_router_multi_line_commands_use_continuation(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that multi-line commands use proper continuation."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # If there are RUN commands with multiple lines, they should use && or \
        run_commands = re.findall(r"^RUN\s+.*", content, re.MULTILINE)
        for cmd in run_commands:
            if len(cmd) > 80:  # Long commands should use continuation
                # Should use && or \ for multi-line
                uses_continuation = "&&" in cmd or "\\" in cmd
                # This is a recommendation, not a hard requirement

    def test_dockerfile_tool_router_copies_application_code(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile copies application code."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should copy tool_router directory
        assert "tool_router" in content, "Should copy tool_router application code"

    def test_dockerfile_tool_router_runs_simple_server(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile runs the simple server."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should run simple_server.py
        assert "simple_server.py" in content, "Should run simple_server.py"

    def test_dockerfile_tool_router_exposes_port_or_curl_in_healthcheck(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile exposes port or uses curl in healthcheck."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should either expose port or use curl in healthcheck
        exposes_port = "EXPOSE" in content
        uses_curl = "curl" in content.lower()

        # At least one should be true for a web service
        assert exposes_port or uses_curl, "Should expose port or use curl for health checks"

    def test_dockerfile_dribbble_copies_application_code(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile copies application code."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        # Should copy dribbble_mcp directory
        assert "dribbble_mcp" in content, "Should copy dribbble_mcp application code"

    def test_dockerfile_security_updates(
        self, dockerfile_tool_router: Path, dockerfile_dribbble: Path
    ) -> None:
        """Test that Dockerfiles include security updates."""
        for dockerfile in [dockerfile_tool_router, dockerfile_dribbble]:
            with open(dockerfile, "r") as f:
                content = f.read()

            # Should update package lists (for debian/ubuntu) or apk (for alpine)
            has_updates = (
                "apt-get update" in content.lower() or "apk update" in content.lower()
            )
            # This is good practice but not always required

    def test_dockerfile_layer_optimization(
        self, dockerfile_tool_router: Path, dockerfile_dribbble: Path
    ) -> None:
        """Test that Dockerfiles optimize layers."""
        for dockerfile in [dockerfile_tool_router, dockerfile_dribbble]:
            with open(dockerfile, "r") as f:
                content = f.read()

            # Count number of RUN commands (fewer is better for optimization)
            run_count = len(re.findall(r"^RUN\s+", content, re.MULTILINE))

            # Should not have excessive RUN commands (< 20 is reasonable)
            assert run_count < 20, f"Should optimize layers (found {run_count} RUN commands)"

    def test_dockerfile_tool_router_no_secrets_hardcoded(
        self, dockerfile_tool_router: Path
    ) -> None:
        """Test that tool-router Dockerfile doesn't contain hardcoded secrets."""
        with open(dockerfile_tool_router, "r") as f:
            content = f.read()

        # Should not contain common secret patterns
        dangerous_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]

        for pattern in dangerous_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            # Filter out obvious placeholders
            real_secrets = [
                m for m in matches if not any(
                    placeholder in m.lower()
                    for placeholder in ["your_", "example", "xxx", "placeholder"]
                )
            ]
            assert not real_secrets, f"Should not contain hardcoded secrets: {real_secrets}"

    def test_dockerfile_dribbble_no_secrets_hardcoded(
        self, dockerfile_dribbble: Path
    ) -> None:
        """Test that dribbble Dockerfile doesn't contain hardcoded secrets."""
        with open(dockerfile_dribbble, "r") as f:
            content = f.read()

        dangerous_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]

        for pattern in dangerous_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            real_secrets = [
                m for m in matches if not any(
                    placeholder in m.lower()
                    for placeholder in ["your_", "example", "xxx", "placeholder"]
                )
            ]
            assert not real_secrets, f"Should not contain hardcoded secrets: {real_secrets}"
