# Forge Patterns Integration Guide

This document describes how the [forge-patterns](https://github.com/LucasSantana-Dev/forge-patterns) shared code quality patterns are integrated into the MCP Gateway project, including what was adopted, what was customized, and how to maintain compliance.

## Overview

The integration follows a **hybrid approach**: shared base configurations are extended locally, with project-specific customizations preserved as overrides. This ensures consistency across the UIForge ecosystem while retaining the superior rule sets already in place.

## Integrated Patterns

### Code Quality

| Pattern | Source | Location | Strategy |
|---------|--------|----------|----------|
| ESLint base config | `forge-patterns` | `patterns/code-quality/eslint/base.config.js` | Extended with project overrides |
| Prettier base config | `forge-patterns` | `patterns/code-quality/prettier/base.config.json` | Referenced via `$schema`, key settings aligned |

### CI/CD

The project uses its own `base-ci.yml` shared workflow (`.github/shared/workflows/base-ci.yml`), which is more comprehensive than the forge-patterns template. The `ci.yml` correctly references it.

## ESLint Configuration

**File**: `.eslintrc.js`

The project extends the shared base config and adds 50+ project-specific rules on top:

```js
const baseConfig = require('./patterns/code-quality/eslint/base.config.js');

module.exports = {
  ...baseConfig,
  // project-specific overrides below
};
```

**Project-specific customizations preserved**:

- `no-console: warn` (base uses `error`)
- `@typescript-eslint/no-explicit-any: warn` (base uses `error`)
- Comprehensive `import/*` rules not in the base
- File-specific overrides for test files and config files

## Prettier Configuration

**File**: `.prettierrc.json`

Aligned with shared base via `$schema` reference. Key settings:

| Setting | Shared Base | Project Value | Notes |
|---------|-------------|---------------|-------|
| `trailingComma` | `es5` | `es5` | ✅ Aligned |
| `arrowParens` | `always` | `always` | ✅ Aligned |
| `singleQuote` | `true` | `true` | ✅ Aligned |
| `printWidth` | `100` | `100` | ✅ Aligned |
| `semi` | `true` | `true` | ✅ Aligned |

**Project-specific overrides preserved**:

- `*.json` — `printWidth: 80`, `trailingComma: none`
- `*.yml` / `*.yaml` — `printWidth: 80`, `singleQuote: false`
- `*.md` — `printWidth: 80`, `proseWrap: always`

## Pattern Validation

Run the compliance check at any time:

```bash
bash scripts/validation/validate-patterns.sh
```

This validates:

1. ESLint config references shared base
2. Prettier config references shared base
3. Shared pattern files exist locally
4. CI/CD uses shared workflow
5. GitHub Actions versions are current
6. Security scanning is configured

The script also runs automatically on every commit via the `validate-patterns` pre-commit hook.

## Updating Shared Patterns

When `forge-patterns` releases updates:

1. Copy updated base configs into `patterns/code-quality/`
2. Review diffs against project overrides for conflicts
3. Run `bash scripts/validation/validate-patterns.sh` to confirm compliance
4. Update this document if the integration strategy changes

## References

- [forge-patterns repository](https://github.com/LucasSantana-Dev/forge-patterns)
- [Assessment Report](./uiforge-patterns-assessment-report.md)
- [Pattern validation script](../scripts/validation/validate-patterns.sh)
- [ESLint base config](../patterns/code-quality/eslint/base.config.js)
- [Prettier base config](../patterns/code-quality/prettier/base.config.json)
