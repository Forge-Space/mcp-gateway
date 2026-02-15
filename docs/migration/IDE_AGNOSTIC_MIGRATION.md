# IDE-Agnostic Migration Guide

## Overview

The MCP Gateway has been refactored to be IDE-agnostic. Previously, the codebase was tightly coupled to Cursor IDE with hardcoded paths, environment variables, and terminology. Now it supports any MCP-compatible IDE (Cursor, Windsurf, VS Code, etc.).

## Breaking Changes

### Directory Structure
- **Old:** `scripts/cursor/`
- **New:** `scripts/mcp-client/`

### Environment Variables
| Old Variable | New Variable | Backward Compatible |
|-------------|--------------|---------------------|
| `CURSOR_MCP_JSON` | `MCP_CLIENT_CONFIG` | ✅ Yes |
| `CURSOR_MCP_SERVER_URL` | `MCP_CLIENT_SERVER_URL` | ✅ Yes |
| `CURSOR_MCP_TIMEOUT_MS` | `MCP_CLIENT_TIMEOUT_MS` | ✅ Yes |
| `REGISTER_CURSOR_MCP_SERVER_NAME` | `REGISTER_MCP_CLIENT_SERVER_NAME` | ✅ Yes |
| `CONTEXT_FORGE_MCP_KEY` | `MCP_CLIENT_KEY` | ✅ Yes |

### File Paths
| Old Path | New Path |
|----------|----------|
| `data/.cursor-mcp-url` | `data/.mcp-client-url` |

### Makefile Targets
| Old Target | New Target | Backward Compatible |
|-----------|------------|---------------------|
| `make cursor-pull` | `make mcp-client-pull` | ✅ Aliased |
| `make refresh-cursor-jwt` | `make refresh-mcp-client-jwt` | ✅ Aliased |
| `make use-cursor-wrapper` | `make use-mcp-client-wrapper` | ✅ Aliased |
| `make verify-cursor-setup` | `make verify-mcp-client-setup` | ✅ Aliased |

### Virtual Server Names
| Old Name | New Name | Notes |
|----------|----------|-------|
| `cursor-router` | `mcp-router` | Tool-router virtual server |
| `cursor-default` | `mcp-default` | Full toolset virtual server |

## Migration Steps

### For Existing Users

1. **Update environment variables** (optional, backward compatible):
   ```bash
   # In .env file
   # Old:
   REGISTER_CURSOR_MCP_SERVER_NAME=cursor-default
   CURSOR_MCP_TIMEOUT_MS=120000

   # New (recommended):
   REGISTER_MCP_CLIENT_SERVER_NAME=mcp-default
   MCP_CLIENT_TIMEOUT_MS=120000
   ```

2. **Update Makefile commands** (optional, aliases work):
   ```bash
   # Old:
   make cursor-pull
   make use-cursor-wrapper
   make verify-cursor-setup

   # New (recommended):
   make mcp-client-pull
   make use-mcp-client-wrapper
   make verify-mcp-client-setup
   ```

3. **Re-register virtual servers** (if using new names):
   ```bash
   # Update .env to use new server names
   REGISTER_MCP_CLIENT_SERVER_NAME=mcp-default

   # Re-register
   make register
   ```

4. **Update IDE config path** (if not using Cursor):
   ```bash
   # For Windsurf
   export MCP_CLIENT_CONFIG=~/.windsurf/mcp.json
   make use-mcp-client-wrapper

   # For VS Code
   export MCP_CLIENT_CONFIG=~/.vscode/settings.json
   make use-mcp-client-wrapper
   ```

### For New Users

Just follow the standard setup in README.md - all new terminology is IDE-agnostic by default.

## IDE-Specific Configuration Examples

### Cursor
```bash
# Default - no config needed
make use-mcp-client-wrapper
```

### Windsurf
```bash
export MCP_CLIENT_CONFIG=~/.windsurf/mcp.json
make use-mcp-client-wrapper
```

### VS Code
```bash
export MCP_CLIENT_CONFIG=~/.vscode/settings.json
make use-mcp-client-wrapper
```

### Zed
```bash
export MCP_CLIENT_CONFIG=~/.config/zed/mcp.json
make use-mcp-client-wrapper
```

## Function Changes

### Shell Functions
- `get_context_forge_key()` → `get_mcp_client_key()` (backward compatible alias exists)
- `write_cursor_mcp_url()` → `write_mcp_client_url()` (internal function)

## Backward Compatibility

All old environment variables and Makefile targets continue to work through aliases and fallback logic. No immediate action required for existing setups.

## Benefits

1. **IDE Portability**: Works with any MCP-compatible IDE
2. **Clear Separation**: No IDE-specific coupling in core logic
3. **Better Naming**: Generic terminology reflects actual purpose
4. **Future-Proof**: Easy to add support for new IDEs

## Support

For issues or questions, see:
- [README.md](../README.md) - General setup
- [IDE_SETUP_GUIDE.md](IDE_SETUP_GUIDE.md) - IDE-specific examples
- [ENVIRONMENT_CONFIGURATION.md](ENVIRONMENT_CONFIGURATION.md) - Configuration details
