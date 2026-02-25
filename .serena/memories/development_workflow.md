# Development Workflow

## Branch Flow
Feature branch → Release branch PR → Main PR → Automated deploy

## Before Committing
1. `ruff check tool_router/ --fix` (auto-fix lint)
2. `ruff format tool_router/` (format)
3. `make test COVERAGE=true` (tests with coverage >=80%)
4. `make lint-strict` (all linters, no fallbacks)
5. Conventional commit message

## Pre-commit Hooks
Configured via `.pre-commit-config.yaml` — runs on `git commit` automatically.

## CI/CD Pipeline
- GitHub Actions: lint, test, security scan, build
- Coverage reports: XML + HTML + terminal
- Branch protection: main is protected, PRs required

## Documentation Governance
- No task-specific docs in repo root or docs/ (*_COMPLETE.md, STATUS_*.md, PHASE*.md, etc.)
- 44 obsolete task reports deleted (2026-02-24, PR #61)
- Task info belongs in: commit messages, CHANGELOG, PR descriptions, or memory files
- .gitignore updated with `.windsurf/plans/`, `.claude/plans/` guards

## Cross-Project Integration
- Depends on @forgespace/core (forge-patterns)
- Patterns synced via `npm run integrate:mcp-gateway` (from forge-patterns)
- Shared constants from forge-patterns/patterns/shared-constants/
