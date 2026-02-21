# IDE Setup Guide

Step-by-step guide to configure MCP Gateway stack profiles in any IDE. All examples use the tool-router approach for optimal performance.

## Table of Contents

- [Quick Start](#quick-start)
- [Cursor](#cursor)
- [VSCode](#vscode)
- [Windsurf](#windsurf)
- [JetBrains IDEs](#jetbrains-ides)
- [Common Issues](#common-issues)

## Quick Start

**3 Steps to Get Running:**

1. **Generate Gateway JWT**: `make jwt` (copy the token)
2. **Choose your stack profile** from [MCP Stack Configurations](MCP_STACK_CONFIGURATIONS.md)
3. **Configure your IDE** using examples below

## Cursor

### Location
`~/.cursor/mcp.json`

### Configuration Example

**Node.js/TypeScript Full Profile:**

```json
{
  "mcpServers": {
    "nodejs-typescript": {
      "command": "/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "nodejs-typescript"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here",
        "SNYK_TOKEN": "your_snyk_token_here",
        "TAVILY_API_KEY": "tvly_your_key_here"
      },
      "timeout": 120000
    }
  }
}
```

**React/Next.js Minimal Profile:**

```json
{
  "mcpServers": {
    "react-nextjs-minimal": {
      "command": "/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "react-nextjs-minimal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      },
      "timeout": 120000
    }
  }
}
```

**Database Development:**

```json
{
  "mcpServers": {
    "database-dev": {
      "command": "/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "database-dev"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://user:password@localhost:5432/dbname",
        "MONGODB_CONNECTION_STRING": "mongodb://localhost:27017/dbname"
      },
      "timeout": 120000
    }
  }
}
```

**UI/Design Development (with Figma):**

```json
{
  "mcpServers": {
    "ui-design-dev": {
      "command": "/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "ui-design-dev"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here",
        "FIGMA_ACCESS_TOKEN": "figd_your_figma_token_here"
      },
      "timeout": 120000
    }
  }
}
```

### Setup Steps

1. **Find your mcp.json location:**
   ```bash
   # Create if it doesn't exist
   mkdir -p ~/.cursor
   touch ~/.cursor/mcp.json
   ```

2. **Get the wrapper script path:**
   ```bash
   cd /path/to/forge-mcp-gateway
   pwd
   # Use this path + /scripts/cursor-mcp-wrapper.sh
   ```

3. **Get your API keys:**
   - GitHub: https://github.com/settings/tokens (needs `repo` scope)
   - Snyk: https://app.snyk.io/account (API Token)
   - Tavily: https://tavily.com (API Key)
   - Figma: https://help.figma.com/hc/en-us/articles/8085703771159 (Personal Access Token)

4. **Copy configuration** from examples above, replacing:
   - `/absolute/path/to/forge-mcp-gateway` with your actual path
   - API key placeholders with your real keys
   - `--server-name` with your chosen profile

5. **Restart Cursor**

### Verification

Open Cursor and check the MCP panel:
- You should see 1-2 tools (execute_task, search_tools)
- Tool descriptions should mention routing to upstream tools

---

## VSCode

### Location
`.vscode/settings.json` (workspace) or `~/.config/Code/User/settings.json` (global)

### Configuration Example

**Node.js/TypeScript Full Profile:**

```json
{
  "mcp.servers": {
    "nodejs-typescript": {
      "command": "/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "nodejs-typescript"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_TOKEN}",
        "SNYK_TOKEN": "${env:SNYK_TOKEN}",
        "TAVILY_API_KEY": "${env:TAVILY_API_KEY}"
      }
    }
  }
}
```

**Python Development Minimal:**

```json
{
  "mcp.servers": {
    "python-dev-minimal": {
      "command": "/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "python-dev-minimal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

### Setup Steps

1. **Choose configuration location:**
   - **Workspace**: `.vscode/settings.json` (project-specific)
   - **Global**: `~/.config/Code/User/settings.json` (all projects)

2. **Set environment variables** (recommended approach):
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export GITHUB_TOKEN="ghp_your_token_here"
   export SNYK_TOKEN="your_snyk_token_here"
   export TAVILY_API_KEY="tvly_your_key_here"
   ```

3. **Or use direct values** (less secure):
   Replace `${env:GITHUB_TOKEN}` with `"ghp_your_token_here"`

4. **Reload VSCode window**: Cmd+Shift+P → "Reload Window"

### Verification

Check VSCode's Output panel (View → Output → MCP) for connection status.

---

## Windsurf

### Location
`.windsurf/mcp.json` (workspace) or `~/.windsurf/mcp.json` (global)

### Configuration Example

**Full-Stack Universal:**

```json
{
  "mcpServers": {
    "fullstack-universal": {
      "command": "/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "fullstack-universal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here",
        "POSTGRES_CONNECTION_STRING": "postgresql://user:password@localhost:5432/dbname",
        "MONGODB_CONNECTION_STRING": "mongodb://localhost:27017/dbname",
        "SNYK_TOKEN": "your_snyk_token_here",
        "TAVILY_API_KEY": "tvly_your_key_here"
      },
      "timeout": 120000
    }
  }
}
```

**Monorepo Universal Minimal:**

```json
{
  "mcpServers": {
    "monorepo-universal-minimal": {
      "command": "/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "monorepo-universal-minimal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      },
      "timeout": 120000
    }
  }
}
```

### Setup Steps

1. **Create configuration file:**
   ```bash
   # Workspace-specific
   mkdir -p .windsurf
   touch .windsurf/mcp.json

   # Or global
   mkdir -p ~/.windsurf
   touch ~/.windsurf/mcp.json
   ```

2. **Copy configuration** from examples above

3. **Restart Windsurf**

### Verification

Check Windsurf's MCP panel for available tools.

---

## JetBrains IDEs

### Location
`.idea/mcp-settings.xml` (workspace)

### Configuration Example

**Java/Spring Boot Full:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="MCPSettings">
    <servers>
      <server name="java-spring">
        <command>/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh</command>
        <args>--server-name java-spring</args>
        <env>
          <variable name="GITHUB_PERSONAL_ACCESS_TOKEN" value="ghp_your_token_here"/>
          <variable name="SNYK_TOKEN" value="your_snyk_token_here"/>
          <variable name="TAVILY_API_KEY" value="tvly_your_key_here"/>
        </env>
        <timeout>120000</timeout>
      </server>
    </servers>
  </component>
</project>
```

**Testing & QA Minimal:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="MCPSettings">
    <servers>
      <server name="testing-qa-minimal">
        <command>/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh</command>
        <args>--server-name testing-qa-minimal</args>
        <env>
          <variable name="GITHUB_PERSONAL_ACCESS_TOKEN" value="ghp_your_token_here"/>
          <variable name="SNYK_TOKEN" value="your_snyk_token_here"/>
        </env>
        <timeout>120000</timeout>
      </server>
    </servers>
  </component>
</project>
```

### Setup Steps

1. **Create configuration file:**
   ```bash
   mkdir -p .idea
   touch .idea/mcp-settings.xml
   ```

2. **Copy configuration** from examples above

3. **Restart IDE**

### Verification

Check IDE's MCP panel or settings for connection status.

---

## Common Issues

### Issue: "Command not found" or "Permission denied"

**Cause**: Wrapper script path is incorrect or not executable

**Solution**:
```bash
# Make script executable
chmod +x /path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh

# Verify path is correct
ls -la /path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh
```

### Issue: "Gateway JWT not set"

**Cause**: GATEWAY_JWT missing from .env file

**Solution**:
```bash
cd /path/to/forge-mcp-gateway
make jwt
# Copy the token and add to .env:
# GATEWAY_JWT=eyJhbGc...
```

### Issue: "Authentication failed" for GitHub/Snyk/Tavily

**Cause**: Invalid or missing API keys

**Solution**:
1. **GitHub**: Regenerate token at https://github.com/settings/tokens
   - Required scopes: `repo`, `read:org`
2. **Snyk**: Get token from https://app.snyk.io/account
3. **Tavily**: Get key from https://tavily.com

### Issue: "Connection timeout"

**Cause**: Gateway not running or timeout too short

**Solution**:
```bash
# Start gateway
cd /path/to/forge-mcp-gateway
make start

# Increase timeout in IDE config
"timeout": 180000  # 3 minutes
```

### Issue: "Too many tools" warning

**Cause**: Using Full variant with many tools

**Solution**:
- Switch to Minimal variant of your stack profile
- All profiles already use tool-router (should show 1-2 tools)

### Issue: "Database connection failed"

**Cause**: Invalid connection string or database not running

**Solution**:
```bash
# Test PostgreSQL connection
psql "postgresql://user:password@localhost:5432/dbname"

# Test MongoDB connection
mongosh "mongodb://localhost:27017/dbname"

# Update connection string in IDE's mcp.json
```

### Issue: IDE doesn't recognize ${env:VAR} syntax

**Cause**: IDE doesn't support environment variable interpolation

**Solution**: Use direct values instead:
```json
"env": {
  "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_actual_token_here"
}
```

## Multiple Profiles

You can configure multiple stack profiles in the same IDE:

```json
{
  "mcpServers": {
    "nodejs-typescript": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "nodejs-typescript"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..." }
    },
    "react-nextjs": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "react-nextjs"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..." }
    },
    "database-dev": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "database-dev"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://...",
        "MONGODB_CONNECTION_STRING": "mongodb://..."
      }
    }
  }
}
```

Switch between profiles by selecting the active MCP server in your IDE's MCP panel.

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** when possible (VSCode `${env:VAR}` syntax)
3. **Rotate tokens regularly** (GitHub tokens, GATEWAY_JWT)
4. **Use minimal scopes** for GitHub tokens (only `repo` if needed)
5. **Keep .env file secure** (add to .gitignore)

## Next Steps

- [MCP Stack Configurations](MCP_STACK_CONFIGURATIONS.md) - Choose your stack profile
- [Environment Configuration](ENVIRONMENT_CONFIGURATION.md) - Minimal .env approach
- [Tool Router Guide](TOOL_ROUTER_GUIDE.md) - How routing works
