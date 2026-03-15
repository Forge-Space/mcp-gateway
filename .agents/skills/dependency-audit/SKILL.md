---
name: dependency-audit
description: Audit Python and Node.js dependency declarations for missing direct deps, unpinned versions, Dockerfile base image drift, and transitive dependency risks. Use when the task is about dependency health, version pinning, or supply chain integrity.
---

# Dependency Audit

## Goal

Detect and fix dependency declaration gaps before they cause production breaks.

## Checks

### 1. Missing Direct Dependencies
Find imports that are not declared in `pyproject.toml` dependencies:

```bash
# Extract all top-level imports from Python source
grep -rh "^from \|^import " tool_router/ --include="*.py" | \
  sed 's/from \([a-zA-Z_]*\).*/\1/' | sed 's/import \([a-zA-Z_]*\).*/\1/' | \
  sort -u | grep -v "^tool_router$\|^dribbble_mcp$\|^__\|^os$\|^sys$\|^typing$\|^collections$\|^datetime$\|^json$\|^re$\|^time$\|^pathlib$\|^logging$\|^functools$\|^threading$\|^unittest$\|^dataclasses$\|^abc$\|^enum$\|^hashlib$\|^hmac$\|^uuid$\|^contextlib$\|^io$\|^copy$\|^math$\|^random$\|^inspect$\|^warnings$\|^textwrap$\|^importlib$\|^base64$\|^secrets$\|^urllib$"
```

Cross-reference against `pyproject.toml [project] dependencies`.

### 2. Version Pinning
Every direct dependency should have a lower bound:
- Acceptable: `fastapi>=0.109.0,<1.0.0`
- Risky: `httpx` (no version constraint)

### 3. Dockerfile Base Image Consistency
All Dockerfiles should use the same Python minor version as `requires-python` in pyproject.toml.

```bash
grep -rn "FROM python:" Dockerfile* service-manager/Dockerfile
```

Expected: all use `python:3.12-*` (or match `requires-python`).

### 4. Optional vs Required
Packages used only in specific deployment modes should be in `[project.optional-dependencies]`:
- `otel` group: OpenTelemetry packages
- `dev` group: test/lint tools

## Fix Patterns

| Issue | Fix |
|-------|-----|
| Import X but X not in deps | Add `X>=min_version` to `[project] dependencies` |
| No version bound | Add `>=lower,<upper` range |
| Dockerfile Python mismatch | Change `FROM python:X.Y` to match pyproject.toml |
| Transitive-only dep | Promote to direct dependency with pinning |

## Validation

```bash
# Verify pyproject.toml is valid
python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"

# Verify pip install works
pip install -e ".[dev]" --dry-run

# Run tests
pytest tool_router/tests/ --timeout=30 -q
```
