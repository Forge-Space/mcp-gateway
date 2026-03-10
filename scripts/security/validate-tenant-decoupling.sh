#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v rg >/dev/null 2>&1; then
  echo "ERROR: ripgrep (rg) is required for tenant-decoupling validation."
  exit 1
fi

INCLUDE_PATHS=(
  "src"
  "scripts"
  "config/shared"
  "config/monitoring"
  "dribbble_mcp"
  "apps/web-admin"
  ".github/workflows"
  ".github/shared"
  "Dockerfile.uiforge.consolidated"
  "package.json"
  ".env.n8n.example"
)

ALLOWLIST_GLOBS=(
  "--glob=!docs/**"
  "--glob=!data/**"
  "--glob=!**/node_modules/**"
  "--glob=!**/dist/**"
  "--glob=!**/coverage/**"
  "--glob=!**/*.lock"
  "--glob=!CHANGELOG.md"
  "--glob=!PROJECT_CONTEXT.md"
  "--glob=!.github/CODEOWNERS"
  "--glob=!.github/branch-protection.md"
  "--glob=!.github/docs/**"
  "--glob=!.github/IMPLEMENTATION_SUMMARY.md"
  "--glob=!scripts/security/validate-tenant-decoupling.sh"
)

TOKENS=(
  "vsantana-organization"
  "@vsantana-org"
  "VSANTANA_"
  "LucasSantana-Dev"
  "github.com/lucassantana/"
  "/Users/lucassantana/"
)

FAIL=0

for token in "${TOKENS[@]}"; do
  MATCHES="$(rg -n --no-heading "${ALLOWLIST_GLOBS[@]}" "$token" "${INCLUDE_PATHS[@]}" || true)"
  if [[ -n "$MATCHES" ]]; then
    echo "BLOCKED token found: $token"
    echo "$MATCHES"
    FAIL=1
  fi
done

if [[ "$FAIL" -ne 0 ]]; then
  echo "Tenant-decoupling validation failed."
  exit 1
fi

echo "Tenant-decoupling validation passed."
