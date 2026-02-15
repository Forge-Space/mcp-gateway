.PHONY: all clean start stop gateway-only register register-wait jwt list-prompts list-servers refresh-cursor-jwt use-cursor-wrapper verify-cursor-setup cursor-pull reset-db cleanup-duplicates generate-secrets lint lint-python lint-typescript lint-all shellcheck test test-coverage format format-python format-typescript deps-check deps-update pre-commit-install help

# Default target
.DEFAULT_GOAL := help

all: help ## Default target (shows help)

clean: reset-db cleanup-duplicates ## Clean up database and duplicates

help: ## Show this help message
	@echo "MCP Gateway - Available Make targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

# === Setup & Secrets ===
generate-secrets: ## Generate JWT and encryption secrets for .env
	@echo "# Add these to .env (min 32 chars; weak secrets cause 'Server disconnected' / context-forge errors):"
	@echo "JWT_SECRET_KEY=$(shell openssl rand -base64 32)"
	@echo "AUTH_ENCRYPTION_SECRET=$(shell openssl rand -base64 32)"

# === Gateway Management ===
start: ## Start the gateway stack (Docker Compose)
	./start.sh

stop: ## Stop the gateway stack
	./start.sh stop

reset-db: ## Reset the database (WARNING: deletes all data)
	./start.sh stop
	rm -f ./data/mcp.db ./data/mcp.db-shm ./data/mcp.db-wal
	@echo "DB removed. Run 'make start' then 'make register' to recreate gateways."

gateway-only: ## Start only the gateway service
	./start.sh gateway-only

register: ## Register gateways and virtual servers
	./scripts/gateway/register.sh

register-wait: ## Register with 30s wait for gateway readiness
	REGISTER_WAIT_SECONDS=30 ./scripts/gateway/register.sh

jwt: ## Generate JWT token for API access
	@bash -c 'set -a; [ -f .env ] && . ./.env; set +a; \
	if python3 "$(CURDIR)/scripts/utils/create-jwt.py"; then \
		exit 0; \
	fi; \
	echo "Local JWT generation failed, trying Docker fallback..."; \
	if docker exec "$${MCPGATEWAY_CONTAINER:-mcpgateway}" python3 -m mcpgateway.utils.create_jwt_token --username "$$PLATFORM_ADMIN_EMAIL" --exp 10080 --secret "$$JWT_SECRET_KEY"; then \
		exit 0; \
	fi; \
	echo "ERROR: JWT generation failed. Check:" >&2; \
	echo "  - PLATFORM_ADMIN_EMAIL=$$PLATFORM_ADMIN_EMAIL" >&2; \
	echo "  - JWT_SECRET_KEY is set (length: $${#JWT_SECRET_KEY})" >&2; \
	echo "  - Container: $${MCPGATEWAY_CONTAINER:-mcpgateway}" >&2; \
	exit 1'

list-prompts: ## List available prompts
	./scripts/gateway/list-prompts.sh

list-servers: ## List virtual servers
	./scripts/virtual-servers/list.sh

cleanup-duplicates: ## Clean up duplicate virtual servers
	./scripts/virtual-servers/cleanup-duplicates.sh

# === Cursor IDE Integration ===
refresh-cursor-jwt: ## Refresh JWT for Cursor IDE
	./scripts/cursor/refresh-jwt.sh

use-cursor-wrapper: ## Set up Cursor wrapper script
	./scripts/cursor/use-wrapper.sh

verify-cursor-setup: ## Verify Cursor setup
	./scripts/cursor/verify-setup.sh

cursor-pull: ## Pull Context Forge Docker image
	@echo "Pulling Context Forge image (used by Cursor wrapper; avoids first-start timeout)..."
	docker pull ghcr.io/ibm/mcp-context-forge:1.0.0-BETA-2

# === Linting & Quality ===
lint: lint-python lint-typescript shellcheck ## Run all linters (Python, TypeScript, Shell)

lint-python: ## Lint Python code with Ruff
	@echo "==> Linting Python code..."
	ruff check tool_router/

lint-typescript: ## Lint TypeScript code with ESLint
	@echo "==> Linting TypeScript code..."
	@command -v npm >/dev/null 2>&1 || { echo "ERROR: npm not found. Install Node.js first."; exit 1; }
	npm run lint

lint-all: lint ## Alias for 'lint' target

shellcheck: ## Lint shell scripts with shellcheck
	@echo "==> Linting shell scripts..."
	@SCRIPTS=$$(find scripts/ -name '*.sh' 2>/dev/null); \
	if [ -f start.sh ]; then SCRIPTS="start.sh $$SCRIPTS"; fi; \
	if [ -n "$$SCRIPTS" ]; then \
		shellcheck -s bash -S warning $$SCRIPTS; \
	else \
		echo "No shell scripts found to check."; \
	fi

# === Formatting ===
format: format-python format-typescript ## Format all code (Python, TypeScript)

format-python: ## Format Python code with Ruff
	@echo "==> Formatting Python code..."
	ruff format tool_router/

format-typescript: ## Format TypeScript code with Prettier
	@echo "==> Formatting TypeScript code..."
	@command -v npm >/dev/null 2>&1 || { echo "ERROR: npm not found. Install Node.js first."; exit 1; }
	npm run format

# === Testing ===
test: ## Run Python tests with pytest
	@echo "==> Running Python tests..."
	pytest tool_router/ -v

test-coverage: ## Run tests with coverage report
	@echo "==> Running tests with coverage..."
	pytest tool_router/ -v --cov=tool_router --cov-report=term-missing --cov-report=html

# === Dependencies ===
deps-check: ## Check for outdated npm dependencies
	@echo "==> Checking npm dependencies..."
	@command -v npm >/dev/null 2>&1 || { echo "ERROR: npm not found. Install Node.js first."; exit 1; }
	npm run deps:check

deps-update: ## Update npm dependencies interactively
	@echo "==> Updating npm dependencies..."
	@command -v npm >/dev/null 2>&1 || { echo "ERROR: npm not found. Install Node.js first."; exit 1; }
	npm run deps:update:interactive

# === Pre-commit Hooks ===
pre-commit-install: ## Install pre-commit hooks
	pre-commit install
	@echo "Pre-commit hooks installed. Run 'pre-commit run --all-files' to check the whole repo."

pre-commit-run: ## Run pre-commit hooks on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hook versions
	pre-commit autoupdate
