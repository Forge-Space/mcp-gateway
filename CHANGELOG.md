# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added
- **`.shellcheckrc`**: strict shellcheck config
- **`.husky/pre-commit`** and **`.husky/commit-msg`**: forge-patterns gates
- **`shell-lint` CI job**: shellcheck + shfmt
- **`base-ci.yml`**: shared CI workflow
- **`scripts/services/`**: enable, disable, list service scripts
- **`scripts/gateway/register-enhanced.sh`**: conditional server registration

### Changed
- **`engines.node`**: `>=18.0.0` to `>=22.0.0`
- **`NODE_VERSION`** in CI: `22` to `24`
- **`ruff>=0.4.0`**, **`mypy>=1.0.0`** added to dev deps

### Fixed
- **18 shell scripts**: `set -e` to `set -euo pipefail`

## [1.26.0] - 2026-02-18

### Pattern Application Phase: UIForge Patterns Integration
- Prettier configuration aligned with forge-patterns base config
- Pattern validation script created
- Pre-commit hooks updated

## [1.25.0] - 2026-02-18

### YAML Migration Validation Complete
- Migration validation script created
- Configuration issues resolved
