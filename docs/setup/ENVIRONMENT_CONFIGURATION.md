# Environment Configuration Guide

Understanding the minimal .env approach and how to configure stack-specific API keys in your IDE.

## Table of Contents

- [Overview](#overview)
- [Philosophy](#philosophy)
- [What Goes Where](#what-goes-where)
- [Migration Guide](#migration-guide)
- [Security Best Practices](#security-best-practices)
- [Examples](#examples)

## Overview

**The Problem**: Traditional approach stores all API keys in `.env` file, leading to:
- Secrets committed to version control
- Difficult team collaboration (everyone needs same keys)
- No per-user customization
- Security risks

**The Solution**: Minimal `.env` with stack-specific keys in IDE configuration:
- Gateway infrastructure in `.env` (shared)
- Stack-specific API keys in IDE's `mcp.json` (per-user)
- Clear separation of concerns
- Better security and portability

## Philosophy

### Minimal .env Approach

The `.env` file should contain **ONLY** gateway infrastructure configuration:

```bash
# Gateway Infrastructure (shared across team)
HOST=0.0.0.0
PORT=4444
DATABASE_URL=sqlite:///./mcp.db
JWT_SECRET_KEY=<strong-secret>
AUTH_ENCRYPTION_SECRET=<strong-secret>
PLATFORM_ADMIN_EMAIL=admin@example.com
PLATFORM_ADMIN_PASSWORD=<secure-password>
GATEWAY_JWT=<generated-jwt>
```

### IDE Configuration

Stack-specific API keys go in your IDE's MCP configuration:

```json
{
  "mcpServers": {
    "nodejs-typescript": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "nodejs-typescript"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token",
        "SNYK_TOKEN": "your_snyk_token",
        "TAVILY_API_KEY": "tvly_your_key"
      }
    }
  }
}
```

## What Goes Where

### .env File (Gateway Infrastructure)

**✅ Include:**
- `HOST`, `PORT` - Gateway server configuration
- `DATABASE_URL` - Gateway's internal database
- `JWT_SECRET_KEY`, `AUTH_ENCRYPTION_SECRET` - Gateway security
- `PLATFORM_ADMIN_EMAIL`, `PLATFORM_ADMIN_PASSWORD` - Admin UI access
- `GATEWAY_JWT` - Tool-router authentication
- Docker configuration (volumes, ports)
- Gateway-level settings

**❌ Exclude:**
- GitHub tokens
- Snyk tokens
- Tavily API keys
- Database connection strings (for MCP servers)
- Any stack-specific credentials

### IDE's mcp.json (Stack-Specific Keys)

**✅ Include:**
- `GITHUB_PERSONAL_ACCESS_TOKEN` - GitHub MCP server
- `SNYK_TOKEN` - Snyk security scanning
- `TAVILY_API_KEY` - Tavily search
- `POSTGRES_CONNECTION_STRING` - PostgreSQL MCP server
- `MONGODB_CONNECTION_STRING` - MongoDB MCP server
- Any other stack-specific API keys

**❌ Exclude:**
- Gateway infrastructure settings
- Shared team configuration
- Docker settings

## Migration Guide

### Step 1: Backup Current Configuration

```bash
# Backup your .env file
cp .env .env.backup

# Backup your IDE configuration
cp ~/.cursor/mcp.json ~/.cursor/mcp.json.backup
```

### Step 2: Identify API Keys to Move

Look for these in your `.env` file:
- `GITHUB_PERSONAL_ACCESS_TOKEN`
- `SNYK_TOKEN`
- `TAVILY_API_KEY`
- `POSTGRES_CONNECTION_STRING`
- `MONGODB_CONNECTION_STRING`
- `FIRECRAWL_API_KEY`

### Step 3: Update .env File

Remove or comment out stack-specific API keys:

```bash
# Before:
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxx
SNYK_TOKEN=xxxxx
TAVILY_API_KEY=tvly_xxxxx

# After:
# ============================================================================
# STACK-SPECIFIC API KEYS - CONFIGURE IN YOUR IDE's mcp.json, NOT HERE
# ============================================================================
# GITHUB_PERSONAL_ACCESS_TOKEN - Configure in IDE's mcp.json env object
# SNYK_TOKEN - Configure in IDE's mcp.json env object
# TAVILY_API_KEY - Configure in IDE's mcp.json env object
```

### Step 4: Configure IDE

Add the API keys to your IDE's MCP configuration:

**Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "your-stack-profile": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "your-stack-profile"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxx",
        "SNYK_TOKEN": "xxxxx",
        "TAVILY_API_KEY": "tvly_xxxxx"
      }
    }
  }
}
```

**VSCode** (`.vscode/settings.json`):
```json
{
  "mcp.servers": {
    "your-stack-profile": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "your-stack-profile"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_TOKEN}",
        "SNYK_TOKEN": "${env:SNYK_TOKEN}",
        "TAVILY_API_KEY": "${env:TAVILY_API_KEY}"
      }
    }
  }
}
```

### Step 5: Test Configuration

```bash
# Restart gateway
make stop
make start

# Restart IDE
# Verify MCP connection works
```

### Step 6: Clean Up

Once confirmed working:
```bash
# Remove backup files
rm .env.backup
rm ~/.cursor/mcp.json.backup
```

## Security Best Practices

### 1. Never Commit API Keys

```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore

# Check what would be committed
git status

# If .env is tracked, remove it
git rm --cached .env
```

### 2. Use Environment Variables (VSCode)

Instead of hardcoding in `mcp.json`:

```bash
# Add to ~/.bashrc or ~/.zshrc
export GITHUB_TOKEN="ghp_your_token"
export SNYK_TOKEN="your_snyk_token"
export TAVILY_API_KEY="tvly_your_key"
```

Then reference in VSCode:
```json
"env": {
  "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_TOKEN}"
}
```

### 3. Rotate Tokens Regularly

**GitHub Tokens:**
- Rotate every 90 days
- Use fine-grained tokens with minimal scopes
- https://github.com/settings/tokens

**Snyk Tokens:**
- Rotate every 90 days
- https://app.snyk.io/account

**Gateway JWT:**
- Rotate weekly: `make jwt`
- Update in `.env`

### 4. Use Minimal Scopes

**GitHub Token Scopes:**
- ✅ `repo` - Only if you need private repo access
- ✅ `read:org` - Only if you need org access
- ❌ `admin:*` - Never needed for MCP

### 5. Separate Personal vs Team Keys

**Personal Keys** (in IDE's mcp.json):
- GitHub personal access token
- Your Snyk account token
- Your Tavily API key

**Team Keys** (in .env):
- Gateway admin credentials
- Shared infrastructure settings

## Examples

### Example 1: Node.js Developer

**`.env` (shared with team):**
```bash
HOST=0.0.0.0
PORT=4444
DATABASE_URL=sqlite:///./mcp.db
JWT_SECRET_KEY=team_shared_secret_key_min_32_chars
AUTH_ENCRYPTION_SECRET=team_shared_salt_min_32_chars
PLATFORM_ADMIN_EMAIL=team@company.com
PLATFORM_ADMIN_PASSWORD=TeamPassword123!
GATEWAY_JWT=<run make jwt>
```

**`~/.cursor/mcp.json` (personal):**
```json
{
  "mcpServers": {
    "nodejs-typescript": {
      "command": "/Users/john/mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "nodejs-typescript"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_johns_personal_token",
        "SNYK_TOKEN": "johns_snyk_token",
        "TAVILY_API_KEY": "johns_tavily_key"
      }
    }
  }
}
```

### Example 2: Full-Stack Developer

**`.env` (same as above):**
```bash
# Gateway infrastructure only
```

**`~/.cursor/mcp.json` (personal):**
```json
{
  "mcpServers": {
    "fullstack-universal": {
      "command": "/Users/jane/mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "fullstack-universal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_janes_token",
        "POSTGRES_CONNECTION_STRING": "postgresql://jane:password@localhost:5432/mydb",
        "MONGODB_CONNECTION_STRING": "mongodb://localhost:27017/mydb",
        "SNYK_TOKEN": "janes_snyk_token",
        "TAVILY_API_KEY": "janes_tavily_key"
      }
    }
  }
}
```

### Example 3: Team with Multiple Developers

**Team Repository** (`.env.example`):
```bash
# Copy to .env and set real values
HOST=0.0.0.0
PORT=4444
DATABASE_URL=sqlite:///./mcp.db
JWT_SECRET_KEY=REPLACE_WITH_STRONG_SECRET
AUTH_ENCRYPTION_SECRET=REPLACE_WITH_STRONG_SALT
PLATFORM_ADMIN_EMAIL=admin@example.com
PLATFORM_ADMIN_PASSWORD=REPLACE_ME

# Stack-specific API keys: Configure in IDE's mcp.json, NOT here
# GITHUB_PERSONAL_ACCESS_TOKEN=<configure-in-ide>
# SNYK_TOKEN=<configure-in-ide>
# TAVILY_API_KEY=<configure-in-ide>
```

**Each Developer** configures their own IDE with personal keys.

## Benefits Summary

### For Developers

✅ **Personal API keys** - Use your own tokens
✅ **No key conflicts** - Everyone has their own credentials
✅ **Easy onboarding** - Copy .env.example, add your keys to IDE
✅ **IDE portability** - Same config works across projects

### For Teams

✅ **No secrets in git** - .env.example has no real keys
✅ **Shared infrastructure** - Gateway config is team-wide
✅ **Per-user limits** - API rate limits per developer
✅ **Better security** - Reduced secret exposure

### For Security

✅ **Separation of concerns** - Infrastructure vs. credentials
✅ **Minimal .env** - Fewer secrets in one place
✅ **Easy rotation** - Rotate personal keys without affecting team
✅ **Audit trail** - Know which developer used which key

## Troubleshooting

### Issue: "API key not found"

**Cause**: Key not configured in IDE's mcp.json

**Solution**: Add the required key to your IDE configuration (see [IDE Setup Guide](IDE_SETUP_GUIDE.md))

### Issue: "Gateway authentication failed"

**Cause**: GATEWAY_JWT missing or expired in .env

**Solution**:
```bash
make jwt
# Copy token to .env: GATEWAY_JWT=<token>
```

### Issue: "Permission denied" for GitHub

**Cause**: Token has insufficient scopes

**Solution**: Regenerate token with `repo` scope at https://github.com/settings/tokens

### Issue: Team member can't connect

**Cause**: Missing .env file or incorrect gateway config

**Solution**:
```bash
# Copy example file
cp .env.example .env

# Generate secrets
make generate-secrets

# Update admin credentials
# Each team member configures their own IDE keys
```

## Next Steps

- [IDE Setup Guide](IDE_SETUP_GUIDE.md) - Configure your IDE
- [MCP Stack Configurations](MCP_STACK_CONFIGURATIONS.md) - Choose your stack
- [Tool Router Guide](TOOL_ROUTER_GUIDE.md) - How routing works
