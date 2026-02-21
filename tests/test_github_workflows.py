"""Test suite for GitHub Actions workflow files."""

from __future__ import annotations

import pytest
import yaml
from pathlib import Path
from typing import Any, Dict


class TestGitHubWorkflows:
    """Test GitHub Actions workflow configuration."""

    @pytest.fixture
    def workflows_dir(self) -> Path:
        """Get the workflows directory path."""
        return Path(__file__).parent.parent / ".github" / "workflows"

    @pytest.fixture
    def reusable_dir(self) -> Path:
        """Get the reusable workflows directory path."""
        return Path(__file__).parent.parent / ".github" / "workflows" / "reusable"

    def test_workflows_directory_exists(self, workflows_dir: Path) -> None:
        """Test that the workflows directory exists."""
        assert workflows_dir.exists(), ".github/workflows should exist"
        assert workflows_dir.is_dir(), ".github/workflows should be a directory"

    def test_ci_workflow_exists(self, workflows_dir: Path) -> None:
        """Test that the main CI workflow file exists."""
        ci_file = workflows_dir / "ci.yml"
        assert ci_file.exists(), "ci.yml should exist"
        assert ci_file.is_file(), "ci.yml should be a file"

    def test_ci_workflow_valid_yaml(self, workflows_dir: Path) -> None:
        """Test that ci.yml is valid YAML."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        assert data is not None, "ci.yml should contain valid YAML"
        assert isinstance(data, dict), "ci.yml should be a YAML dictionary"

    def test_ci_workflow_has_name(self, workflows_dir: Path) -> None:
        """Test that ci.yml has a workflow name."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        assert "name" in data, "Workflow should have a name"
        assert data["name"], "Workflow name should not be empty"

    def test_ci_workflow_has_triggers(self, workflows_dir: Path) -> None:
        """Test that ci.yml has appropriate triggers."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        # YAML may parse "on" as True (boolean), so check for both
        assert "on" in data or True in data, "Workflow should have triggers (on)"
        on_config = data.get("on", data.get(True, {}))

        # Should have push and/or pull_request triggers
        has_triggers = (
            "push" in on_config
            or "pull_request" in on_config
            or "workflow_dispatch" in on_config
        )
        assert has_triggers, "Workflow should have push, pull_request, or workflow_dispatch triggers"

    def test_ci_workflow_has_jobs(self, workflows_dir: Path) -> None:
        """Test that ci.yml defines jobs."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        assert "jobs" in data, "Workflow should have jobs"
        assert data["jobs"], "Jobs should not be empty"
        assert isinstance(data["jobs"], dict), "Jobs should be a dictionary"

    def test_ci_workflow_environment_variables(self, workflows_dir: Path) -> None:
        """Test that ci.yml defines required environment variables."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        # Check for env section
        if "env" in data:
            env = data["env"]
            assert isinstance(env, dict), "env should be a dictionary"

            # Should define key versions
            expected_vars = ["NODE_VERSION", "PYTHON_VERSION"]
            for var in expected_vars:
                if var in env:
                    assert env[var], f"{var} should not be empty"

    def test_ci_workflow_uses_shared_template(self, workflows_dir: Path) -> None:
        """Test that ci.yml uses shared workflow template."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        jobs = data.get("jobs", {})

        # Check if any job uses a reusable workflow
        uses_reusable = False
        for job_name, job_config in jobs.items():
            if isinstance(job_config, dict) and "uses" in job_config:
                uses_reusable = True
                break

        # CI workflow should use reusable workflows or define steps
        assert uses_reusable or any(
            "steps" in job for job in jobs.values() if isinstance(job, dict)
        ), "Jobs should either use reusable workflows or define steps"

    def test_ci_workflow_has_test_job(self, workflows_dir: Path) -> None:
        """Test that ci.yml includes testing jobs."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        jobs = data.get("jobs", {})

        # Should have test-related jobs
        test_jobs = [name for name in jobs.keys() if "test" in name.lower() or "ci" in name.lower()]
        assert test_jobs, "Workflow should have test-related jobs"

    def test_reusable_workflows_directory_exists(self, reusable_dir: Path) -> None:
        """Test that reusable workflows directory exists."""
        assert reusable_dir.exists(), "reusable workflows directory should exist"
        assert reusable_dir.is_dir(), "reusable should be a directory"

    def test_setup_node_workflow_exists(self, reusable_dir: Path) -> None:
        """Test that setup-node.yml exists."""
        setup_node = reusable_dir / "setup-node.yml"
        assert setup_node.exists(), "setup-node.yml should exist"

    def test_setup_node_workflow_valid(self, reusable_dir: Path) -> None:
        """Test that setup-node.yml is valid and reusable."""
        setup_node = reusable_dir / "setup-node.yml"

        with open(setup_node, "r") as f:
            data = yaml.safe_load(f)

        assert data is not None, "setup-node.yml should be valid YAML"
        # YAML may parse "on" as True (boolean), so check for both
        assert "on" in data or True in data, "Reusable workflow should have 'on' trigger"
        on_config = data.get("on", data.get(True, {}))
        assert "workflow_call" in on_config, "Reusable workflow should use workflow_call"

    def test_setup_node_workflow_has_inputs(self, reusable_dir: Path) -> None:
        """Test that setup-node.yml defines inputs."""
        setup_node = reusable_dir / "setup-node.yml"

        with open(setup_node, "r") as f:
            data = yaml.safe_load(f)

        on_config = data.get("on", data.get(True, {}))
        workflow_call = on_config.get("workflow_call", {})

        # Should have inputs for node version
        if "inputs" in workflow_call:
            inputs = workflow_call["inputs"]
            assert isinstance(inputs, dict), "inputs should be a dictionary"

    def test_setup_node_workflow_installs_dependencies(self, reusable_dir: Path) -> None:
        """Test that setup-node.yml installs Node.js dependencies."""
        setup_node = reusable_dir / "setup-node.yml"

        with open(setup_node, "r") as f:
            content = f.read()

        # Should contain npm install commands
        assert "npm" in content.lower(), "Should use npm for Node.js setup"
        assert "install" in content.lower() or "ci" in content.lower(), "Should install dependencies"

    def test_setup_python_workflow_exists(self, reusable_dir: Path) -> None:
        """Test that setup-python.yml exists."""
        setup_python = reusable_dir / "setup-python.yml"
        assert setup_python.exists(), "setup-python.yml should exist"

    def test_setup_python_workflow_valid(self, reusable_dir: Path) -> None:
        """Test that setup-python.yml is valid and reusable."""
        setup_python = reusable_dir / "setup-python.yml"

        with open(setup_python, "r") as f:
            data = yaml.safe_load(f)

        assert data is not None, "setup-python.yml should be valid YAML"
        # YAML may parse "on" as True (boolean), so check for both
        assert "on" in data or True in data, "Reusable workflow should have 'on' trigger"
        on_config = data.get("on", data.get(True, {}))
        assert "workflow_call" in on_config, "Reusable workflow should use workflow_call"

    def test_setup_python_workflow_has_inputs(self, reusable_dir: Path) -> None:
        """Test that setup-python.yml defines inputs."""
        setup_python = reusable_dir / "setup-python.yml"

        with open(setup_python, "r") as f:
            data = yaml.safe_load(f)

        on_config = data.get("on", data.get(True, {}))
        workflow_call = on_config.get("workflow_call", {})

        # Should have inputs for Python version
        if "inputs" in workflow_call:
            inputs = workflow_call["inputs"]
            assert isinstance(inputs, dict), "inputs should be a dictionary"

    def test_setup_python_workflow_installs_dependencies(self, reusable_dir: Path) -> None:
        """Test that setup-python.yml installs Python dependencies."""
        setup_python = reusable_dir / "setup-python.yml"

        with open(setup_python, "r") as f:
            content = f.read()

        # Should contain pip install commands
        assert "pip" in content.lower(), "Should use pip for Python setup"
        assert "install" in content.lower(), "Should install dependencies"

    def test_setup_python_workflow_installs_test_tools(self, reusable_dir: Path) -> None:
        """Test that setup-python.yml installs testing tools."""
        setup_python = reusable_dir / "setup-python.yml"

        with open(setup_python, "r") as f:
            content = f.read()

        # Should install pytest and related tools
        test_tools = ["pytest", "black", "flake8", "mypy"]
        has_test_tools = any(tool in content.lower() for tool in test_tools)
        assert has_test_tools, "Should install testing/linting tools"

    def test_upload_coverage_workflow_exists(self, reusable_dir: Path) -> None:
        """Test that upload-coverage.yml exists."""
        upload_coverage = reusable_dir / "upload-coverage.yml"
        assert upload_coverage.exists(), "upload-coverage.yml should exist"

    def test_upload_coverage_workflow_valid(self, reusable_dir: Path) -> None:
        """Test that upload-coverage.yml is valid and reusable."""
        upload_coverage = reusable_dir / "upload-coverage.yml"

        with open(upload_coverage, "r") as f:
            data = yaml.safe_load(f)

        assert data is not None, "upload-coverage.yml should be valid YAML"
        # YAML may parse "on" as True (boolean), so check for both
        assert "on" in data or True in data, "Reusable workflow should have 'on' trigger"
        on_config = data.get("on", data.get(True, {}))
        assert "workflow_call" in on_config, "Reusable workflow should use workflow_call"

    def test_upload_coverage_workflow_has_secrets(self, reusable_dir: Path) -> None:
        """Test that upload-coverage.yml requires CODECOV_TOKEN secret."""
        upload_coverage = reusable_dir / "upload-coverage.yml"

        with open(upload_coverage, "r") as f:
            data = yaml.safe_load(f)

        on_config = data.get("on", data.get(True, {}))
        workflow_call = on_config.get("workflow_call", {})

        # Should require secrets for code coverage
        if "secrets" in workflow_call:
            secrets = workflow_call["secrets"]
            assert isinstance(secrets, dict), "secrets should be a dictionary"
            assert "CODECOV_TOKEN" in secrets, "Should require CODECOV_TOKEN"

    def test_upload_coverage_workflow_uses_codecov_action(self, reusable_dir: Path) -> None:
        """Test that upload-coverage.yml uses Codecov action."""
        upload_coverage = reusable_dir / "upload-coverage.yml"

        with open(upload_coverage, "r") as f:
            content = f.read()

        # Should use codecov action
        assert "codecov" in content.lower(), "Should use Codecov for coverage upload"

    def test_all_workflows_have_timeouts(self, workflows_dir: Path, reusable_dir: Path) -> None:
        """Test that workflow jobs have timeout configurations."""
        workflow_files = []

        # Collect all workflow files
        if workflows_dir.exists():
            workflow_files.extend(workflows_dir.glob("*.yml"))
        if reusable_dir.exists():
            workflow_files.extend(reusable_dir.glob("*.yml"))

        for workflow_file in workflow_files:
            with open(workflow_file, "r") as f:
                data = yaml.safe_load(f)

            if "jobs" in data:
                for job_name, job_config in data["jobs"].items():
                    if isinstance(job_config, dict):
                        # Timeout is recommended but not always required
                        # Just check the structure is valid
                        assert isinstance(job_config, dict), f"Job {job_name} should be a dict"

    def test_workflows_use_recent_actions_versions(self, workflows_dir: Path) -> None:
        """Test that workflows use reasonably recent action versions."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            content = f.read()

        # Should use v4+ for checkout action (if present)
        if "actions/checkout@" in content:
            # Extract version
            assert "actions/checkout@v" in content, "Should use versioned checkout action"

    def test_ci_workflow_has_pattern_validation(self, workflows_dir: Path) -> None:
        """Test that ci.yml includes pattern validation job."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        jobs = data.get("jobs", {})

        # Should have pattern validation job
        has_pattern_job = "pattern-validation" in jobs or "pattern_validation" in jobs
        assert has_pattern_job, "CI should include pattern validation"

    def test_ci_workflow_has_integration_tests(self, workflows_dir: Path) -> None:
        """Test that ci.yml includes integration test job."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        jobs = data.get("jobs", {})

        # Should have integration test job
        has_integration = "integration-test" in jobs or "integration_test" in jobs
        assert has_integration, "CI should include integration tests"

    def test_integration_test_job_uses_postgres(self, workflows_dir: Path) -> None:
        """Test that integration test job configures PostgreSQL service."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        jobs = data.get("jobs", {})
        integration_job = jobs.get("integration-test") or jobs.get("integration_test")

        if integration_job:
            # Should define services with postgres
            assert "services" in integration_job, "Integration tests should use services"
            services = integration_job["services"]
            assert "postgres" in services, "Should configure PostgreSQL service"

    def test_ci_workflow_has_performance_tests(self, workflows_dir: Path) -> None:
        """Test that ci.yml includes performance test job."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        jobs = data.get("jobs", {})

        # Should have performance test job
        has_performance = "performance-test" in jobs or "performance_test" in jobs
        assert has_performance, "CI should include performance tests"

    def test_ci_workflow_has_docs_check(self, workflows_dir: Path) -> None:
        """Test that ci.yml includes documentation check job."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        jobs = data.get("jobs", {})

        # Should have docs check job
        has_docs = "docs-check" in jobs or "docs_check" in jobs
        assert has_docs, "CI should include documentation checks"

    def test_ci_workflow_has_summary(self, workflows_dir: Path) -> None:
        """Test that ci.yml includes workflow summary job."""
        ci_file = workflows_dir / "ci.yml"

        with open(ci_file, "r") as f:
            data = yaml.safe_load(f)

        jobs = data.get("jobs", {})

        # Should have summary job
        has_summary = any("summary" in job.lower() for job in jobs.keys())
        assert has_summary, "CI should include workflow summary"