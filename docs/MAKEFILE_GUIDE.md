# MCP Gateway Makefile Documentation

## 🎯 Overview

This comprehensive Makefile replaces all manual shell scripts with organized, easy-to-use targets. It provides a single entry point for all MCP Gateway operations, from development to deployment.

## 🚀 Quick Start

```bash
# Show all available commands
make help

# Complete quick start setup
make quickstart

# Individual setup steps
make setup          # Initial configuration
make start           # Start services
make register        # Register gateways
make status          # Check system status
```

## 📋 Command Categories

### 🚀 Quick Start Commands
- `make setup` - Interactive setup wizard
- `make start` - Start the MCP Gateway stack
- `make stop` - Stop the MCP Gateway stack
- `make restart` - Restart the stack
- `make register` - Register gateways and virtual servers
- `make status` - Show comprehensive system status

### 🔧 Development Commands
- `make lint` - Run all linting (Python + Shell + TypeScript)
- `make lint-strict` - Run strict linting (no auto-fix)
- `make test` - Run all tests (Python + Web Admin)
- `make test-python` - Run Python tests only
- `make test-web` - Run Web Admin tests only
- `make test-integration` - Run integration tests
- `make test-coverage` - Run tests with coverage report
- `make validate` - Validate project configuration
- `make deps` - Update all dependencies

### 📦 NPM Deployment Commands
- `make npm-setup` - Setup NPM deployment for Core Package
- `make npm-test` - Test NPM deployment (dry run)
- `make npm-publish` - Publish to NPM (dry run by default)
- `make npm-release` - Full NPM release (actual publish)
- `make npm-version TYPE=<patch|minor|major>` - Bump NPM version

### 🛡️ Security Commands
- `make security` - Run comprehensive security scans
- `make security-harden` - Apply security hardening
- `make audit` - Audit dependencies for vulnerabilities

### 🚀 Deployment Commands
- `make deploy` - Deploy to production (with confirmation)
- `make deploy-test` - Test deployment configuration
- `make rollback` - Rollback last deployment

### 📊 Monitoring Commands
- `make monitor` - Show system monitoring dashboard
- `make monitor-advanced` - Advanced monitoring with ML
- `make monitor-predictive` - Predictive scaling monitoring
- `make logs` - Show service logs
- `make logs-follow` - Follow service logs in real-time

### 💾 Backup & Restore Commands
- `make backup` - Create system backup
- `make backup-list` - List available backups
- `make restore BACKUP=<file>` - Restore from backup

### 🔧 IDE Setup Commands
- `make ide-setup IDE=<cursor|windsurf|vscode|all>` - Setup IDE configuration
- `make ide-backup` - Backup IDE configurations
- `make ide-restore` - Restore IDE configurations

### 🧹 Maintenance Commands
- `make clean` - Clean temporary files and caches
- `make clean-docker` - Clean Docker resources
- `make doctor` - Comprehensive system health check

### 📚 Documentation Commands
- `make docs` - Generate documentation
- `make docs-serve` - Serve documentation locally

### ⚙️ Utility Commands
- `make shell` - Open shell in gateway container
- `make shell-router` - Open shell in tool-router container
- `make debug` - Enable debug mode
- `make version` - Show version information

## 🔧 Advanced Usage

### Environment Variables

You can customize behavior with environment variables:

```bash
# Set wait time for registration
WAIT=60 make register-wait

# Set output format for status
FORMAT=json make status
FORMAT=detailed make status
```

### Parameter Examples

```bash
# NPM version bumping
make npm-version TYPE=patch
make npm-version TYPE=minor
make npm-version TYPE=major

# IDE setup
make ide-setup IDE=cursor
make ide-setup IDE=windsurf
make ide-setup IDE=vscode
make ide-setup IDE=all

# Restore from backup
make restore BACKUP=data/backups/backup_20231201_120000.tar.gz
```

## 🎨 Color Output

The Makefile uses color-coded output for better readability:

- 🟢 **Green** - Success messages
- 🟡 **Yellow** - Warnings and information
- 🔴 **Red** - Error messages and dangerous operations
- 🔵 **Blue** - Information and status
- 🟣 **Purple** - Advanced features
- 🟦 **Cyan** - Headers and important information

## 📊 Command Examples

### Development Workflow
```bash
# Complete development setup
make setup
make deps
make lint
make test
make validate
```

### NPM Release Workflow
```bash
# Setup NPM deployment
make npm-setup

# Test deployment
make npm-test

# Bump version and release
make npm-version TYPE=minor
make npm-release
```

### Production Deployment
```bash
# Test deployment first
make deploy-test

# Deploy to production
make deploy

# Monitor deployment
make logs-follow
make status
```

### Security Maintenance
```bash
# Run security scans
make security
make audit

# Apply hardening
make security-harden
```

### System Maintenance
```bash
# Health check
make doctor

# Clean up
make clean
make clean-docker

# Backup before major changes
make backup
```

## 🔍 Troubleshooting

### Common Issues

#### Make Command Not Found
```bash
# Install make (macOS)
brew install make

# Install make (Ubuntu/Debian)
sudo apt-get install build-essential
```

#### Permission Denied
```bash
# Make scripts executable
chmod +x scripts/*.sh
chmod +x start.sh
```

#### Docker Issues
```bash
# Check Docker status
docker --version
docker-compose --version

# Clean Docker resources
make clean-docker
```

#### Python Environment Issues
```bash
# Check Python version
python3 --version

# Install/update dependencies
make deps

# Clean Python cache
make clean
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Enable debug mode
make debug

# Check system health
make doctor

# View detailed logs
make logs-follow
```

## 📚 Integration with Existing Scripts

The Makefile integrates with existing scripts while providing a cleaner interface:

| Old Command | New Make Command |
|-------------|------------------|
| `./scripts/setup-wizard.py` | `make setup` |
| `./start.sh` | `make start` |
| `./scripts/gateway/register.sh` | `make register` |
| `./scripts/status.py` | `make status` |
| `./scripts/deploy-production.sh` | `make deploy` |
| `./scripts/backup/create-backup.sh` | `make backup` |
| `./scripts/security-hardening.sh` | `make security-harden` |

## 🎯 Best Practices

### Before Making Changes
1. Run `make doctor` to check system health
2. Create a backup with `make backup`
3. Run tests with `make test`
4. Validate configuration with `make validate`

### Development Workflow
1. `make setup` - Initial setup
2. `make deps` - Update dependencies
3. `make lint` - Check code quality
4. `make test` - Run tests
5. `make validate` - Validate configuration

### Production Deployment
1. `make deploy-test` - Test deployment
2. `make security` - Security scan
3. `make backup` - Create backup
4. `make deploy` - Deploy to production
5. `make status` - Verify deployment

### NPM Publishing
1. `make npm-setup` - Setup deployment
2. `make npm-test` - Test deployment
3. `make npm-version` - Bump version
4. `make npm-release` - Publish to NPM

## 🔧 Customization

### Adding New Commands

To add new commands, edit the Makefile:

```makefile
# Add to .PHONY line
.PHONY: help setup my-new-command

# Add new command
my-new-command: ## Description of my new command
	@echo "Running my new command..."
	# Your command here
```

### Modifying Existing Commands

You can modify existing commands by editing the corresponding target in the Makefile.

## 📞 Getting Help

### Command-Specific Help
```bash
# Quick start help
make help-quick

# Development help
make help-dev

# Deployment help
make help-deploy

# Security help
make help-security
```

### Troubleshooting Help
1. Run `make doctor` for system health check
2. Check logs with `make logs`
3. Review this documentation
4. Check individual script documentation in `scripts/README.md`

## 🚀 Migration Guide

### From Manual Scripts
Replace manual script calls with Make commands:

**Before:**
```bash
./scripts/setup-wizard.py
./start.sh
./scripts/gateway/register.sh
./scripts/status.py
```

**After:**
```bash
make setup
make start
make register
make status
```

### From Complex Workflows
Simplify complex workflows with combined targets:

**Before:**
```bash
# Multiple steps
python3 scripts/setup-wizard.py
pip install -r requirements.txt
ruff check .
shellcheck scripts/*.sh
python -m pytest tests/
```

**After:**
```bash
# Single command
make quickstart  # or make setup && make deps && make lint && make test
```

## 🎉 Benefits

1. **Simplified Interface** - Single entry point for all operations
2. **Consistent Naming** - Clear, descriptive command names
3. **Error Handling** - Built-in error checking and user confirmation
4. **Color Output** - Easy-to-read colored output
5. **Documentation** - Built-in help system
6. **Safety** - Confirmation prompts for dangerous operations
7. **Flexibility** - Environment variables and parameters
8. **Integration** - Works with existing scripts and workflows

The Makefile provides a professional, enterprise-grade interface for managing MCP Gateway operations while maintaining compatibility with existing tools and scripts.