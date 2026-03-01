# Code Style Conventions

## Python (primary)
- **Formatter**: ruff format (double quotes, spaces, line-length 120)
- **Linter**: ruff with comprehensive rule sets (E, F, W, I, N, UP, ANN, S, B, C4, etc.)
- **Ruff scope**: `src = ["tool_router", "dribbble_mcp"]` — CI only checks these dirs. `ruff check .` catches tests/scripts/service-manager too
- **Per-file-ignores**: tests/, scripts/, service-manager/ have subprocess security (S607/S603/PLW1510) and other rules suppressed (PR #93, 2026-03-01)
- **Lint status**: 0 errors ecosystem-wide as of 2026-03-01 (was 1188, fixed in PR #93)
- **Type hints**: Required (ANN rules enabled, except ANN401 for Any)
- **Docstrings**: Google convention
- **Naming**: PEP8 (snake_case functions/vars, PascalCase classes)
- **Max complexity**: McCabe 10, max-args 5, max-branches 12, max-returns 6, max-statements 50
- **Imports**: isort with known-first-party = ["tool_router", "dribbble_mcp"]
- **No print statements**: T20 enabled (use logging instead)
- **No commented-out code**: ERA enabled

## TypeScript (npm wrapper)
- **Linter**: ESLint
- **Formatter**: Prettier
- **Style**: Matches forge-patterns conventions

## Shell Scripts
- **Linter**: shellcheck
- **Located in**: scripts/, start.sh

## General
- Functions <50 lines, cyclomatic complexity <10
- Line width: 120 chars (Python), 100 chars (TypeScript)
- Coverage: >=80% (pytest --cov-fail-under=80)
- Conventional commits: feat, fix, refactor, chore, docs
