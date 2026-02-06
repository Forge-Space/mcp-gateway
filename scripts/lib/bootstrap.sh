# Shared bootstrap: script dir, repo root, logging, env.
# Source from scripts as: source "$(dirname "${BASH_SOURCE[0]}")/lib/bootstrap.sh"
# Then call load_env; scripts that require .env should exit if load_env fails.
_BOOTSTRAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$(cd "$_BOOTSTRAP_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || true
# shellcheck source=scripts/lib/log.sh
source "$SCRIPT_DIR/lib/log.sh" 2>/dev/null || true

load_env() {
  if [[ ! -f "$REPO_ROOT/.env" ]]; then
    return 1
  fi
  set -a
  # shellcheck source=.env
  source "$REPO_ROOT/.env"
  set +a
  return 0
}
