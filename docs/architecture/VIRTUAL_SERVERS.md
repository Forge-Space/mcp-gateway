# Virtual Servers

Virtual servers organize tools into logical collections to manage IDE tool limits and create focused workflows.

## Overview

Most MCP clients (Cursor, VS Code, etc.) have a limit of approximately **60 tools per connection**. When you register many MCP servers, you can easily exceed this limit, causing warnings or connection issues.

Virtual servers solve this by:
- Grouping tools into collections
- Providing multiple connection endpoints
- Organizing tools by use case or domain

## Default Virtual Servers

### cursor-default

**Purpose:** All available tools from all registered gateways.

**Use when:**
- You have fewer than 60 total tools
- You want access to everything
- You're working on diverse tasks

**Configuration:**
```bash
# Created automatically by make register
# URL: http://localhost:4444/servers/<UUID>/mcp
```

### cursor-router (Tool Router)

**Purpose:** Single entry point using the tool-router gateway.

**Use when:**
- You have many tools (>60)
- You want intelligent tool selection
- You prefer dynamic tool discovery

**How it works:**
1. Exposes only 1-2 tools (`execute_task`, `search_tools`)
2. Dynamically queries gateway API for all tools
3. Intelligently selects and executes the best tool

**Configuration:**
```env
# In .env
GATEWAY_JWT=<token-from-make-jwt>
REGISTER_CURSOR_MCP_SERVER_NAME=cursor-router
```

See [TOOL_ROUTER_GUIDE.md](TOOL_ROUTER_GUIDE.md) for details.

## Custom Virtual Servers

Create custom virtual servers with specific tool subsets using `config/virtual-servers.txt`.

### Configuration Format

```text
ServerName|gateway1,gateway2,gateway3
```

**Example:**
```text
cursor-search|tavily,brave-search,exa
cursor-dev|sequential-thinking,playwright,snyk
cursor-docs|Context7,prisma-remote
```

### Creating Custom Servers

1. **Edit configuration:**
   ```bash
   nano config/virtual-servers.txt
   ```

2. **Add server definitions:**
   ```text
   my-search-server|tavily,brave-search
   my-dev-server|sequential-thinking,playwright,snyk,github
   my-docs-server|Context7,prisma-remote
   ```

3. **Register servers:**
   ```bash
   make register
   ```

4. **Get connection URLs:**
   The script prints a URL for each server:
   ```
   Virtual server: my-search-server
   URL: http://localhost:4444/servers/abc123/mcp

   Virtual server: my-dev-server
   URL: http://localhost:4444/servers/def456/mcp
   ```

5. **Connect IDE:**
   Add each URL as a separate MCP server in your IDE config.

## Use Cases

### By Workflow

**Search & Research:**
```text
cursor-search|tavily,brave-search,exa,Context7
```

**Development & Testing:**
```text
cursor-dev|sequential-thinking,playwright,chrome-devtools,snyk
```

**Documentation & Learning:**
```text
cursor-docs|Context7,prisma-remote,deepwiki
```

**File Operations:**
```text
cursor-files|filesystem,git-mcp,memory
```

### By Technology Stack

**Frontend Development:**
```text
cursor-frontend|sequential-thinking,playwright,chrome-devtools,browser-tools
```

**Backend Development:**
```text
cursor-backend|snyk,github,postgres,mongodb
```

**Full Stack:**
```text
cursor-fullstack|sequential-thinking,playwright,snyk,github,postgres
```

## Managing Tool Limits

### Check Tool Count

```bash
# List all tools from a virtual server
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:4444/servers/<UUID>/tools
```

### Strategies

1. **Multiple Focused Servers** (Recommended)
   - Create 2-3 servers with 20-30 tools each
   - Switch between them based on task
   - Avoid tool limit warnings

2. **Single Router Server**
   - Use cursor-router (tool-router)
   - Only 1-2 tools exposed
   - Dynamic access to all tools

3. **Hybrid Approach**
   - cursor-router for general use
   - Specialized servers for specific workflows
   - Best of both worlds

## Admin UI Management

### Creating Virtual Servers

1. Open Admin UI: http://localhost:4444/admin
2. Navigate to **Virtual Servers**
3. Click **Create Virtual Server**
4. Configure:
   - Name: `my-server`
   - Description: Purpose of this server
   - Select gateways to include
5. Save and note the UUID

### Editing Virtual Servers

1. Find server in **Virtual Servers** list
2. Click **Edit**
3. Add/remove gateways
4. Update tools list
5. Save changes

### Viewing Tools

1. Select virtual server
2. View **Tools** tab
3. See all available tools
4. Test tools directly in UI

## Connection Examples

### Cursor/VS Code

```json
{
  "mcpServers": {
    "search-server": {
      "command": "npx",
      "args": [
        "-y",
        "@forge-mcp-gateway/client",
        "--url=http://localhost:4444/servers/abc123/mcp",
        "--token=<JWT>"
      ]
    },
    "dev-server": {
      "command": "npx",
      "args": [
        "-y",
        "@forge-mcp-gateway/client",
        "--url=http://localhost:4444/servers/def456/mcp",
        "--token=<JWT>"
      ]
    }
  }
}
```

### Windsurf

```json
{
  "mcpServers": {
    "search-server": {
      "command": "node",
      "args": [
        "/path/to/forge-mcp-gateway/build/index.js"
      ],
      "env": {
        "GATEWAY_URL": "http://localhost:4444",
        "GATEWAY_JWT": "<JWT>",
        "VIRTUAL_SERVER_UUID": "abc123"
      }
    }
  }
}
```

## Best Practices

1. **Keep servers focused** - 20-30 tools per server
2. **Use descriptive names** - `cursor-search`, not `server1`
3. **Document purpose** - Add descriptions in Admin UI
4. **Test tool count** - Verify under 60 tools
5. **Update regularly** - Refresh when adding gateways

## Troubleshooting

### Too Many Tools Warning

**Symptom:** IDE warns about tool limit exceeded

**Solution:**
1. Count tools in virtual server
2. Create multiple focused servers
3. Or switch to cursor-router

### Server Not Found

**Symptom:** Connection fails with "server not found"

**Solution:**
1. Verify UUID in URL
2. Check server exists in Admin UI
3. Regenerate with `make register`

### Tools Not Appearing

**Symptom:** Expected tools missing from IDE

**Solution:**
1. Check gateway is registered
2. Verify gateway is attached to virtual server
3. Restart IDE to refresh tool list

## Next Steps

- **[Tool Router Guide](TOOL_ROUTER_GUIDE.md)** - Single entry point pattern
- **[Admin UI Registration](../configuration/ADMIN_UI_MANUAL_REGISTRATION.md)** - Manual setup
- **[AI Usage Guide](../operations/AI_USAGE.md)** - Effective tool usage
