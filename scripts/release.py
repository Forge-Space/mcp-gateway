#!/usr/bin/env python3
"""Automated release script for mcp-gateway.

Usage:
    python scripts/release.py patch     # 1.12.0 → 1.12.1
    python scripts/release.py minor     # 1.12.0 → 1.13.0
    python scripts/release.py major     # 1.12.0 → 2.0.0
    python scripts/release.py --detect  # auto-detect bump type from commits

Steps performed:
  1. Detect bump type from conventional commits (if --detect)
  2. Compute new version
  3. Update pyproject.toml version
  4. Promote [Unreleased] → [NEW_VERSION] in CHANGELOG.md
  5. Run quality gates (lint + tests)
  6. Create branch, commit, push, open PR
  7. Poll CI until all required checks pass (or timeout)
  8. Merge PR (admin squash)
  9. Tag + create GitHub Release
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
REPO_SLUG = "Forge-Space/mcp-gateway"

REQUIRED_CI_JOBS = {"Lint", "Test", "Build"}
CI_POLL_INTERVAL = 30  # seconds
CI_TIMEOUT = 900  # 15 minutes


# ── Helpers ──────────────────────────────────────────────────────────────────


def run(cmd: str, *, capture: bool = False, check: bool = True) -> str:
    """Run a shell command, return stdout."""
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True, check=check)
    return result.stdout.strip() if capture else ""


def current_version() -> str:
    text = PYPROJECT.read_text()
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        sys.exit("Could not parse version from pyproject.toml")
    return m.group(1)


def bump_version(version: str, bump: str) -> str:
    parts = list(map(int, version.split(".")))
    if bump == "major":
        return f"{parts[0] + 1}.0.0"
    if bump == "minor":
        return f"{parts[0]}.{parts[1] + 1}.0"
    return f"{parts[0]}.{parts[1]}.{parts[2] + 1}"


def detect_bump_type() -> str:
    """Auto-detect bump type from commits since last tag."""
    last_tag = run("git tag --sort=-version:refname | head -1", capture=True)
    ref = f"{last_tag}..HEAD" if last_tag else "HEAD~10..HEAD"
    msgs = run(f"git log {ref} --format='%s'", capture=True).splitlines()
    if any(re.match(r"^[a-z]+!:", m) or "BREAKING CHANGE" in m for m in msgs):
        return "major"
    if any(re.match(r"^feat[(!:]", m) for m in msgs):
        return "minor"
    return "patch"


def get_unreleased_entries() -> str:
    """Extract content of the [Unreleased] section from CHANGELOG."""
    text = CHANGELOG.read_text()
    m = re.search(r"## \[Unreleased\]\n(.*?)(?=\n## \[)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def update_pyproject_version(new_version: str) -> None:
    text = PYPROJECT.read_text()
    new_text = re.sub(
        r'^(version\s*=\s*)"[^"]+"',
        rf'\1"{new_version}"',
        text,
        flags=re.MULTILINE,
    )
    PYPROJECT.write_text(new_text)


def promote_changelog(new_version: str, unreleased: str) -> None:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    text = CHANGELOG.read_text()
    new_section = f"## [{new_version}] - {today}\n\n{unreleased}\n"
    new_text = text.replace(
        "## [Unreleased]\n",
        f"## [Unreleased]\n\n{new_section}",
    )
    CHANGELOG.write_text(new_text)


def poll_ci(pr_number: int, timeout: int = CI_TIMEOUT) -> bool:
    """Poll PR CI until required checks all pass. Returns True on success."""
    deadline = time.time() + timeout
    print(f"\nPolling CI for PR #{pr_number} (timeout {timeout}s)...")
    while time.time() < deadline:
        raw = run(
            f"GITHUB_TOKEN= gh pr view {pr_number} --repo {REPO_SLUG} --json statusCheckRollup",
            capture=True,
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            time.sleep(CI_POLL_INTERVAL)
            continue

        checks = data.get("statusCheckRollup", [])
        ci_checks = [c for c in checks if c.get("workflowName") == "CI Pipeline"]
        required = {c["name"]: c for c in ci_checks if c["name"] in REQUIRED_CI_JOBS}

        if len(required) < len(REQUIRED_CI_JOBS):
            print(f"  Waiting for CI jobs to appear ({len(required)}/{len(REQUIRED_CI_JOBS)})...")
            time.sleep(CI_POLL_INTERVAL)
            continue

        all_done = all(c["status"] == "COMPLETED" for c in required.values())
        all_pass = all(c["conclusion"] in ("SUCCESS", "SKIPPED") for c in required.values())

        statuses = ", ".join(
            f"{n}: {'✅' if c['conclusion'] == 'SUCCESS' else '⏳' if c['status'] != 'COMPLETED' else '❌'}"
            for n, c in required.items()
        )
        print(f"  {statuses}")

        if all_done and all_pass:
            print("  All required CI checks passed ✅")
            return True
        if all_done and not all_pass:
            failed = [n for n, c in required.items() if c["conclusion"] not in ("SUCCESS", "SKIPPED")]
            print(f"  CI FAILED: {failed}")
            return False

        time.sleep(CI_POLL_INTERVAL)

    print("  CI poll timed out")
    return False


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Automate mcp-gateway releases")
    parser.add_argument(
        "bump",
        nargs="?",
        choices=["patch", "minor", "major"],
        help="Version bump type",
    )
    parser.add_argument("--detect", action="store_true", help="Auto-detect bump type from commits")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without executing")
    parser.add_argument("--no-poll", action="store_true", help="Skip CI polling (just open PR)")
    args = parser.parse_args()

    if not args.bump and not args.detect:
        parser.error("Provide bump type (patch/minor/major) or use --detect")

    bump = args.bump or detect_bump_type()
    old_version = current_version()
    new_version = bump_version(old_version, bump)
    unreleased = get_unreleased_entries()
    branch = f"chore/release-{new_version}"
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    print("\nmcp-gateway release automation")
    print(f"  Bump:        {bump}")
    print(f"  Old version: {old_version}")
    print(f"  New version: {new_version}")
    print(f"  Branch:      {branch}")
    print(f"  Unreleased:  {'(empty — will create minimal entry)' if not unreleased else unreleased[:80] + '...'}")

    if args.dry_run:
        print("\n[dry-run] No changes made.")
        return

    # 1. Verify clean working tree on main
    status = run("git status --short", capture=True)
    if status:
        sys.exit(f"Working tree is dirty — commit or stash changes first:\n{status}")

    current_branch = run("git branch --show-current", capture=True)
    if current_branch != "main":
        sys.exit(f"Must be on main branch (currently on '{current_branch}')")

    run("git pull")

    # 2. Update files
    print("\nUpdating pyproject.toml...")
    update_pyproject_version(new_version)

    print("Promoting CHANGELOG...")
    entry = unreleased or f"### Changed\n\n- Maintenance release: {new_version}"
    promote_changelog(new_version, entry)

    # 3. Quality gates
    print("\nRunning quality gates...")
    result = subprocess.run("ruff check tool_router/ dribbble_mcp/", shell=True)
    if result.returncode != 0:
        sys.exit("Lint failed — fix errors before releasing")

    result = subprocess.run(
        "python3 -m pytest tool_router/tests/ -q --no-cov --timeout=30",
        shell=True,
    )
    if result.returncode != 0:
        sys.exit("Tests failed — fix failures before releasing")

    # 4. Branch + commit + push
    print(f"\nCreating branch {branch}...")
    run(f"git checkout -b {branch}")
    run("git add pyproject.toml CHANGELOG.md")
    run(f'git commit -m "chore(release): v{new_version}"')
    run(f"git push -u origin {branch}")

    # 5. Open PR
    print("\nOpening PR...")
    pr_body = f"## v{new_version} — {today}\n\nAutomated release PR.\n\n### Changes\n\n{entry}\n"
    pr_url = run(
        f'GITHUB_TOKEN= gh pr create --title "chore(release): v{new_version}" '
        f'--body "{pr_body}" --base main --head {branch}',
        capture=True,
    )
    print(f"PR opened: {pr_url}")

    pr_number_m = re.search(r"/pull/(\d+)", pr_url)
    if not pr_number_m:
        sys.exit(f"Could not parse PR number from: {pr_url}")
    pr_number = int(pr_number_m.group(1))

    if args.no_poll:
        print(f"\nSkipping CI poll. Merge PR #{pr_number} manually when ready.")
        return

    # 6. Poll CI
    if not poll_ci(pr_number):
        sys.exit(f"\nCI failed or timed out on PR #{pr_number}. Check and re-run.")

    # 7. Merge
    print(f"\nMerging PR #{pr_number}...")
    run(
        f"GITHUB_TOKEN= gh pr merge {pr_number} --repo {REPO_SLUG} "
        f"--squash --delete-branch --admin "
        f'--subject "chore(release): v{new_version} (#{pr_number})"'
    )

    # 8. Tag + GitHub Release
    print(f"\nTagging v{new_version}...")
    run("git checkout main && git pull")
    run(f"git tag v{new_version}")
    run(f"git push origin v{new_version}")

    print("Creating GitHub Release...")
    release_notes = f"## v{new_version} — {today}\n\n{entry}"
    run(
        f"GITHUB_TOKEN= gh release create v{new_version} "
        f"--repo {REPO_SLUG} "
        f'--title "v{new_version}" '
        f'--notes "{release_notes}" '
        f"--target main"
    )

    print(f"\n✅ Released v{new_version} successfully!")
    print(f"   Tag:     v{new_version}")
    print(f"   Release: https://github.com/{REPO_SLUG}/releases/tag/v{new_version}")


if __name__ == "__main__":
    main()
