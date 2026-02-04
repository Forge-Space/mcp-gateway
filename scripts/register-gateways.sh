#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f .env ]]; then
  echo "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."
  exit 1
fi

set -a
source .env
set +a

echo "Register gateways – checking environment..."

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
max_wait="${REGISTER_GATEWAY_MAX_WAIT:-90}"
interval=3

try_health() {
  local base="$1" limit="$2"
  local elapsed=0 code=""
  while [[ "$elapsed" -lt "$limit" ]]; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$base/health" 2>/dev/null || true)
    if [[ "$code" == "200" ]]; then
      printf '\r  OK after %ds.    \n' "$elapsed" >&2
      echo "$code"
      return
    fi
    printf '\r  %ds elapsed (waiting for 200)...   ' "$elapsed" >&2
    sleep "$interval"
    elapsed=$((elapsed + interval))
  done
  echo >&2
  echo "${code:-000}"
}

if [[ "$GATEWAY_URL" =~ 127\.0\.0\.1 ]]; then
  first_url="${GATEWAY_URL//127.0.0.1/localhost}"
  second_url="$GATEWAY_URL"
elif [[ "$GATEWAY_URL" =~ localhost ]]; then
  first_url="$GATEWAY_URL"
  second_url="${GATEWAY_URL//localhost/127.0.0.1}"
else
  first_url="$GATEWAY_URL"
  second_url=""
fi

echo "Waiting for gateway at $first_url (up to ${max_wait}s)..."
code=$(try_health "$first_url" "$max_wait")
if [[ "$code" != "200" ]] && [[ -n "$second_url" ]]; then
  echo "Trying alternate URL: $second_url"
  code=$(try_health "$second_url" "$max_wait")
  [[ "$code" == "200" ]] && GATEWAY_URL="$second_url"
elif [[ "$code" == "200" ]] && [[ "$first_url" != "$GATEWAY_URL" ]]; then
  GATEWAY_URL="$first_url"
fi
if [[ "$code" != "200" ]]; then
  echo "Gateway not reachable at $GATEWAY_URL (health got ${code} after ${max_wait}s)."
  echo "Start with ./start.sh. If already started: docker compose ps gateway && docker compose logs gateway"
  exit 1
fi
echo "Gateway ready at $GATEWAY_URL"

if [[ -n "${REGISTER_WAIT_SECONDS:-}" ]] && [[ "${REGISTER_WAIT_SECONDS}" -gt 0 ]] 2>/dev/null; then
  echo "Waiting ${REGISTER_WAIT_SECONDS}s for translate containers to be ready..."
  left="${REGISTER_WAIT_SECONDS}"
  while [[ "$left" -gt 0 ]]; do
    printf "\r  %ds remaining...   " "$left"
    if [[ "$left" -ge 5 ]]; then step=5; else step=$left; fi
    sleep "$step"
    left=$((left - step))
  done
  echo ""
fi

echo "Generating JWT for admin API..."
if docker compose version &>/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE="docker-compose"
else
  COMPOSE=""
fi

if [[ -n "$COMPOSE" ]] && $COMPOSE ps gateway -q 2>/dev/null | grep -q .; then
  JWT=$($COMPOSE exec -T gateway python3 -m mcpgateway.utils.create_jwt_token \
    --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null)
else
  CONTAINER="${MCPGATEWAY_CONTAINER:-mcpgateway}"
  if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
    echo "Gateway is not running. Start with ./start.sh (from repo root)."
    exit 1
  fi
  JWT=$(docker exec "$CONTAINER" python3 -m mcpgateway.utils.create_jwt_token \
    --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null)
fi
if [[ -z "$JWT" ]]; then
  echo "Failed to generate JWT."
  exit 1
fi
echo "JWT generated."

register() {
  local name="$1" url="$2"
  if [[ "$url" =~ ^https?://([^:/]+):[0-9]+ ]]; then
    local host="${BASH_REMATCH[1]}"
    if [[ -n "$COMPOSE" ]] && ! $COMPOSE ps "$host" -q 2>/dev/null | grep -q .; then
      echo "SKIP $name ($host not running; start with ./start.sh)"
      return
    fi
  fi
  local json
  json=$(printf '{"name":"%s","url":"%s"}' "$name" "$url")
  local out
  out=$(curl -s -w "\n%{http_code}" --connect-timeout 10 --max-time 45 \
    -X POST -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
    -d "$json" "$GATEWAY_URL/gateways" 2>/dev/null)
  local code
  code=$(echo "$out" | tail -n1)
  if [[ "$code" =~ ^2[0-9][0-9]$ ]]; then
    echo "OK $name"
    return
  fi
  body=$(echo "$out" | sed '$d')
  msg=$(echo "$body" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p')
  detail=$(echo "$body" | sed -n 's/.*"detail":"\([^"]*\)".*/\1/p')
  if [[ "$msg" =~ already\ exists ]] || [[ "$detail" =~ already\ exists ]]; then
    echo "OK $name (already registered)"
    return
  fi
  echo "FAIL $name ($url)"
  if [[ -n "${REGISTER_VERBOSE:-}" ]]; then
    echo "$body"
  else
    [[ -n "$msg" ]] && echo "  $msg"
    [[ -n "$detail" ]] && echo "  detail: $detail"
  fi
  if [[ "$url" =~ :801[0-9]/sse|:802[0-1]/sse ]]; then
    HAS_LOCAL_FAIL=1
    echo "  → docker compose logs gateway; docker compose logs <service>"
  fi
}

HAS_LOCAL_FAIL=0
if [[ -n "$EXTRA_GATEWAYS" ]]; then
  echo "Registering gateways from EXTRA_GATEWAYS..."
  while IFS= read -r line; do
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    IFS='|' read -r name url _ <<< "$line"
    register "$name" "$url"
  done <<< "$(echo "$EXTRA_GATEWAYS" | tr ',' '\n')"
fi

if [[ -f "$SCRIPT_DIR/gateways.txt" ]]; then
  echo "Registering gateways from scripts/gateways.txt..."
  while IFS= read -r line || [[ -n "$line" ]]; do
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    IFS='|' read -r name url _ <<< "$line"
    register "$name" "$url"
  done < "$SCRIPT_DIR/gateways.txt"
fi

if [[ -z "$EXTRA_GATEWAYS" && ! -f "$SCRIPT_DIR/gateways.txt" ]]; then
  echo "No gateways to register. Set EXTRA_GATEWAYS in .env or add lines to scripts/gateways.txt (Name|URL|Transport)."
else
  echo "Done."
  if [[ "${HAS_LOCAL_FAIL:-0}" -eq 1 ]]; then
    echo "If local gateways failed: REGISTER_VERBOSE=1 for full API response; REGISTER_WAIT_SECONDS=30 if translate containers were still starting; docker compose ps to confirm all services are up."
  fi
fi
