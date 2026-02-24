# Contributing to MCP Gateway

Thank you for contributing to MCP Gateway. This guide covers everything you need to know to submit high-quality contributions.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Review Process](#review-process)

---

## Code of Conduct

All contributors are expected to be respectful, constructive, and professional. Harassment or exclusionary behavior will not be tolerated.

---

## Getting Started

### 1. Fork and clone

```bash
git clone https://github.com/Forge-Space/mcp-gateway.git
cd mcp-gateway
npm install
```

### 2. Create a feature branch

```bash
git checkout -b feat/my-feature
```

### 3. Validate your environment

```bash
make lint
make test
npm run build
```

---

## Development Workflow

### Repository structure

MCP Gateway is a hybrid TypeScript and Python project with Docker Compose orchestration:

```
src/
├── gateway/          # TypeScript gateway service
├── ai/               # Python AI modules (feedback.py, ui_specialist.py)
├── scoring/          # Python scoring engine (matcher.py)
└── core/             # Core configuration and utilities
```

### Commands

```bash
make start            # Start all services with Docker Compose
make stop             # Stop all services
make lint             # Lint TypeScript and Python
make test             # Run all test suites
npm run build         # Build TypeScript components
```

### Python tooling

- Linter: Ruff
- Type checker: mypy
- Test runner: pytest
- Python version: 3.12+

### TypeScript tooling

- Linter: ESLint
- Formatter: Prettier
- Node version: 22+

### Branch flow

```
feature → dev → release → main
```

1. Create feature branch from `dev`
2. Open PR to `dev` for review
3. After merge, release branches are created from `dev`
4. Release branches merge to `main` for deployment

### Commit message format

Follow Angular conventional commits:

```
feat(ai): add contextual feedback scoring
fix(gateway): resolve routing timeout issue
docs(readme): update Docker setup instructions
refactor(scoring): simplify matcher algorithm
test(ai): add unit tests for ui_specialist
chore(deps): upgrade ruff to 0.9.0
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `chore`

---

## Code Standards

### TypeScript

- Strict mode enabled
- No `any` types without justification
- All functions must have explicit return types
- Use type imports: `import type { ... }`

### Python

- Type hints required for all function signatures
- Use `from __future__ import annotations` for forward references
- Follow PEP 8 conventions (enforced by Ruff)
- Docstrings for public modules, classes, and functions

### General code quality

- Functions: maximum 50 lines
- Cyclomatic complexity: maximum 10
- Line width: maximum 100 characters
- No comments unless explicitly requested or documenting complex algorithms

### Security

- Never commit secrets or credentials
- Use environment variables for configuration
- Validate all user inputs
- Sanitize all outputs

---

## Testing Requirements

### Coverage targets

- Overall coverage: minimum 80%
- Critical modules: 100% (ai/feedback.py, ai/ui_specialist.py, scoring/matcher.py, core/config.py)
- Edge cases and error conditions required

### What to test

- Business logic and routing logic
- Integration flows between services
- Error handling and edge cases
- AI scoring accuracy

### What NOT to test

- Trivial getters/setters
- Simple enum definitions
- Third-party library behavior

### Running tests

```bash
make test             # Run all tests (Python + TypeScript)
pytest                # Run Python tests only
npm test              # Run TypeScript tests only
```

---

## Pull Request Process

### Before opening a PR

Ensure all of the following pass:

```
- [ ] make lint passes with no errors
- [ ] make test passes with all tests green
- [ ] npm run build succeeds
- [ ] Docker services start correctly with make start
- [ ] No secrets or credentials committed
- [ ] CHANGELOG.md updated under [Unreleased]
- [ ] README.md updated if public API changed
- [ ] Commit messages follow conventional commit format
```

### PR checklist

1. Push your branch: `git push origin feat/my-feature`
2. Open PR targeting `dev` branch
3. Fill in the PR template completely
4. Link related issues using `Closes #123` syntax
5. Request review from maintainers
6. Address all review feedback

### PR title format

```
feat(ai): add sentiment analysis module
fix(scoring): resolve null pointer in matcher
docs: update Docker deployment guide
```

---

## Review Process

1. **Automated CI** runs lint, type-check, build, tests, and security scans
2. **Maintainer review** checks code quality, architecture, and standards compliance
3. **Approval** requires CI passing + at least 1 maintainer approval
4. **Merge** is done by a maintainer using squash merge to `dev`

Typical review turnaround: 2-5 business days.

---

## Questions?

Open a [GitHub Discussion](https://github.com/Forge-Space/mcp-gateway/discussions) or file an [issue](https://github.com/Forge-Space/mcp-gateway/issues).
