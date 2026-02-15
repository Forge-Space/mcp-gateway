"""Shared pytest fixtures for API tests."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture
def temp_config_file(monkeypatch: MonkeyPatch) -> Iterator[Path]:
    """Create a temporary virtual-servers.txt file for testing.

    Args:
        monkeypatch: Pytest fixture for mocking/patching during tests.

    Yields:
        Path to the temporary virtual-servers.txt configuration file.
        The file contains test server configurations and is automatically
        cleaned up (along with any .bak backup files) after the test completes.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("# Test configuration\n")
        f.write("cursor-default|sequential-thinking,filesystem|true\n")
        f.write("cursor-search|tavily,brave-search|false\n")
        f.write("cursor-browser|playwright,puppeteer\n")  # No enabled flag
        temp_path = Path(f.name)

    # Mock the config file path
    def mock_get_file():
        return temp_path

    monkeypatch.setattr("tool_router.api.lifecycle.get_virtual_servers_file", mock_get_file)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)
    backup = temp_path.with_suffix(".txt.bak")
    backup.unlink(missing_ok=True)
