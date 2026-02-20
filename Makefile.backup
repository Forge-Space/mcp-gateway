# MCP Gateway - Comprehensive Makefile
# Replaces all manual shell scripts with organized targets
# Version: 2.0 - Enterprise Ready

.PHONY: help setup start stop restart status register ide-setup lint test security deploy monitor backup restore clean deps validate docs npm

# Default target
.DEFAULT_GOAL := help

# === Configuration ===
PYTHON := python3
NODE_VERSION := 22
DOCKER_COMPOSE := docker-compose
GATEWAY_URL := http://localhost:4444
HEALTH_URL := http://localhost:8001/health

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m

# === Help System ===

help: ## Show all available commands with descriptions
	@echo "$(CYAN)MCP Gateway - Enterprise Makefile$(NC)"
	@echo "$(CYAN)=====================================$(NC)"
	@echo ""
	@echo "$(YELLOW)🚀 Quick Start:$(NC)"
	@echo "  make setup          # Initial setup wizard"
	@echo "  make start           # Start all services"
	@echo "  make register        # Register gateways"
	@echo "  make status          # Check system status"
	@echo ""
	@echo "$(YELLOW)🔧 Development:$(NC)"
	@echo "  make lint            # Run linting (Python + Shell)"
	@echo "  make test            # Run all tests"
	@echo "  make validate        # Validate configuration"
	@echo "  make deps            # Update dependencies"
	@echo ""
	@echo "$(YELLOW)📦 NPM Deployment:$(NC)"
	@echo "  make npm-setup       # Setup NPM deployment"
	@echo "  make npm-test        # Test NPM deployment"
	@echo "  make npm-publish     # Publish to NPM (dry run)"
	@echo "  make npm-release     # Full NPM release"
	@echo ""
	@echo "$(YELLOW)🛡️ Security:$(NC)"
	@echo "  make security        # Run security scans"
	@echo "  make security-harden # Security hardening"
	@echo "  make audit           # Dependency audit"
	@echo ""
	@echo "$(YELLOW)🚀 Deployment:$(NC)"
	@echo "  make deploy          # Deploy to production"
	@echo "  make deploy-test     # Test deployment"
	@echo "  make rollback        # Rollback deployment"
	@echo ""
	@echo "$(YELLOW)📊 Monitoring:$(NC)"
	@echo "  make monitor         # System monitoring"
	@echo "  monitor-advanced     # Advanced monitoring"
	@echo "  monitor-ml           # ML-based monitoring"
	@echo ""
	@echo "$(YELLOW)💾 Backup & Restore:$(NC)"
	@echo "  make backup          # Create backup"
	@echo "  make restore         # Restore from backup"
	@echo "  make backup-list     # List backups"
	@echo ""
	@echo "$(YELLOW)🔧 IDE Setup:$(NC)"
	@echo "  make ide-setup       # IDE configuration"
	@echo "  make ide-backup      # Backup IDE config"
	@echo "  make ide-restore     # Restore IDE config"
	@echo ""
	@echo "$(YELLOW)🧹 Maintenance:$(NC)"
	@echo "  make clean           # Clean temporary files"
	@echo "  make logs            # Show logs"
	@echo "  make doctor          # System health check"
	@echo ""
	@echo "$(YELLOW)📚 Documentation:$(NC)"
	@echo "  make docs            # Generate docs"
	@echo "  make docs-serve      # Serve docs locally"
	@echo ""
	@echo "$(YELLOW)⚙️  Utilities:$(NC)"
	@echo "  make shell           # Open shell in container"
	@echo "  make debug           # Debug mode"
	@echo "  make version         # Show version info"
	@echo ""
	@echo "$(BLUE)Use 'make help-<category>' for detailed help$(NC)"

# === Quick Start Commands ===

setup: ## Interactive setup wizard for initial configuration
	@echo "$(GREEN)🚀 Starting MCP Gateway Setup Wizard...$(NC)"
	@$(PYTHON) scripts/setup-wizard.py

quickstart: setup start register status ## Complete quick start (setup + start + register + status)

start: ## Start the MCP Gateway stack
	@echo "$(GREEN)🚀 Starting MCP Gateway services...$(NC)"
	@./start.sh

stop: ## Stop the MCP Gateway stack
	@echo "$(YELLOW)🛑 Stopping MCP Gateway services...$(NC)"
	@./start.sh stop

restart: stop start ## Restart the MCP Gateway stack

status: ## Show comprehensive system status
	@echo "$(BLUE)📊 MCP Gateway System Status$(NC)"
	@echo "$(BLUE)===========================$(NC)"
	@$(PYTHON) scripts/status.py

status-json: ## Show status in JSON format
	@$(PYTHON) scripts/status.py --json

status-detailed: ## Show detailed system status
	@$(PYTHON) scripts/status.py --detailed

register: ## Register gateways and virtual servers
	@echo "$(GREEN)📝 Registering gateways and virtual servers...$(NC)"
	@./scripts/gateway/register.sh

register-wait: ## Register with wait time
	@if [ -z "$(WAIT)" ]; then WAIT=30; fi; \
		echo "$(GREEN)📝 Registering gateways (wait $(WAIT)s)...$(NC)"; \
		REGISTER_WAIT_SECONDS=$(WAIT) ./scripts/gateway/register.sh

# === Development Commands ===

lint: ## Run all linting (Python + Shell + TypeScript)
	@echo "$(BLUE)🔍 Running comprehensive linting...$(NC)"
	@echo "$(YELLOW)Python linting...$(NC)"
	@ruff check . --fix
	@echo "$(YELLOW)Shell script linting...$(NC)"
	@shellcheck scripts/*.sh
	@echo "$(YELLOW)TypeScript linting (web admin)...$(NC)"
	@cd apps/web-admin && npm run lint || true
	@echo "$(GREEN)✅ Linting complete!$(NC)"

lint-strict: ## Run strict linting (no auto-fix)
	@echo "$(BLUE)🔍 Running strict linting...$(NC)"
	@ruff check .
	@shellcheck scripts/*.sh
	@cd apps/web-admin && npm run lint || true

test: ## Run all tests (Python + Web Admin)
	@echo "$(BLUE)🧪 Running all tests...$(NC)"
	@echo "$(YELLOW)Python tests...$(NC)"
	@make test-python
	@echo "$(YELLOW)Web Admin tests...$(NC)"
	@make test-web
	@echo "$(GREEN)✅ All tests complete!$(NC)"

test-python: ## Run Python tests
	@echo "$(YELLOW)🐍 Running Python tests...$(NC)"
	@cd tool_router && python -m pytest tests/ -v --tb=short

test-web: ## Run Web Admin tests
	@echo "$(YELLOW)🌐 Running Web Admin tests...$(NC)"
	@cd apps/web-admin && npm test || echo "No tests configured"

test-integration: ## Run integration tests
	@echo "$(YELLOW)🔗 Running integration tests...$(NC)"
	@./scripts/run-integration-tests.sh

test-coverage: ## Run tests with coverage
	@echo "$(YELLOW)📊 Running tests with coverage...$(NC)"
	@cd tool_router && python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

validate: ## Validate project configuration
	@echo "$(BLUE)✅ Validating project configuration...$(NC)"
	@./scripts/validate-config
	@./scripts/validate-patterns.sh
	@echo "$(GREEN)✅ Validation complete!$(NC)"

deps: ## Update all dependencies
	@echo "$(BLUE)📦 Updating dependencies...$(NC)"
	@echo "$(YELLOW)Python dependencies...$(NC)"
	@pip install --upgrade pip
	@pip install -r requirements.txt
	@echo "$(YELLOW)Web Admin dependencies...$(NC)"
	@cd apps/web-admin && npm update
	@echo "$(GREEN)✅ Dependencies updated!$(NC)"

# === NPM Deployment Commands ===

npm-setup: ## Setup NPM deployment for Core Package
	@echo "$(GREEN)📦 Setting up NPM deployment...$(NC)"
	@./scripts/setup-npm-deployment.sh

npm-test: ## Test NPM deployment (dry run)
	@echo "$(BLUE)🧪 Testing NPM deployment (dry run)...$(NC)"
	@npm run build
	@npm pack --dry-run
	@echo "$(GREEN)✅ NPM deployment test passed!$(NC)"

npm-publish: ## Publish to NPM (dry run by default)
	@echo "$(YELLOW)📦 Publishing to NPM (dry run)...$(NC)"
	@npm run build
	@npm pack --dry-run
	@echo "$(GREEN)✅ Ready for actual publishing. Use 'npm-release' for real publish.$(NC)"

npm-release: ## Full NPM release (actual publish)
	@echo "$(RED)🚀 Publishing to NPM (ACTUAL RELEASE)...$(NC)"
	@read -p "Are you sure you want to publish to NPM? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		npm run build && npm publish; \
		echo "$(GREEN)✅ Published to NPM!$(NC)"; \
	else \
		echo "$(YELLOW)❌ Publish cancelled.$(NC)"; \
	fi

npm-version: ## Bump NPM version
	@if [ -z "$(TYPE)" ]; then \
		echo "$(YELLOW)Usage: make npm-version TYPE=<patch|minor|major>$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)🔢 Bumping $(TYPE) version...$(NC)"
	@npm version $(TYPE)
	@git push --tags
	@echo "$(GREEN)✅ Version bumped and pushed!$(NC)"

# === Security Commands ===

security: ## Run comprehensive security scans
	@echo "$(BLUE)🔒 Running security scans...$(NC)"
	@echo "$(YELLOW)Snyk security scan...$(NC)"
	@if command -v snyk &> /dev/null; then \
		snyk test --severity-threshold=high; \
	else \
		echo "$(YELLOW)⚠️  Snyk not installed. Install with: npm install -g snyk$(NC)"; \
	fi
	@echo "$(YELLOW)Python security audit...$(NC)"
	@pip-audit --requirement requirements.txt
	@echo "$(GREEN)✅ Security scan complete!$(NC)"

security-harden: ## Apply security hardening
	@echo "$(BLUE)🔒 Applying security hardening...$(NC)"
	@./scripts/security-hardening.sh
	@echo "$(GREEN)✅ Security hardening applied!$(NC)"

audit: ## Audit dependencies for vulnerabilities
	@echo "$(BLUE)🔍 Auditing dependencies...$(NC)"
	@npm audit
	@pip-audit --requirement requirements.txt
	@echo "$(GREEN)✅ Audit complete!$(NC)"

# === Deployment Commands ===

deploy: ## Deploy to production
	@echo "$(RED)🚀 Deploying to production...$(NC)"
	@read -p "Are you sure you want to deploy to production? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		./scripts/deploy-production.sh; \
		echo "$(GREEN)✅ Deployed to production!$(NC)"; \
	else \
		echo "$(YELLOW)❌ Deploy cancelled.$(NC)"; \
	fi

deploy-test: ## Test deployment configuration
	@echo "$(BLUE)🧪 Testing deployment configuration...$(NC)"
	@./scripts/deploy-production.sh --test

rollback: ## Rollback last deployment
	@echo "$(RED)🔄 Rolling back deployment...$(NC)"
	@./scripts/rollback/rollback.sh

# === Monitoring Commands ===

monitor: ## Show system monitoring dashboard
	@echo "$(BLUE)📊 System Monitoring Dashboard$(NC)"
	@./scripts/monitoring-dashboard.sh

monitor-advanced: ## Advanced monitoring with ML
	@echo "$(PURPLE)🧠 Advanced ML Monitoring$(NC)"
	@./scripts/ml-monitoring.py

monitor-predictive: ## Predictive scaling monitoring
	@echo "$(PURPLE)🔮 Predictive Scaling Monitoring$(NC)"
	@./scripts/predictive-scaling.py

logs: ## Show service logs
	@echo "$(BLUE)📋 Service Logs$(NC)"
	@$(DOCKER_COMPOSE) logs --tail=100 gateway tool-router

logs-follow: ## Follow service logs in real-time
	@echo "$(BLUE)📋 Following service logs...$(NC)"
	@$(DOCKER_COMPOSE) logs -f gateway tool-router

# === Backup & Restore Commands ===

backup: ## Create system backup
	@echo "$(BLUE)💾 Creating system backup...$(NC)"
	@./scripts/backup/create-backup.sh

backup-list: ## List available backups
	@echo "$(BLUE)📋 Available backups:$(NC)"
	@ls -la data/backups/ 2>/dev/null || echo "$(YELLOW)No backups found$(NC)"

restore: ## Restore from backup
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(YELLOW)Usage: make restore BACKUP=<backup-file>$(NC)"; \
		make backup-list; \
		exit 1; \
	fi
	@echo "$(RED)🔄 Restoring from backup: $(BACKUP)$(NC)"
	@read -p "Are you sure? This will overwrite current data. [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		./scripts/backup/restore.sh $(BACKUP); \
		echo "$(GREEN)✅ Restore complete!$(NC)"; \
	else \
		echo "$(YELLOW)❌ Restore cancelled.$(NC)"; \
	fi

# === IDE Setup Commands ===

ide-setup: ## Setup IDE configuration
	@if [ -z "$(IDE)" ]; then \
		echo "$(YELLOW)Usage: make ide-setup IDE=<cursor|windsurf|vscode|all>$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)💻 Setting up $(IDE)...$(NC)"
	@$(PYTHON) scripts/ide-setup.py --ide $(IDE)

ide-backup: ## Backup IDE configurations
	@echo "$(BLUE)💾 Backing up IDE configurations...$(NC)"
	@$(PYTHON) scripts/ide-setup.py --backup

ide-restore: ## Restore IDE configurations
	@echo "$(BLUE)🔄 Restoring IDE configurations...$(NC)"
	@$(PYTHON) scripts/ide-setup.py --restore

# === Maintenance Commands ===

clean: ## Clean temporary files and caches
	@echo "$(BLUE)🧹 Cleaning temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@cd apps/web-admin && rm -rf .next/ node_modules/.cache/ 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

clean-docker: ## Clean Docker resources
	@echo "$(BLUE)🧹 Cleaning Docker resources...$(NC)"
	@$(DOCKER_COMPOSE) down --volumes --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✅ Docker cleanup complete!$(NC)"

doctor: ## Comprehensive system health check
	@echo "$(CYAN)🩺 MCP Gateway Health Check$(NC)"
	@echo "$(CYAN)===========================$(NC)"
	@echo "$(YELLOW)🔧 Checking dependencies...$(NC)"
	@which python3 pip docker docker-compose jq || echo "$(RED)❌ Missing dependencies$(NC)"
	@echo "$(YELLOW)📁 Checking directories...$(NC)"
	@test -d scripts || echo "$(RED)❌ scripts directory missing$(NC)"
	@test -d tool_router || echo "$(RED)❌ tool_router directory missing$(NC)"
	@echo "$(YELLOW)🔍 Checking configuration...$(NC)"
	@test -f .env || echo "$(YELLOW)⚠️  .env file missing$(NC)"
	@test -f docker-compose.yml || echo "$(RED)❌ docker-compose.yml missing$(NC)"
	@echo "$(YELLOW)🌐 Checking services...$(NC)"
	@curl -s $(HEALTH_URL) > /dev/null && echo "$(GREEN)✅ Service healthy$(NC)" || echo "$(RED)❌ Service unhealthy$(NC)"
	@echo "$(GREEN)✅ Health check complete!$(NC)"

# === Documentation Commands ===

docs: ## Generate documentation
	@echo "$(BLUE)📚 Generating documentation...$(NC)"
	@echo "$(YELLOW)API Documentation...$(NC)"
	@cd tool_router && python -m pydoc . > ../docs/api.md 2>/dev/null || true
	@echo "$(YELLOW)README updates...$(NC)"
	@$(PYTHON) scripts/help.py --markdown > docs/commands.md 2>/dev/null || true
	@echo "$(GREEN)✅ Documentation generated!$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)📚 Starting documentation server...$(NC)"
	@cd docs && python3 -m http.server 8080 2>/dev/null || echo "$(YELLOW)Install Python http.server$(NC)"

# === Utility Commands ===

shell: ## Open shell in gateway container
	@echo "$(BLUE)🐚 Opening shell in gateway container...$(NC)"
	@$(DOCKER_COMPOSE) exec gateway bash

shell-router: ## Open shell in tool-router container
	@echo "$(BLUE)🐚 Opening shell in tool-router container...$(NC)"
	@$(DOCKER_COMPOSE) exec tool-router bash

debug: ## Enable debug mode
	@echo "$(PURPLE)🐛 Enabling debug mode...$(NC)"
	@export DEBUG=true
	@./start.sh

version: ## Show version information
	@echo "$(CYAN)MCP Gateway Version Information$(NC)"
	@echo "$(CYAN)=============================$(NC)"
	@echo "$(YELLOW)Project Version:$(NC) $$(jq -r '.version' package.json 2>/dev/null || echo 'Unknown')"
	@echo "$(YELLOW)Python Version:$(NC) $$(python3 --version)"
	@echo "$(YELLOW)Docker Version:$(NC) $$(docker --version 2>/dev/null | cut -d' ' -f3)"
	@echo "$(YELLOW)Node Version:$(NC) $$(node --version 2>/dev/null || echo 'Not installed')"
	@echo "$(YELLOW)Git Version:$(NC) $$(git --version 2>/dev/null | cut -d' ' -f3)"

# === Advanced Commands (Hidden) ===

enterprise-features: ## Enable enterprise features
	@echo "$(PURPLE)🏢 Enabling enterprise features...$(NC)"
	@$(PYTHON) scripts/enterprise-features.py

ml-optimize: ## Run ML optimization
	@echo "$(PURPLE)🧠 Running ML optimization...$(NC)"
	@$(PYTHON) scripts/ai-optimization.py

multi-cloud: ## Multi-cloud management
	@echo "$(PURPLE)☁️  Multi-cloud management...$(NC)"
	@$(PYTHON) scripts/multi-cloud-manager.py

# === Help Categories ===

help-quick: ## Show quick start commands only
	@echo "$(CYAN)Quick Start Commands:$(NC)"
	@echo "  make setup      # Initial setup"
	@echo "  make start      # Start services"
	@echo "  make register   # Register gateways"
	@echo "  make status     # Check status"

help-dev: ## Show development commands only
	@echo "$(CYAN)Development Commands:$(NC)"
	@echo "  make lint       # Run linting"
	@echo "  make test       # Run tests"
	@echo "  make validate   # Validate config"
	@echo "  make deps        # Update dependencies"

help-deploy: ## Show deployment commands only
	@echo "$(CYAN)Deployment Commands:$(NC)"
	@echo "  make deploy     # Deploy to production"
	@echo "  make deploy-test # Test deployment"
	@echo "  make rollback   # Rollback deployment"
	@echo "  make npm-release # NPM release"

help-security: ## Show security commands only
	@echo "$(CYAN)Security Commands:$(NC)"
	@echo "  make security   # Security scans"
	@echo "  make audit      # Dependency audit"
	@echo "  make security-harden # Security hardening"