# Suggested Commands

## Development
```bash
make lint              # Run all linters (Python + TS + shell)
make lint-strict       # CI-friendly strict linting
make test              # Run pytest
make test COVERAGE=true # Run tests with coverage report
ruff check tool_router/ --fix  # Auto-fix Python lint issues
ruff format tool_router/       # Format Python code
```

## Services
```bash
make start             # Start Docker Compose stack
make stop              # Stop services
make register          # Register gateways and virtual servers
make status            # Check system status
make status FORMAT=json # JSON status output
make clean             # Full cleanup (stop + reset DB)
```

## Setup & Config
```bash
make setup             # Interactive setup wizard
make ide-setup IDE=all # Configure all IDEs
make auth ACTION=generate # Generate JWT token
make auth ACTION=check    # Validate JWT config
make deps ACTION=install  # Install all dependencies
```

## System Utilities (macOS/Darwin)
```bash
git status / git diff / git log --oneline
python3 -m pytest tool_router/ -v
pip3 install -r requirements-dev.txt
docker compose ps / docker compose logs
```
