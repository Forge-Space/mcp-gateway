---
name: ide-integration
description: Guide for adding, modifying, or debugging MCP Gateway IDE integration. Use when the task involves IDE setup scripts, mcp-wrapper.sh, ide-setup.py, setup-wizard.py, or adding support for a new IDE. Also use when troubleshooting "No MCP servers found" in Cursor/Windsurf/Zed/VSCode/Claude Desktop.
---

# IDE Integration

## Supported IDEs and Config Locations

| IDE | Config Key | Config Path | Container Key |
|-----|-----------|-------------|---------------|
| Cursor | `cursor` | `~/.cursor/mcp.json` | `mcpServers` |
| Windsurf | `windsurf` | `~/.windsurf/mcp.json` | `mcpServers` |
| VSCode | `vscode` | `.vscode/settings.json` | `mcp.servers` |
| Claude Desktop | `claude` | macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`<br>Linux: `~/.config/claude/claude_desktop_config.json` | `mcpServers` |
| Zed | `zed` | `~/.config/zed/settings.json` | `context_servers` |

## Key Files

```
scripts/
├── ide-setup.py          # Unified IDE management CLI (IDEManager class)
├── setup-forge-space-mcp.sh  # Bash installer (single-IDE, Cursor-focused)
├── setup-wizard.py       # Interactive wizard (calls ide-setup.py)
├── mcp-wrapper.sh        # Real executable — stdio bridge via npx
└── mcp-wrapper.sh        # Must NOT be a symlink
```

## mcp-wrapper.sh Contract

The wrapper reads `MCP_CLIENT_SERVER_URL` from env and proxies stdio to the npm client:
```bash
exec npx --yes @forgespace/mcp-gateway-client --url="${MCP_CLIENT_SERVER_URL}"
```

If it's a broken symlink or not executable, ALL wrapper-based IDE flows will fail silently.

**Check**: `test -x scripts/mcp-wrapper.sh && bash -n scripts/mcp-wrapper.sh`

## Adding a New IDE

In `scripts/ide-setup.py` `IDEManager.__init__`:

1. Add an `IDEConfig` entry to `self.ides`
2. Set `config_path` to the platform-correct path
3. Set `config_format` (always `"json"` for now)
4. Determine the container key (`mcpServers`, `mcp.servers`, or `context_servers`)
5. Update `generate_ide_config()` for the new container key format
6. Update `install_ide_config()` merge logic
7. Update `use_wrapper_script()` write logic
8. Update `verify_setup()` container key lookup
9. Add detection to `detect_installed_ides()`
10. Add to `available_ides` in `setup-wizard.py._ide_step()`
11. Add test cases in `tests/test_ide_setup.py`

## Zed-Specific Format

Zed uses `context_servers` instead of `mcpServers`, and the command is an object:
```json
{
  "context_servers": {
    "context-forge": {
      "command": {"path": "/path/to/mcp-wrapper.sh", "args": []},
      "settings": {},
      "env": {"MCP_CLIENT_SERVER_URL": "http://localhost:4444/servers/UUID/mcp"}
    }
  }
}
```

## CLI Quick Reference

```bash
# Detect installed IDEs
python3 scripts/ide-setup.py detect

# Install config for an IDE (reads URL from data/.mcp-client-url)
python3 scripts/ide-setup.py setup cursor
python3 scripts/ide-setup.py setup zed
python3 scripts/ide-setup.py setup all

# Use wrapper script (all IDEs)
python3 scripts/ide-setup.py setup cursor --action use-wrapper
python3 scripts/ide-setup.py setup zed --action use-wrapper

# Verify setup
python3 scripts/ide-setup.py setup cursor --action verify

# Check status
python3 scripts/ide-setup.py setup cursor --action status
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `mcp-wrapper.sh: No such file or directory` | Broken symlink | `ls -la scripts/mcp-wrapper.sh` — if symlink, delete and recreate as real script |
| `MCP_CLIENT_SERVER_URL is not set` | `data/.mcp-client-url` missing | `make register` |
| Zed shows empty tool list | `context_servers` key missing | Run `setup zed --action use-wrapper` |
| Claude Desktop not found on macOS | Wrong detection path | Fixed in Phase 2 — uses `~/Library/Application Support/Claude` |
| IDE wizard runs but doesn't write config | `setup-wizard.py` used wrong sub-command | Fixed in Phase 2 — now calls `setup <ide> --action use-wrapper` |

## Tests

```bash
pytest tests/test_ide_setup.py -v --timeout=30
```
