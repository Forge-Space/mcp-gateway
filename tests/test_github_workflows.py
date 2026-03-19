"""Test suite for GitHub Actions workflow files."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def _workflow_on(data: dict) -> dict:
    return data.get("on", data.get(True, {}))


class TestGitHubWorkflows:
    """Validate workflow files against current CI contracts."""

    @pytest.fixture
    def repo_root(self) -> Path:
        return Path(__file__).parent.parent

    @pytest.fixture
    def workflows_dir(self, repo_root: Path) -> Path:
        return repo_root / ".github" / "workflows"

    @pytest.fixture
    def reusable_dir(self, workflows_dir: Path) -> Path:
        return workflows_dir / "reusable"

    @pytest.fixture
    def ci_data(self, workflows_dir: Path) -> dict:
        return _load_yaml(workflows_dir / "ci.yml")

    @pytest.fixture
    def release_data(self, workflows_dir: Path) -> dict:
        return _load_yaml(workflows_dir / "release-automation.yml")

    def test_workflows_directory_exists(self, workflows_dir: Path, reusable_dir: Path) -> None:
        assert workflows_dir.exists() and workflows_dir.is_dir()
        assert reusable_dir.exists() and reusable_dir.is_dir()

    def test_ci_workflow_exists_and_valid_yaml(self, workflows_dir: Path, ci_data: dict) -> None:
        ci_file = workflows_dir / "ci.yml"
        assert ci_file.exists() and ci_file.is_file()
        assert ci_data["name"] == "CI Pipeline"

    def test_ci_workflow_has_expected_triggers_and_branch_prefixes(self, ci_data: dict) -> None:
        on_cfg = _workflow_on(ci_data)
        for trigger in ["push", "pull_request"]:
            assert trigger in on_cfg
            branches = on_cfg[trigger].get("branches", [])
            for expected in [
                "main",
                "dev",
                "release/*",
                "feature/*",
                "feat/*",
                "fix/*",
                "chore/*",
                "test/*",
                "refactor/*",
                "ci/*",
                "docs/*",
            ]:
                assert expected in branches

    def test_ci_workflow_has_required_jobs(self, ci_data: dict) -> None:
        jobs = ci_data.get("jobs", {})
        expected_jobs = {
            "tenant-decoupling",
            "lint",
            "test",
            "build",
            "typecheck",
            "security",
            "test-autogen-warn",
            "workflow-summary",
        }
        assert expected_jobs.issubset(set(jobs))

    def test_ci_workflow_uses_sha_pinned_actions(self, workflows_dir: Path) -> None:
        ci_content = (workflows_dir / "ci.yml").read_text(encoding="utf-8")
        uses_lines = [line.strip() for line in ci_content.splitlines() if "uses:" in line]
        assert uses_lines
        for line in uses_lines:
            uses = line.split("uses:", maxsplit=1)[1].strip()
            if "${{" in uses:
                continue
            if uses.startswith("docker://"):
                continue
            if "@" not in uses:
                continue
            ref = uses.rsplit("@", maxsplit=1)[1]
            is_sha = len(ref) == 40 and all(ch in "0123456789abcdef" for ch in ref.lower())
            assert is_sha, f"Action must be SHA pinned: {uses}"

    def test_ci_build_depends_on_lint_and_test(self, ci_data: dict) -> None:
        build_needs = ci_data["jobs"]["build"].get("needs", [])
        assert "lint" in build_needs
        assert "test" in build_needs

    def test_ci_workflow_summary_depends_on_all_jobs(self, ci_data: dict) -> None:
        summary_needs = set(ci_data["jobs"]["workflow-summary"].get("needs", []))
        assert summary_needs == {
            "tenant-decoupling",
            "lint",
            "test",
            "build",
            "typecheck",
            "security",
            "test-autogen-warn",
        }

    def test_ci_test_job_includes_workflow_test_file(self, ci_data: dict) -> None:
        run_script = ci_data["jobs"]["test"]["steps"][-1]["run"]
        assert "tests/" in run_script
        assert "--ignore=tests/test_github_workflows.py" not in run_script

    def test_release_workflow_exists_and_uses_make_test(self, workflows_dir: Path, release_data: dict) -> None:
        release_file = workflows_dir / "release-automation.yml"
        assert release_file.exists() and release_file.is_file()
        assert release_data["name"] == "Automated Release Pipeline"

        release_content = release_file.read_text(encoding="utf-8")
        assert "make test" in release_content

    def test_release_workflow_has_main_push_trigger(self, release_data: dict) -> None:
        on_cfg = _workflow_on(release_data)
        assert "push" in on_cfg
        push_branches = on_cfg["push"].get("branches", [])
        assert "main" in push_branches

    def test_reusable_workflow_files_exist_and_are_valid(self, reusable_dir: Path) -> None:
        expected = ["setup-node.yml", "setup-python.yml", "upload-coverage.yml"]
        for name in expected:
            path = reusable_dir / name
            assert path.exists() and path.is_file()
            data = _load_yaml(path)
            on_cfg = _workflow_on(data)
            assert "workflow_call" in on_cfg

    def test_setup_node_reusable_installs_dependencies(self, reusable_dir: Path) -> None:
        content = (reusable_dir / "setup-node.yml").read_text(encoding="utf-8").lower()
        assert "npm" in content
        assert "install" in content or "ci" in content

    def test_setup_python_reusable_installs_dependencies_and_tools(self, reusable_dir: Path) -> None:
        content = (reusable_dir / "setup-python.yml").read_text(encoding="utf-8").lower()
        assert "pip" in content
        assert "install" in content
        for tool in ["pytest", "mypy", "flake8"]:
            assert tool in content

    def test_upload_coverage_reusable_references_codecov(self, reusable_dir: Path) -> None:
        content = (reusable_dir / "upload-coverage.yml").read_text(encoding="utf-8").lower()
        assert "codecov" in content

    def test_all_workflow_jobs_use_timeout_minutes(self, workflows_dir: Path, reusable_dir: Path) -> None:
        workflow_files = [
            workflows_dir / "ci.yml",
            workflows_dir / "release-automation.yml",
        ]
        for workflow_file in workflow_files:
            data = _load_yaml(workflow_file)
            for job in data.get("jobs", {}).values():
                if isinstance(job, dict) and "uses" not in job:
                    assert "timeout-minutes" in job, f"Missing timeout in {workflow_file.name}"
