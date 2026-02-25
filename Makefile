# MCP Gateway - Simplified Makefile (Phase 3: Command Simplification)
# Reduced from 50+ targets to 12 core targets for easier onboarding

.PHONY: setup start stop register status ide-setup auth lint lint-strict test deps help clean quickstart \
       n8n-start n8n-stop n8n-logs n8n-backup n8n-health n8n-secrets

# Default target
.DEFAULT_GOAL := help

# === Core Commands (12 targets total) ===

setup: ## Interactive configuration wizard (replaces setup, setup-dev, config-wizard)
	@echo "🚀 Starting MCP Gateway Setup Wizard..."
	python3 scripts/setup-wizard.py

start: ## Start the gateway stack (Docker Compose)
	@echo "🚀 Starting MCP Gateway services..."
	./start.sh

stop: ## Stop the gateway stack
	@echo "🛑 Stopping MCP Gateway services..."
	./start.sh stop

register: ## Register gateways and virtual servers (replaces register, register-wait, register-enhanced)
	@echo "📝 Registering gateways and virtual servers..."
	@if [ "$(WAIT)" = "true" ]; then \
		REGISTER_WAIT_SECONDS=30 ./scripts/gateway/register.sh; \
	else \
		./scripts/gateway/register.sh; \
	fi

status: ## Comprehensive system status check (replaces status, status-detailed, status-json, list-servers)
	@echo "📊 Checking system status..."
	@if [ "$(FORMAT)" = "json" ]; then \
		python3 scripts/status.py --json; \
	elif [ "$(FORMAT)" = "detailed" ]; then \
		python3 scripts/status.py --detailed; \
	else \
		python3 scripts/status.py; \
	fi

ide-setup: ## Unified IDE setup and management (replaces all cursor-specific commands)
	@if [ -z "$(IDE)" ]; then \
		echo "💻 IDE Setup Usage:"; \
		echo "  make ide-setup IDE=<cursor|windsurf|vscode|claude|all>"; \
		echo "  make ide-setup IDE=<name> ACTION=<install|backup|restore|status>"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make ide-setup IDE=cursor                    # Install Cursor"; \
		echo "  make ide-setup IDE=all                       # Install all IDEs"; \
		echo "  make ide-setup IDE=windsurf ACTION=backup     # Backup Windsurf"; \
		exit 1; \
	fi
	@echo "💻 Configuring $(IDE)..."
	python3 scripts/ide-setup.py setup $(IDE) --action $(or $(ACTION),install)

auth: ## Authentication commands (replaces jwt, auth-check, auth-refresh, generate-secrets)
	@if [ -z "$(ACTION)" ]; then \
		echo "🔐 Authentication Usage:"; \
		echo "  make auth ACTION=generate     # Generate JWT token"; \
		echo "  make auth ACTION=check         # Check JWT configuration"; \
		echo "  make auth ACTION=refresh       # Refresh JWT token"; \
		echo "  make auth ACTION=secrets       # Generate secrets"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make auth ACTION=generate     # Generate JWT"; \
		echo "  make auth ACTION=check         # Check config"; \
		exit 1; \
	fi
	@echo "🔐 Authentication: $(ACTION)..."
	@if [ "$(ACTION)" = "generate" ]; then \
		bash -c 'set -a; [ -f .env ] && . ./.env; set +a; \
		if python3 scripts/utils/create-jwt.py; then \
			echo "✅ JWT token generated"; \
		else \
			echo "❌ JWT generation failed"; \
		fi'; \
	elif [ "$(ACTION)" = "check" ]; then \
		if [ ! -f .env ]; then echo "❌ .env file not found"; exit 1; fi; \
		set -a; . ./.env; set +a; \
		if [ -z "$$JWT_SECRET_KEY" ]; then echo "❌ JWT_SECRET_KEY not set"; exit 1; fi; \
		if [ $${#JWT_SECRET_KEY} -lt 32 ]; then echo "❌ JWT_SECRET_KEY too short"; exit 1; fi; \
		echo "✅ JWT configuration valid"; \
	elif [ "$(ACTION)" = "refresh" ]; then \
		bash -c 'set -a; [ -f .env ] && . ./.env; set +a; \
		if python3 scripts/utils/create-jwt.py --exp 20160; then \
			echo "✅ JWT token refreshed (14 days)"; \
		else \
			echo "❌ JWT refresh failed"; \
		fi'; \
	elif [ "$(ACTION)" = "secrets" ]; then \
		echo "# Add these to .env (min 32 chars):"; \
		echo "JWT_SECRET_KEY=$$(openssl rand -base64 32)"; \
		echo "AUTH_ENCRYPTION_SECRET=$$(openssl rand -base64 32)"; \
	else \
		echo "❌ Unknown action: $(ACTION)"; \
		exit 1; \
	fi

lint: ## Run all linters (replaces lint-python, lint-typescript, shellcheck, lint-all)
	@echo "🔍 Running all linters..."
	@echo "==> Python..."
	ruff check tool_router/ || echo "⚠️ Python lint issues found"
	@echo "==> TypeScript..."
	@if [ -f package.json ]; then npm run lint || echo "⚠️ TypeScript lint issues found"; fi
	@echo "==> Shell scripts..."
	@SCRIPTS=$$(find scripts/ -name '*.sh' 2>/dev/null); \
	if [ -f start.sh ]; then SCRIPTS="start.sh $$SCRIPTS"; fi; \
	if [ -n "$$SCRIPTS" ]; then shellcheck $$SCRIPTS || echo "⚠️ Shell lint issues found"; fi

lint-strict: ## Run all linters without fallbacks (CI-friendly)
	@echo "🔍 Running strict linters (no fallbacks)..."
	@echo "==> Python..."
	ruff check tool_router/
	@echo "==> TypeScript..."
	@if [ -f package.json ]; then npm run lint; fi
	@echo "==> Shell scripts..."
	@SCRIPTS=$$(find scripts/ -name '*.sh' 2>/dev/null); \
	if [ -f start.sh ]; then SCRIPTS="start.sh $$SCRIPTS"; fi; \
	if [ -n "$$SCRIPTS" ]; then shellcheck $$SCRIPTS; fi

test: ## Run tests (replaces test, test-coverage)
	@echo "🧪 Running tests..."
	pytest tool_router/tests/ dribbble_mcp/tests/ \
		--ignore=tool_router/tests/performance \
		--ignore=tool_router/tests/integration \
		--ignore=tool_router/tests/test_training \
		--ignore=tool_router/tests/training \
		--ignore=tool_router/tests/unit/test_training_pipeline.py \
		--ignore=tool_router/tests/unit/test_specialist_coordinator.py \
		--ignore=tool_router/tests/unit/test_ui_specialist.py \
		--ignore=tool_router/tests/test_cache_basic.py \
		--ignore=tool_router/tests/test_cache_compliance.py \
		--timeout=30 --maxfail=10

deps: ## Dependency management (replaces deps-check, deps-update, pre-commit-install)
	@if [ -z "$(ACTION)" ]; then \
		echo "📦 Dependency Management Usage:"; \
		echo "  make deps ACTION=check         # Check for updates"; \
		echo "  make deps ACTION=update        # Update dependencies"; \
		echo "  make deps ACTION=hooks         # Install pre-commit hooks"; \
		echo "  make deps ACTION=install        # Install all dependencies"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make deps ACTION=check         # Check npm updates"; \
		echo "  make deps ACTION=install        # Install npm + pip"; \
		exit 1; \
	fi
	@echo "📦 Dependencies: $(ACTION)..."
	@if [ "$(ACTION)" = "check" ]; then \
		if [ -f package.json ]; then npm run deps:check || echo "⚠️ npm updates available"; fi; \
	elif [ "$(ACTION)" = "update" ]; then \
		if [ -f package.json ]; then npm run deps:update:interactive; fi; \
	elif [ "$(ACTION)" = "hooks" ]; then \
		pre-commit install && echo "✅ Pre-commit hooks installed"; \
	elif [ "$(ACTION)" = "install" ]; then \
		echo "Installing all dependencies..."; \
		if [ -f package.json ]; then npm install; fi; \
		if [ -f requirements.txt ]; then pip3 install -r requirements.txt; fi; \
		if [ -f requirements-dev.txt ]; then pip3 install -r requirements-dev.txt; fi; \
	else \
		echo "❌ Unknown action: $(ACTION)"; \
		exit 1; \
	fi

help: ## Show help and examples (replaces help, help-topics, help-examples, list-prompts)
	@if [ -z "$(TOPIC)" ]; then \
		echo "🚀 MCP Gateway - Simplified Command Interface"; \
		echo ""; \
		echo "📋 Core Commands (12 total):"; \
		echo "  setup              # Interactive configuration wizard"; \
		echo "  start              # Start gateway services"; \
		echo "  stop               # Stop gateway services"; \
		echo "  register           # Register gateways and servers"; \
		echo "  status             # Check system status"; \
		echo "  ide-setup          # Configure IDE connections"; \
		echo "  auth               # Authentication management"; \
		echo "  lint               # Run code linters"; \
		echo "  test               # Run tests"; \
		echo "  deps               # Dependency management"; \
		echo "  help               # Show this help"; \
		echo "  clean              # Clean up and reset"; \
		echo ""; \
		echo "🔧 Advanced Options:"; \
		echo "  make status FORMAT=json|detailed     # Status formats"; \
		echo "  make register WAIT=true              # Wait for readiness"; \
		echo "  make ide-setup IDE=all               # Configure all IDEs"; \
		echo "  make auth ACTION=generate|check|refresh|secrets"; \
		echo "  make test COVERAGE=true               # Run with coverage"; \
		echo "  make deps ACTION=check|update|hooks|install"; \
		echo "  make help TOPIC=setup|ide|auth|services|n8n"; \
		echo ""; \
		echo "📚 Quick Start:"; \
		echo "  1. make setup                    # Configure everything"; \
		echo "  2. make start                    # Start services"; \
		echo "  3. make register                 # Register servers"; \
		echo "  4. make status                   # Check status"; \
		echo "  5. make ide-setup IDE=all        # Configure IDEs"; \
		echo ""; \
		echo "🤖 n8n Automation:"; \
		echo "  make n8n-start                   # Start n8n"; \
		echo "  make n8n-stop                    # Stop n8n"; \
		echo "  make n8n-logs                    # Tail n8n logs"; \
		echo "  make n8n-health                  # Health check"; \
		echo "  make n8n-backup                  # Export workflows"; \
		echo "  make n8n-secrets                 # Generate webhook secrets"; \
	else \
		echo "📚 Help: $(TOPIC)"; \
		case "$(TOPIC)" in \
			setup) \
				echo "Setup wizard configures:"; \
				echo "• Environment variables (.env)"; \
				echo "• Authentication secrets"; \
				echo "• IDE connections"; \
				echo "• Development environment"; \
				echo "• Service registration"; \
				echo ""; \
				echo "Usage: make setup"; \
				;; \
			ide) \
				echo "IDE configuration supports:"; \
				echo "• Cursor, VSCode, Windsurf, Claude Desktop"; \
				echo "• Automatic detection and setup"; \
				echo "• Configuration backup/restore"; \
				echo ""; \
				echo "Usage: make ide-setup IDE=<name|all>"; \
				;; \
			auth) \
				echo "Authentication management:"; \
				echo "• JWT token generation"; \
				echo "• Configuration validation"; \
				echo "• Secret key generation"; \
				echo "• Token refresh"; \
				echo ""; \
				echo "Usage: make auth ACTION=generate|check|refresh|secrets"; \
				;; \
			services) \
				echo "Service management:"; \
				echo "• Gateway start/stop"; \
				echo "• Server registration"; \
				echo "• Status monitoring"; \
				echo "• Health checks"; \
				echo ""; \
				echo "Usage: make start|stop|register|status"; \
				;; \
			n8n) \
				echo "n8n automation layer:"; \
				echo "• Self-hosted workflow automation (Docker)"; \
				echo "• CI failure alerts, security advisories"; \
				echo "• Cross-repo release notifications"; \
				echo "• Stale PR reminders, velocity reports"; \
				echo "• Docker health monitoring"; \
				echo ""; \
				echo "Setup:"; \
				echo "  1. cp .env.n8n.example .env.n8n"; \
				echo "  2. Fill in secrets (make n8n-secrets)"; \
				echo "  3. make n8n-start"; \
				echo "  4. Open http://localhost:5678"; \
				echo ""; \
				echo "Usage: make n8n-start|n8n-stop|n8n-logs|n8n-health|n8n-backup|n8n-secrets"; \
				;; \
			*) \
				echo "Topic '$(TOPIC)' not found. Available: setup, ide, auth, services, n8n"; \
				;; \
		esac; \
	fi

clean: ## Clean up and reset (replaces reset-db, cleanup-duplicates, config-cleanup)
	@echo "🧹 Cleaning up MCP Gateway..."
	@echo "Stopping services..."
	./start.sh stop
	@echo "Cleaning database..."
	rm -f ./data/mcp.db ./data/mcp.db-shm ./data/mcp.db-wal
	@echo "Cleaning duplicates..."
	./scripts/virtual-servers/cleanup-duplicates.sh 2>/dev/null || true
	@echo "✅ Cleanup complete. Run 'make setup && make start && make register' to recreate."

# === n8n Automation ===

n8n-start: ## Start n8n automation service
	@if [ ! -f .env.n8n ]; then \
		echo "Missing .env.n8n — copy from .env.n8n.example and fill in values"; \
		exit 1; \
	fi
	docker compose -f docker-compose.n8n.yml up -d

n8n-stop: ## Stop n8n automation service
	docker compose -f docker-compose.n8n.yml stop

n8n-logs: ## Tail n8n container logs
	docker logs -f forge-n8n

n8n-backup: ## Export all n8n workflows to n8n-workflows/
	docker exec forge-n8n n8n export:workflow --all \
		--output=/home/node/.n8n/backups/workflows.json
	docker cp forge-n8n:/home/node/.n8n/backups/workflows.json \
		n8n-workflows/backup-$$(date +%Y%m%d).json
	@echo "Backup saved to n8n-workflows/backup-$$(date +%Y%m%d).json"

n8n-health: ## Check n8n health
	@curl -sf http://localhost:5678/healthz > /dev/null \
		&& echo "n8n is healthy" \
		|| echo "n8n is not responding"

n8n-secrets: ## Generate webhook secrets for .env.n8n
	@echo "# Paste into .env.n8n:"
	@echo "WEBHOOK_SECRET_CI_FAILURE=$$(openssl rand -hex 32)"
	@echo "WEBHOOK_SECRET_SECURITY_ADVISORY=$$(openssl rand -hex 32)"
	@echo "WEBHOOK_SECRET_RELEASE_NOTIFIER=$$(openssl rand -hex 32)"
	@echo "WEBHOOK_SECRET_STALE_PR=$$(openssl rand -hex 32)"
	@echo "WEBHOOK_SECRET_VELOCITY_REPORT=$$(openssl rand -hex 32)"
	@echo "WEBHOOK_SECRET_DOCKER_HEALTH=$$(openssl rand -hex 32)"

# === Quick Start Examples ===
quickstart: ## Quick start for new users
	@echo "🚀 MCP Gateway Quick Start"
	@echo "========================"
	@echo "1. make setup"
	@echo "2. make start"
	@echo "3. make register"
	@echo "4. make status"
	@echo "5. make ide-setup IDE=all"
	@echo ""
	@echo "📚 More help: make help"
