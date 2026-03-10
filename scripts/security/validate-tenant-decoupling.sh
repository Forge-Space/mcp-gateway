#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

SEARCH_TOOL=""
if command -v rg >/dev/null 2>&1; then
  SEARCH_TOOL="rg"
elif command -v grep >/dev/null 2>&1; then
  SEARCH_TOOL="grep"
else
  echo "ERROR: neither ripgrep (rg) nor grep is available."
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

EXISTING_INCLUDE_PATHS=()
for include_path in "${INCLUDE_PATHS[@]}"; do
  if [[ -e "$include_path" ]]; then
    EXISTING_INCLUDE_PATHS+=("$include_path")
  fi
done

if [[ "${#EXISTING_INCLUDE_PATHS[@]}" -eq 0 ]]; then
  echo "Tenant-decoupling validation skipped: include paths not found."
  exit 0
fi

for token in "${TOKENS[@]}"; do
  if [[ "$SEARCH_TOOL" == "rg" ]]; then
    MATCHES="$(rg -n --no-heading --fixed-strings "${ALLOWLIST_GLOBS[@]}" \
      "$token" "${EXISTING_INCLUDE_PATHS[@]}" || true)"
  else
    MATCHES="$(grep -RInF --binary-files=without-match \
      --exclude-dir=docs \
      --exclude-dir=data \
      --exclude-dir=node_modules \
      --exclude-dir=dist \
      --exclude-dir=coverage \
      --exclude='*.lock' \
      --exclude='CHANGELOG.md' \
      --exclude='PROJECT_CONTEXT.md' \
      --exclude='CODEOWNERS' \
      --exclude='branch-protection.md' \
      --exclude='IMPLEMENTATION_SUMMARY.md' \
      --exclude='validate-tenant-decoupling.sh' \
      "$token" "${EXISTING_INCLUDE_PATHS[@]}" || true)"
  fi

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
