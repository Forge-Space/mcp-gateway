# Linting and Formatting Guide

**Version:** 1.0.0
**Last Updated:** 2025-02-14
**Audience:** Contributors, Maintainers

---

## Overview

This document describes the linting, formatting, and code quality tools configured for the MCP Gateway project. All configurations are aligned with the project's cost-free, self-hosted philosophy and enforce strict quality standards.

### Tech Stack Coverage

- **Python** - Ruff (linting + formatting)
- **TypeScript** - ESLint + Prettier
- **Shell Scripts** - Shellcheck
- **YAML/JSON** - Prettier + yamllint
- **Markdown** - markdownlint (via CodeRabbit)
- **Docker** - hadolint (via CodeRabbit)

---

## Quick Start

### Install Dependencies

```bash
# Python dependencies (if not already installed)
pip install -r requirements.txt

# Node.js dependencies
npm install

# Pre-commit hooks
pip install pre-commit
pre-commit install
```

### Run All Checks

```bash
# Run all linters
make lint

# Format all code
make format

# Run pre-commit hooks
pre-commit run --all-files
```

---

## Python Configuration

### Ruff

**Configuration:** `@/pyproject.toml`

Ruff is an extremely fast Python linter and formatter that replaces multiple tools (flake8, black, isort, etc.).

#### Ruff Features

- **Linting:** PEP 8 compliance, type checking, import sorting
- **Formatting:** Black-compatible code formatting
- **Performance:** 10-100x faster than traditional tools
- **Cost:** $0 (open-source)

#### Usage

```bash
# Lint Python code
make lint-python
ruff check tool_router/

# Format Python code
make format-python
ruff format tool_router/

# Auto-fix issues
ruff check tool_router/ --fix
```

#### Ruff Rules

- Line length: 100 characters
- Target Python: 3.9+
- Strict type hints required
- Google-style docstrings
- Import sorting: stdlib → third-party → local

#### Configuration Excerpt

```toml
[tool.ruff]
line-length = 100
target-version = "py39"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "ANN", "B", "A", "C4", "DTZ", "T10", "DJ", "EM", "ISC", "ICN", "G", "PIE", "T20", "PT", "Q", "RSE", "RET", "SIM", "TID", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]
```

---

## TypeScript Configuration

### ESLint

**Configuration:** `@/.eslintrc.json`

ESLint enforces code quality and consistency for the TypeScript NPM client.

#### ESLint Features

- **Type-aware linting** - Uses TypeScript compiler for deep analysis
- **Import organization** - Automatic import sorting and grouping
- **Strict rules** - No `any`, explicit return types, strict booleans
- **Cost:** $0 (open-source)

#### Usage

```bash
# Lint TypeScript
make lint-typescript
npm run lint

# Auto-fix issues
npm run lint:eslint:fix

# Type check only
npm run lint:types
```

#### ESLint Rules

```json
{
  "@typescript-eslint/no-explicit-any": "error",
  "@typescript-eslint/explicit-function-return-type": "error",
  "@typescript-eslint/strict-boolean-expressions": "error",
  "@typescript-eslint/no-floating-promises": "error",
  "@typescript-eslint/consistent-type-imports": "error",
  "import/order": ["error", {
    "groups": ["builtin", "external", "internal", "parent", "sibling", "index"],
    "newlines-between": "always",
    "alphabetize": { "order": "asc" }
  }]
}
```

#### Example

```typescript
// ❌ BAD
import { Client } from './client'
import fs from 'fs'

function getData(id) {
  return fetch(`/api/${id}`)
}

// ✅ GOOD
import fs from 'fs'

import { Client } from './client'

function getData(id: string): Promise<Response> {
  return fetch(`/api/${id}`)
}
```

### Prettier

**Configuration:** `@/.prettierrc.json`

Prettier handles code formatting for TypeScript, JSON, YAML, and Markdown.

#### Prettier Features

- **Opinionated formatting** - No configuration debates
- **Multi-language** - TS, JS, JSON, YAML, MD
- **IDE integration** - Works with all major editors
- **Cost:** $0 (open-source)

#### Usage

```bash
# Format TypeScript
make format-typescript
npm run format

# Check formatting only
npm run lint:prettier
```

#### Configuration

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": false,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

---

## Shell Script Configuration

### Shellcheck

**Tool:** shellcheck
**Make Target:** `make shellcheck`

Shellcheck analyzes shell scripts for common errors and best practices.

#### Shellcheck Features

- **POSIX compliance** - Ensures portability
- **Error detection** - Catches common mistakes
- **Best practices** - Suggests improvements
- **Cost:** $0 (open-source)

#### Usage

```bash
# Lint all shell scripts
make shellcheck

# Lint specific script
shellcheck scripts/gateway/register.sh
```

#### Common Issues Fixed

```bash
# ❌ BAD - Unquoted variable
echo $USER

# ✅ GOOD - Quoted variable
echo "$USER"

# ❌ BAD - Missing error handling
cd /tmp
rm -rf data/

# ✅ GOOD - Error handling
cd /tmp || exit 1
rm -rf data/
```

---

## Pre-commit Hooks

**Configuration:** `@/.pre-commit-config.yaml`

Pre-commit hooks run automatically before each commit to catch issues early.

### Installed Hooks

1. **Security**

   - gitleaks - Secret detection
   - detect-private-key - Private key detection

2. **Standard Checks**

   - check-yaml - YAML syntax
   - check-json - JSON syntax
   - check-toml - TOML syntax
   - end-of-file-fixer - Ensure newline at EOF
   - trailing-whitespace - Remove trailing spaces
   - check-added-large-files - Block files >1MB
   - check-merge-conflict - Detect merge conflicts
   - mixed-line-ending - Enforce LF line endings

3. **Python**

   - ruff (lint) - Code quality
   - ruff-format - Code formatting
   - pytest - Run tests

4. **TypeScript**

   - prettier - Code formatting
   - eslint - Code quality
   - tsc - Type checking

5. **Shell**

   - shellcheck - Script linting

6. **Dependencies**

   - npm-check-updates - Check outdated packages (manual stage)

### Pre-commit Usage

```bash
# Install hooks
make pre-commit-install

# Run on all files
make pre-commit-run

# Run specific hook
pre-commit run ruff --all-files

# Run dependency check (manual stage)
pre-commit run npm-check-updates --hook-stage manual

# Update hook versions
make pre-commit-update
```

### Skipping Hooks

```bash
# Skip all hooks (use sparingly)
git commit --no-verify -m "emergency fix"

# Skip specific hook
SKIP=eslint git commit -m "fix: urgent change"
```

---

## CI/CD Integration

**Configuration:** `@/.github/workflows/ci.yml`

All quality checks run automatically in CI/CD on every push and pull request.

### CI Jobs

1. **lint-python** - Ruff linting for Python
2. **lint-shell** - Shellcheck for shell scripts
3. **lint-typescript** - ESLint + Prettier for TypeScript
4. **dependency-check** - npm-check-updates + npm audit
5. **test** - pytest for Python tests
6. **build** - Docker build + smoke tests
7. **trivy** - Container security scanning
8. **security** - Secret scanning with Trufflehog

### Dependency Checking

The `dependency-check` job runs on every PR:

```yaml
- name: Check for outdated dependencies
  run: npm run deps:check
  continue-on-error: true

- name: npm audit
  run: npm audit --audit-level=high
  continue-on-error: false
```

**Behavior:**

- `deps:check` - Reports outdated packages (non-blocking)
- `npm audit` - Blocks PR if high/critical vulnerabilities found

---

## Dependency Management

### npm-check-updates

**Tool:** npm-check-updates (ncu)
**Cost:** $0 (open-source)

Checks for outdated npm dependencies and updates package.json.

#### Usage

```bash
# Check for updates
make deps-check
npm run deps:check

# Update all dependencies
npm run deps:update

# Interactive update (recommended)
make deps-update
npm run deps:update:interactive

# Update specific package
npx npm-check-updates -u typescript
npm install
```

#### Output Example

```text
Checking /Users/user/mcp-gateway/package.json
[====================] 11/11 100%

 @types/node              ^22.10.5  →  ^22.10.6
 eslint                    ^9.18.0  →   ^9.18.1
 typescript                ^5.7.3   →   ^5.7.4

Run npm install to install new versions.
```

### npm audit

Checks for known security vulnerabilities in dependencies.

```bash
# Check for vulnerabilities
npm audit

# Fix automatically (if possible)
npm audit fix

# Force fix (may introduce breaking changes)
npm audit fix --force
```

---

## IDE Integration

### VS Code / Windsurf

**Recommended Extensions:**

- Python: `ms-python.python`
- Ruff: `charliermarsh.ruff`
- ESLint: `dbaeumer.vscode-eslint`
- Prettier: `esbenp.prettier-vscode`
- Shellcheck: `timonwong.shellcheck`

**Settings (`.vscode/settings.json`):**

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "ruff.lint.run": "onSave",
  "ruff.format.args": ["--line-length=100"]
}
```

---

## Makefile Targets

### Linting

```bash
make lint              # Run all linters (Python + TypeScript + Shell)
make lint-python       # Lint Python code only
make lint-typescript   # Lint TypeScript code only
make shellcheck        # Lint shell scripts only
```

### Formatting

```bash
make format            # Format all code (Python + TypeScript)
make format-python     # Format Python code only
make format-typescript # Format TypeScript code only
```

### Testing

```bash
make test              # Run Python tests
make test-coverage     # Run tests with coverage report
```

### Dependencies

```bash
make deps-check        # Check for outdated npm packages
make deps-update       # Update npm packages interactively
```

### Pre-commit

```bash
make pre-commit-install # Install pre-commit hooks
make pre-commit-run     # Run all hooks on all files
make pre-commit-update  # Update hook versions
```

### Help

```bash
make help              # Show all available targets
make                   # Same as 'make help' (default)
```

---

## Troubleshooting

### Ruff Not Found

```bash
# Install Ruff
pip install ruff

# Or install all Python dependencies
pip install -r requirements.txt
```

### ESLint Errors After npm install

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Pre-commit Hook Failures

```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall
pre-commit uninstall
pre-commit install
```

### Prettier Formatting Conflicts with ESLint

This shouldn't happen with our configuration (`eslint-config-prettier` disables conflicting rules), but if it does:

```bash
# Run Prettier first, then ESLint
npm run format
npm run lint:eslint:fix
```

### npm-check-updates Shows No Updates

```bash
# Check if you're using latest ncu
npm install -g npm-check-updates

# Force check all packages
npx npm-check-updates --target latest
```

---

## Best Practices

### Before Committing

1. **Run linters locally**

   ```bash
   make lint
   ```

2. **Format code**

   ```bash
   make format
   ```

3. **Run tests**

   ```bash
   make test
   ```

4. **Check dependencies** (if package.json changed)

   ```bash
   make deps-check
   npm audit
   ```

### During Development

- **Enable format-on-save** in your IDE
- **Fix linting errors immediately** - Don't accumulate technical debt
- **Run pre-commit hooks** before pushing
- **Check CI status** after pushing

### Code Review

- **All linters must pass** - No exceptions
- **No new vulnerabilities** - npm audit must be clean
- **Dependencies justified** - New deps must be cost-free and necessary
- **Tests added** - New code requires tests

---

## Configuration Files Reference

| File | Purpose | Documentation |
|------|---------|---------------|
| `@/.eslintrc.json` | ESLint configuration | [ESLint Docs](https://eslint.org/docs/latest/) |
| `@/.prettierrc.json` | Prettier configuration | [Prettier Docs](https://prettier.io/docs/en/) |
| `@/.prettierignore` | Prettier ignore patterns | [Prettier Ignore](https://prettier.io/docs/en/ignore.html) |
| `@/pyproject.toml` | Ruff configuration | [Ruff Docs](https://docs.astral.sh/ruff/) |
| `@/.pre-commit-config.yaml` | Pre-commit hooks | [Pre-commit Docs](https://pre-commit.com/) |
| `@/tsconfig.json` | TypeScript compiler options | [TSConfig Docs](https://www.typescriptlang.org/tsconfig) |
| `@/package.json` | npm scripts and dependencies | [npm Docs](https://docs.npmjs.com/) |
| `@/Makefile` | Build automation | This document |

---

## References

- **Ruff:** <https://docs.astral.sh/ruff/>
- **ESLint:** <https://eslint.org/docs/latest/>
- **Prettier:** <https://prettier.io/docs/en/>
- **Shellcheck:** <https://www.shellcheck.net/>
- **Pre-commit:** <https://pre-commit.com/>
- **npm-check-updates:** <https://github.com/raineorshine/npm-check-updates>
- **Project PLAN:** `@/PLAN.md`
- **CodeRabbit Guide:** `@/docs/development/CODERABBIT_GUIDE.md`

---

**Remember:** All tools are cost-free and self-hosted. No paid services allowed.
