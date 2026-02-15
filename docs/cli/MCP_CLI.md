# MCP Gateway Unified CLI Tool

**Version:** 1.0.0
**Status:** Production Ready

---

## Overview

The `mcp` command provides a unified interface for all MCP Gateway operations, replacing the need to remember multiple `make` commands and scripts.

### Key Features

- **Simple Commands**: Intuitive command structure
- **Interactive Wizard**: Guided setup for new users
- **IDE Auto-Detection**: Automatically finds installed IDEs
- **Server Management**: Enable/disable servers with one command
- **Color-Coded Output**: Clear visual feedback

---

## Installation

The `mcp` command is located at `scripts/mcp` and can be used directly:

```bash
# From project root
./scripts/mcp help

# Or add to PATH for system-wide access
sudo ln -s "$(pwd)/scripts/mcp" /usr/local/bin/mcp
mcp help
```

---

## Command Reference

### General Commands

#### `mcp help`
Show help message with all available commands.

```bash
mcp help
```

#### `mcp init`
Initialize MCP Gateway project. Checks prerequisites, creates `.env` file, and sets up data directory.

```bash
mcp init
```

**What it does:**
- Checks for Docker and Docker Compose
- Creates `.env` from `.env.example` if needed
- Creates `data/` directory
- Displays next steps

#### `mcp start`
Start the gateway stack (equivalent to `make start`).

```bash
mcp start
```

#### `mcp stop`
Stop the gateway stack (equivalent to `make stop`).

```bash
mcp stop
```

#### `mcp restart`
Restart the gateway stack.

```bash
mcp restart
```

#### `mcp status`
Check gateway health and show running containers.

```bash
mcp status
```

---

### Server Management

#### `mcp server list`
List all virtual servers with their enabled/disabled status.

```bash
mcp server list
```

**Output:**
```
Virtual Servers (enabled/disabled):
✓ cursor-search (enabled) - gateways: brave-search,github
✗ browser-tools (disabled) - gateways: puppeteer,playwright
```

#### `mcp server enable <name>`
Enable a virtual server.

```bash
mcp server enable cursor-search
```

#### `mcp server disable <name>`
Disable a virtual server.

```bash
mcp server disable browser-tools
```

#### `mcp server info <name>`
Get detailed information about a server (uses REST API).

```bash
mcp server info cursor-search
```

**Output (JSON):**
```json
{
  "name": "cursor-search",
  "gateways": ["brave-search", "github"],
  "enabled": true,
  "found": true
}
```

---

### IDE Configuration

#### `mcp ide detect`
Auto-detect installed IDEs (Windsurf, Cursor).

```bash
mcp ide detect
```

**Output:**
```
ℹ Detecting installed IDEs...
✓ Found: Windsurf
✓ Found: Cursor
ℹ Detected 2 IDE(s)
```

#### `mcp ide config`
Generate IDE configuration interactively.

```bash
mcp ide config
```

**Interactive prompts:**
1. Select IDE (Windsurf or Cursor)
2. Generates configuration
3. Displays copy-pasteable JSON

#### `mcp ide setup`
Run interactive IDE setup wizard.

```bash
mcp ide setup
```

**What it does:**
1. Detects installed IDEs
2. Asks which IDE to configure
3. Generates configuration
4. Provides step-by-step instructions

---

### Interactive Wizard

#### `mcp wizard`
Run the complete interactive setup wizard.

```bash
mcp wizard
```

**Wizard Steps:**
1. **Initialize**: Check prerequisites and create `.env`
2. **Start Gateway**: Optionally start the gateway stack
3. **Configure IDE**: Optionally set up IDE configuration
4. **Summary**: Display next steps

**Perfect for:**
- First-time setup
- Onboarding new team members
- Quick project initialization

---

## Usage Examples

### First-Time Setup

```bash
# 1. Initialize project
mcp init

# 2. Start gateway
mcp start

# 3. Configure IDE
mcp ide setup

# Or use the wizard for all steps
mcp wizard
```

### Daily Operations

```bash
# Check status
mcp status

# List servers
mcp server list

# Enable a server
mcp server enable cursor-search

# Restart gateway
mcp restart
```

### Server Lifecycle Management

```bash
# Disable unused servers to speed up startup
mcp server disable browser-tools
mcp server disable puppeteer
mcp server disable playwright

# Enable when needed
mcp server enable browser-tools

# Check which servers are enabled
mcp server list
```

### IDE Configuration

```bash
# Auto-detect IDEs
mcp ide detect

# Generate config for Windsurf
mcp ide config
# Select: 1 (Windsurf)

# Or use the setup wizard
mcp ide setup
```

---

## Comparison with Make Commands

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `make start` | `mcp start` | Simpler |
| `make stop` | `mcp stop` | Simpler |
| `make list-enabled` | `mcp server list` | More intuitive |
| `make enable-server SERVER=name` | `mcp server enable name` | No variable needed |
| `make disable-server SERVER=name` | `mcp server disable name` | No variable needed |
| `make ide-windsurf` | `mcp ide config` | Interactive |
| `make ide-cursor` | `mcp ide config` | Interactive |

---

## Advanced Usage

### Adding to System PATH

For system-wide access:

```bash
# Option 1: Symlink (recommended)
sudo ln -s "$(pwd)/scripts/mcp" /usr/local/bin/mcp

# Option 2: Add to PATH in shell profile
echo 'export PATH="$PATH:/path/to/mcp-gateway/scripts"' >> ~/.bashrc
source ~/.bashrc

# Now use from anywhere
mcp help
```

### Shell Completion (Future)

Shell completion scripts will be added in a future update:

```bash
# Bash
mcp completion bash > /etc/bash_completion.d/mcp

# Zsh
mcp completion zsh > /usr/local/share/zsh/site-functions/_mcp
```

---

## Troubleshooting

### Command Not Found

```bash
# Make sure script is executable
chmod +x scripts/mcp

# Run from project root
./scripts/mcp help
```

### Docker Not Running

```bash
mcp status
# Error: Docker is not running

# Start Docker Desktop or Docker daemon
# Then try again
mcp start
```

### Gateway Not Starting

```bash
# Check logs
docker compose logs

# Reset and restart
make reset-db
mcp start
```

---

## Integration with CI/CD

The `mcp` command can be used in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Initialize MCP Gateway
  run: ./scripts/mcp init

- name: Start Gateway
  run: ./scripts/mcp start

- name: Check Status
  run: ./scripts/mcp status

- name: Enable Test Servers
  run: |
    ./scripts/mcp server enable test-server
    ./scripts/mcp server list
```

---

## Future Enhancements

Planned features for future versions:

- [ ] Shell completion (bash, zsh, fish)
- [ ] `mcp logs` - View gateway logs
- [ ] `mcp update` - Update gateway to latest version
- [ ] `mcp backup` - Backup configuration and data
- [ ] `mcp restore` - Restore from backup
- [ ] `mcp health` - Detailed health checks
- [ ] `mcp metrics` - Display gateway metrics

---

## Contributing

To add new commands:

1. Add function in `scripts/mcp` (e.g., `cmd_new_feature()`)
2. Add case in `main()` function
3. Update this documentation
4. Test thoroughly
5. Submit PR

---

## Support

- **Documentation**: [docs/](../README.md)
- **Issues**: [GitHub Issues](https://github.com/LucasSantana-Dev/mcp-gateway/issues)
- **Discussions**: [GitHub Discussions](https://github.com/LucasSantana-Dev/mcp-gateway/discussions)

---

**Last Updated:** 2026-02-15
**Version:** 1.0.0
