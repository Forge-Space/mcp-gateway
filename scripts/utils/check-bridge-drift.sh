#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

canonical_files=(
  "README.md"
  "apps/web-admin/src/app/ide-integration/page.tsx"
  "scripts/setup-forge-space-mcp.sh"
  "scripts/ide-setup.py"
  "docs/operations/AI_USAGE.md"
  "docs/setup/IDE_SETUP_GUIDE.md"
  "docs/setup/ENVIRONMENT_CONFIGURATION.md"
)

for path in "${canonical_files[@]}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing canonical file for bridge drift check: ${path}" >&2
    exit 1
  fi
done

check_forbidden() {
  local pattern="$1"
  local label="$2"
  local hits
  hits="$(grep -nH -E "${pattern}" "${canonical_files[@]}" || true)"
  if [[ -n "${hits}" ]]; then
    echo "Forbidden ${label} found in canonical setup surfaces:" >&2
    echo "${hits}" >&2
    exit 1
  fi
}

check_forbidden 'cursor-mcp-wrapper\.sh' 'wrapper alias reference'
check_forbidden '\.cursor-mcp-url' 'legacy URL file reference'
check_forbidden 'make use-cursor-wrapper' 'legacy make target reference'

npx_hits="$(grep -nH -E 'npx[[:space:]]+-y[[:space:]]+@forgespace/mcp-gateway-client' "${canonical_files[@]}" || true)"
if [[ -n "${npx_hits}" ]]; then
  unexpected="$(echo "${npx_hits}" | grep -vE 'not resolvable on npm|not a supported setup path|unavailable until' || true)"
  if [[ -n "${unexpected}" ]]; then
    echo "Unsupported active NPX setup claims found in canonical setup surfaces:" >&2
    echo "${unexpected}" >&2
    exit 1
  fi
fi

echo "Bridge drift check passed."
