.PHONY: start stop gateway-only register register-wait jwt list-prompts list-servers refresh-cursor-jwt use-cursor-wrapper verify-cursor-setup reset-db cleanup-duplicates generate-secrets lint shellcheck test pre-commit-install

generate-secrets:
	@echo "# Add these to .env (min 32 chars; weak secrets cause 'Server disconnected' / context-forge errors):"
	@echo "JWT_SECRET_KEY=$(shell openssl rand -base64 32)"
	@echo "AUTH_ENCRYPTION_SECRET=$(shell openssl rand -base64 32)"

start:
	./start.sh

stop:
	./start.sh stop

reset-db:
	./start.sh stop
	rm -f ./data/mcp.db ./data/mcp.db-shm ./data/mcp.db-wal
	@echo "DB removed. Run 'make start' then 'make register' to recreate gateways."

gateway-only:
	./start.sh gateway-only

register:
	./scripts/register-gateways.sh

register-wait:
	REGISTER_WAIT_SECONDS=30 ./scripts/register-gateways.sh

jwt:
	@bash -c 'set -a; [ -f .env ] && . ./.env; set +a; \
	  python3 "$(CURDIR)/scripts/create_jwt_token_standalone.py" 2>/dev/null || \
	  docker exec "$${MCPGATEWAY_CONTAINER:-mcpgateway}" python3 -m mcpgateway.utils.create_jwt_token --username "$$PLATFORM_ADMIN_EMAIL" --exp 10080 --secret "$$JWT_SECRET_KEY" 2>/dev/null'

list-prompts:
	./scripts/list-prompts.sh

list-servers:
	./scripts/list-servers.sh

refresh-cursor-jwt:
	./scripts/refresh-cursor-jwt.sh

use-cursor-wrapper:
	./scripts/use-cursor-wrapper.sh

verify-cursor-setup:
	./scripts/verify-cursor-setup.sh

cleanup-duplicates:
	./scripts/cleanup-duplicate-servers.sh

lint:
	$(MAKE) shellcheck
	ruff check tool_router/

shellcheck:
	shellcheck -s bash -S warning start.sh scripts/*.sh scripts/lib/*.sh

test:
	pytest tool_router/ -v

pre-commit-install:
	pre-commit install
	@echo "Run 'pre-commit run --all-files' once to check the whole repo."
