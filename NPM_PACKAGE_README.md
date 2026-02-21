# @mcp-gateway/client

NPX client for connecting to MCP Gateway instances. This package allows you to use your MCP Gateway with any MCP-compatible IDE using the standard NPX configuration pattern.

## Quick Start

### Prerequisites

1. **Running MCP Gateway**: You need a running MCP Gateway instance
2. **Virtual Server**: Create a virtual server in the gateway
3. **JWT Token**: Only needed if gateway has `AUTH_REQUIRED=true` (not needed for local development)

### Installation

No installation needed! Use `npx` to run directly:

**Local Development (Default - No Auth):**

```json
{
  "mcpServers": {
    "my-gateway": {
      "command": "npx",
      "args": [
        "-y",
        "@mcp-gateway/client",
        "--url=http://localhost:4444/servers/<YOUR-SERVER-UUID>/mcp"
      ]
    }
  }
}
```

**Production/Remote (With Auth):**

```json
{
  "mcpServers": {
    "my-gateway": {
      "command": "npx",
      "args": [
        "-y",
        "@mcp-gateway/client",
        "--url=https://gateway.example.com/servers/<YOUR-SERVER-UUID>/mcp",
        "--token=<YOUR-JWT-TOKEN>"
      ]
    }
  }
}
```

### Environment Variables

Alternatively, set environment variables:

```json
{
  "mcpServers": {
    "my-gateway": {
      "command": "npx",
      "args": ["-y", "@mcp-gateway/client"],
      "env": {
        "MCP_GATEWAY_URL": "http://localhost:4444/servers/<YOUR-SERVER-UUID>/mcp",
        "MCP_GATEWAY_TOKEN": "<YOUR-JWT-TOKEN>",
        "MCP_GATEWAY_TIMEOUT": "120000"
      }
    }
  }
}
```

## Configuration

### Required Parameters

- **`--url`** or **`MCP_GATEWAY_URL`**: Full URL to your virtual server's MCP endpoint
  - Format: `http://localhost:4444/servers/<UUID>/mcp`
  - Get this from: `make register` or Admin UI

### Optional Parameters

- **`--token`** or **`MCP_GATEWAY_TOKEN`**: JWT authentication token
  - **Only required if** gateway has `AUTH_REQUIRED=true` in `.env`
  - **Not needed for local development** (default: `AUTH_REQUIRED=false`)
  - Generate with: `make jwt` or from Admin UI

- **`MCP_GATEWAY_TIMEOUT`**: Request timeout in milliseconds (default: 120000)

## Getting Your Configuration Values

### 1. Start Gateway

```bash
cd /path/to/mcp-gateway
make start
```

### 2. Register Virtual Server

```bash
make register
```

This creates a virtual server and saves the URL to `data/.cursor-mcp-url`.

### 3. (Optional) Generate JWT Token

**Only needed if you set `AUTH_REQUIRED=true` in `.env`**

```bash
make jwt
```

Copy the generated token. For local development, you can skip this step.

### 4. Configure Your IDE

**Cursor** (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "mcp-gateway": {
      "command": "npx",
      "args": [
        "-y",
        "@mcp-gateway/client",
        "--url=http://localhost:4444/servers/abc-123-def/mcp"
      ],
      "timeout": 120000
    }
  }
}
```

**VS Code** (`.vscode/settings.json`):

```json
{
  "mcp.servers": {
    "mcp-gateway": {
      "command": "npx",
      "args": [
        "-y",
        "@mcp-gateway/client",
        "--url=http://localhost:4444/servers/abc-123-def/mcp"
      ]
    }
  }
}
```

**Windsurf** (`~/.windsurf/mcp.json`):

```json
{
  "mcpServers": {
    "mcp-gateway": {
      "command": "npx",
      "args": [
        "-y",
        "@mcp-gateway/client",
        "--url=http://localhost:4444/servers/abc-123-def/mcp"
      ]
    }
  }
}
```

> **Note**: Add `"--token=<JWT>"` to args only if your gateway has `AUTH_REQUIRED=true`

## Features

- ✅ **Standard MCP Protocol**: Works with any MCP-compatible IDE
- ✅ **No Installation**: Use `npx` to run without installing
- ✅ **Tools**: Access all tools from your gateway's virtual server
- ✅ **Resources**: Read resources exposed by the gateway
- ✅ **Prompts**: Use prompts configured in the gateway
- ✅ **Authentication**: Secure JWT-based authentication
- ✅ **Timeout Control**: Configurable request timeouts

## Troubleshooting

### "MCP_GATEWAY_URL is required" or "MCP_GATEWAY_TOKEN is required"

MCP_GATEWAY_URL is always required. MCP_GATEWAY_TOKEN is only required when the gateway has AUTH_REQUIRED=true (production/remote setups). For local development with AUTH_REQUIRED=false, no token is needed.

### "Gateway request failed: 401 Unauthorized"

Your JWT token may have expired. Generate a new one:

```bash
cd /path/to/mcp-gateway
make jwt
```

### "Gateway request timeout"

Increase the timeout:

```json
{
  "env": {
    "MCP_GATEWAY_TIMEOUT": "180000"
  }
}
```

### Connection Issues

1. Verify gateway is running: `docker ps | grep mcpgateway`
2. Check gateway health: `curl http://localhost:4444/health`
3. Verify virtual server exists in Admin UI: `http://localhost:4444`

## Comparison: NPX vs Shell Wrapper

| Feature | NPX Client | Shell Wrapper |
|---------|-----------|---------------|
| Installation | `npx` (no install) | Requires repo clone |
| Configuration | IDE's mcp.json | IDE's mcp.json |
| Dependencies | Node.js only | Docker + Bash + Python |
| Portability | Cross-platform | macOS/Linux only |
| Updates | Auto via npx -y | Manual git pull |

## Advanced Usage

### Multiple Gateway Instances

Configure different virtual servers:

```json
{
  "mcpServers": {
    "gateway-dev": {
      "command": "npx",
      "args": ["-y", "@mcp-gateway/client"],
      "env": {
        "MCP_GATEWAY_URL": "http://localhost:4444/servers/dev-uuid/mcp",
        "MCP_GATEWAY_TOKEN": "dev-token"
      }
    },
    "gateway-prod": {
      "command": "npx",
      "args": ["-y", "@mcp-gateway/client"],
      "env": {
        "MCP_GATEWAY_URL": "https://prod.example.com/servers/prod-uuid/mcp",
        "MCP_GATEWAY_TOKEN": "prod-token"
      }
    }
  }
}
```

### Remote Gateway

Connect to a remote gateway instance:

```json
{
  "mcpServers": {
    "remote-gateway": {
      "command": "npx",
      "args": [
        "-y",
        "@mcp-gateway/client",
        "--url=https://gateway.example.com/servers/uuid/mcp",
        "--token=your-token"
      ]
    }
  }
}
```

## Development

### Building from Source

```bash
git clone https://github.com/lucassantana/mcp-gateway.git
cd mcp-gateway
npm install
npm run build
```

### Testing Locally

```bash
# Link for local testing
npm link

# Use in IDE config
{
  "command": "mcp-gateway",
  "args": ["--url=...", "--token=..."]
}
```

## License

MIT

## Support

- **Documentation**: [MCP Gateway README](https://github.com/lucassantana/mcp-gateway/blob/main/README.md)
- **Issues**: [GitHub Issues](https://github.com/lucassantana/mcp-gateway/issues)
- **Discussions**: [GitHub Discussions](https://github.com/lucassantana/mcp-gateway/discussions)
