# mcp-gateway

Self-hosted MCP gateway with tool-router. Python 3.12.

## Quick Reference

```bash
pip install -e ".[dev]"
pytest tool_router/tests/ -v --timeout=30
ruff check tool_router/ dribbble_mcp/
ruff format --check tool_router/ dribbble_mcp/
python -m build
```

## Project Structure

```
tool_router/          # Main Python package (NOT apps/tool-router/)
  ai/                 # AI selector, prompts, feedback
  cache/              # Caching layer
  core/               # Core server
  scoring/            # Tool scoring/matching
  training/           # Training pipeline (experimental)
  tests/              # Test suite
dribbble_mcp/         # Dribbble MCP integration
apps/                 # Legacy structure (DO NOT reference in CI)
```

## CI

- Authoritative workflow: `.github/workflows/ci.yml` (4 jobs: Lint, Test, Build, Security)
- Release pipeline: `.github/workflows/release-automation.yml` — runs `make test` (quality-gates job must pass before Docker build + PyPI publish)
- `GITHUB_TOKEN= gh ...` required (env var overrides keyring)
- `CLAUDE.md` is gitignored — use `git add -f CLAUDE.md` to commit changes
- GitGuardian workflow: `.github/workflows/gitguardian.yml` — `GITGUARDIAN_API_KEY` secret may be invalid (check secret first if scan fails)
- Main branch required checks: "Test", "Build", "Lint" (must match CI job `name:` fields exactly)
- GitGuardian `GITGUARDIAN_API_KEY` secret is expired — scan fails but is not a required check
- Main branch ruleset has no bypass actors by default — temporarily add via API for urgent merges

## Documentation Governance
- NEVER create task-specific docs in repo root or docs/ (e.g., *_COMPLETE.md, *_SUMMARY.md, STATUS_*.md, PHASE*.md, *_REPORT.md, *_CHECKLIST.md)
- Task completion info belongs in: commit messages, CHANGELOG.md, PR descriptions, or memory files
- Session plans stay in .claude/plans/ (ephemeral, not committed)
- Allowed root .md: README, CHANGELOG, CONTRIBUTING, CLAUDE, PROJECT_CONTEXT, PUBLISHING
- docs/ is for living operational/architectural guides only

## Known Issues

- `docs/PRODUCTION_DEPLOYMENT.md`: deployment guide with docker-compose examples — CodeRabbit flags many issues, some are intentional documentation (not runnable code)
- ~342 pre-existing test failures (broken imports, removed classes, mock mismatches)
- Excluded in CI: training/, test_observability, test_cache_basic, test_cache_compliance, unit/test_specialist_coordinator, unit/test_ui_specialist, performance/, integration/
- pyproject.toml `addopts` is the single source of truth for pytest flags (coverage, verbosity, strict-markers). Makefile and ci.yml only add `--ignore` and `--timeout` flags — NEVER use `--override-ini`
- `make test` and `ci.yml` test step are aligned — update both when adding/removing test exclusions
- Coverage omit list in `[tool.coverage.run]` must match the test `--ignore` list — if a test file is ignored, its source module should be in `omit`
- `pytest-timeout` required but was missing from dev deps (now added)
