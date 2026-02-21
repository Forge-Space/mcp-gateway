"""Tests for dribbble_mcp.health_check module."""

from __future__ import annotations

import subprocess
import urllib.error
from unittest.mock import MagicMock, patch, call

import pytest

from dribbble_mcp.health_check import main


class TestHealthCheck:
    """Test cases for the health check functionality."""

    @patch('urllib.request.urlopen')
    def test_main_http_health_check_success(self, mock_urlopen):
        """Test successful HTTP health check."""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value = mock_response

        with patch('sys.exit') as mock_exit:
            main()
            # Should exit with 0 first (successful HTTP check), then 1 (function continues)
            assert mock_exit.call_args_list[0] == call(0)
            # Verify urlopen was called with correct URL
            mock_urlopen.assert_called_once_with('http://localhost:8035/health', timeout=5)

    @patch('urllib.request.urlopen')
    def test_main_http_health_check_failure(self, mock_urlopen):
        """Test HTTP health check failure falls back to process check."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")

        with patch('subprocess.run') as mock_run, patch('sys.exit') as mock_exit:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout.strip.return_value = "12345"
            mock_run.return_value = mock_result

            main()
            mock_exit.assert_called_once_with(0)

    @patch('urllib.request.urlopen')
    def test_main_http_health_check_non_200(self, mock_urlopen):
        """Test HTTP health check returns non-200 status falls back to process check."""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 500
        mock_urlopen.return_value = mock_response

        with patch('subprocess.run') as mock_run, patch('sys.exit') as mock_exit:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout.strip.return_value = "12345"
            mock_run.return_value = mock_result

            main()
            mock_exit.assert_called_once_with(0)

    @patch('urllib.request.urlopen')
    @patch('subprocess.run')
    def test_main_process_check_success(self, mock_run, mock_urlopen):
        """Test successful process health check."""
        mock_urlopen.side_effect = Exception("HTTP check failed")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout.strip.return_value = "12345"
        mock_run.return_value = mock_result

        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(0)
            mock_run.assert_called_once_with(
                ['pgrep', '-f', 'dribbble_mcp'],
                capture_output=True,
                text=True,
                timeout=5
            )

    @patch('urllib.request.urlopen')
    @patch('subprocess.run')
    def test_main_process_check_no_process(self, mock_run, mock_urlopen):
        """Test process health check when no process found."""
        mock_urlopen.side_effect = Exception("HTTP check failed")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout.strip.return_value = ""
        mock_run.return_value = mock_result

        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)

    @patch('urllib.request.urlopen')
    @patch('subprocess.run')
    def test_main_process_check_empty_output(self, mock_run, mock_urlopen):
        """Test process health check when process found but no output."""
        mock_urlopen.side_effect = Exception("HTTP check failed")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout.strip.return_value = ""
        mock_run.return_value = mock_result

        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)

    @patch('urllib.request.urlopen')
    @patch('subprocess.run')
    def test_main_process_check_exception(self, mock_run, mock_urlopen):
        """Test process health check when subprocess raises exception."""
        mock_urlopen.side_effect = Exception("HTTP check failed")
        mock_run.side_effect = subprocess.TimeoutExpired("pgrep", 5)

        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)

    @patch('urllib.request.urlopen')
    @patch('subprocess.run')
    def test_main_both_checks_fail(self, mock_run, mock_urlopen):
        """Test when both HTTP and process checks fail."""
        mock_urlopen.side_effect = Exception("HTTP check failed")
        mock_run.side_effect = Exception("Process check failed")

        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)

    @patch('urllib.request.urlopen')
    def test_main_http_check_timeout(self, mock_urlopen):
        """Test HTTP health check timeout."""
        mock_urlopen.side_effect = urllib.error.URLError("timeout")

        with patch('subprocess.run') as mock_run, patch('sys.exit') as mock_exit:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout.strip.return_value = "12345"
            mock_run.return_value = mock_result

            main()
            mock_exit.assert_called_once_with(0)

    @patch('urllib.request.urlopen')
    @patch('subprocess.run')
    def test_main_process_check_with_timeout(self, mock_run, mock_urlopen):
        """Test process check with timeout parameter."""
        mock_urlopen.side_effect = Exception("HTTP check failed")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout.strip.return_value = "12345"
        mock_run.return_value = mock_result

        with patch('sys.exit') as mock_exit:
            main()
            mock_run.assert_called_once_with(
                ['pgrep', '-f', 'dribbble_mcp'],
                capture_output=True,
                text=True,
                timeout=5
            )
            mock_exit.assert_called_once_with(0)
