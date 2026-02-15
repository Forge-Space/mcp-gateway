# Server Lifecycle Management API

## Overview

The Server Lifecycle Management API provides REST endpoints for managing virtual servers in the MCP Gateway. These endpoints allow you to list, query, enable, and disable virtual servers programmatically.

## Base URL

```
http://localhost:4444/api
```

For production deployments, replace with your gateway URL.

## Authentication

Currently, the API endpoints are accessible without authentication when running locally. For production deployments, implement proper authentication:

**Recommended Approaches:**
- **API Keys**: Use environment-configured tokens (e.g., `API_KEY` in env vars, validate via middleware)
- **OAuth2/OpenID Connect**: For user-based flows with identity providers
- **Reverse Proxy/API Gateway**: Place service behind nginx/Traefik/Kong that enforces authentication

**Security Best Practices:**
- Store credentials in environment variables or secrets management systems (never hardcode)
- Enable TLS/HTTPS in production (e.g., `ssl_certificate` in nginx, Let's Encrypt)
- Rotate API keys regularly and audit access logs
- Example: `Authorization: Bearer ${API_TOKEN}` header with token validation middleware

## Endpoints

### List All Virtual Servers

Get a list of all virtual servers with their status.

**Endpoint:** `GET /api/virtual-servers`

**Response:**
```json
{
  "servers": [
    {
      "name": "cursor-default",
      "gateways": ["sequential-thinking", "filesystem", "tavily"],
      "enabled": true
    },
    {
      "name": "cursor-search",
      "gateways": ["tavily", "brave-search"],
      "enabled": false
    }
  ],
  "summary": {
    "total": 2,
    "enabled": 1,
    "disabled": 1
  }
}
```

**Status Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl http://localhost:4444/api/virtual-servers
```

---

### Get Server Status

Get details about a specific virtual server.

**Endpoint:** `GET /api/virtual-servers/{server_name}`

**Parameters:**
- `server_name` (path) - Name of the server

**Response (Success):**
```json
{
  "name": "cursor-default",
  "gateways": ["sequential-thinking", "filesystem"],
  "enabled": true,
  "found": true
}
```

**Response (Not Found):**
```json
{
  "error": "Server 'nonexistent' not found",
  "found": false
}
```

**Status Codes:**
- `200 OK` - Server found
- `404 Not Found` - Server not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl http://localhost:4444/api/virtual-servers/cursor-default
```

---

### Update Server Status

Enable or disable a virtual server.

**Endpoint:** `PATCH /api/virtual-servers/{server_name}`

**Parameters:**
- `server_name` (path) - Name of the server

**Request Body:**
```json
{
  "enabled": true
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Server 'cursor-default' enabled",
  "server_name": "cursor-default",
  "enabled": true
}
```

**Response (Not Found):**
```json
{
  "success": false,
  "error": "Server 'nonexistent' not found"
}
```

**Response (Bad Request):**
```json
{
  "error": "Missing 'enabled' field in request body"
}
```

**Status Codes:**
- `200 OK` - Update successful
- `400 Bad Request` - Invalid request body
- `404 Not Found` - Server not found
- `500 Internal Server Error` - Server error

**Examples:**

Enable a server:
```bash
curl -X PATCH http://localhost:4444/api/virtual-servers/cursor-search \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

Disable a server:
```bash
curl -X PATCH http://localhost:4444/api/virtual-servers/cursor-default \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

---

## Integration Examples

### JavaScript/TypeScript (React)

```typescript
// List all servers
async function listServers() {
  const response = await fetch('http://localhost:4444/api/virtual-servers');
  const data = await response.json();
  return data;
}

// Get server status
async function getServerStatus(serverName: string) {
  const response = await fetch(
    `http://localhost:4444/api/virtual-servers/${serverName}`
  );
  const data = await response.json();
  return data;
}

// Enable/disable server
async function updateServer(serverName: string, enabled: boolean) {
  const response = await fetch(
    `http://localhost:4444/api/virtual-servers/${serverName}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ enabled }),
    }
  );
  const data = await response.json();
  return data;
}

// React component example
function ServerToggle({ serverName, initialEnabled }) {
  const [enabled, setEnabled] = useState(initialEnabled);
  const [loading, setLoading] = useState(false);

  const handleToggle = async () => {
    setLoading(true);
    try {
      const result = await updateServer(serverName, !enabled);
      if (result.success) {
        setEnabled(!enabled);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleToggle} disabled={loading}>
      {enabled ? 'Disable' : 'Enable'} {serverName}
    </button>
  );
}
```

### Python

```python
import requests

BASE_URL = "http://localhost:4444/api"

# List all servers
def list_servers():
    response = requests.get(f"{BASE_URL}/virtual-servers")
    return response.json()

# Get server status
def get_server_status(server_name):
    response = requests.get(f"{BASE_URL}/virtual-servers/{server_name}")
    return response.json()

# Enable server
def enable_server(server_name):
    response = requests.patch(
        f"{BASE_URL}/virtual-servers/{server_name}",
        json={"enabled": True}
    )
    return response.json()

# Disable server
def disable_server(server_name):
    response = requests.patch(
        f"{BASE_URL}/virtual-servers/{server_name}",
        json={"enabled": False}
    )
    return response.json()
```

### cURL

```bash
# List all servers
curl http://localhost:4444/api/virtual-servers

# Get server status
curl http://localhost:4444/api/virtual-servers/cursor-default

# Enable server
curl -X PATCH http://localhost:4444/api/virtual-servers/cursor-search \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Disable server
curl -X PATCH http://localhost:4444/api/virtual-servers/cursor-default \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

---

## Error Handling

All endpoints return JSON responses with appropriate HTTP status codes.

**Common Error Response Format:**
```json
{
  "error": "Error message describing what went wrong"
}
```

**Error Codes:**
- `400 Bad Request` - Invalid request parameters or body
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Unexpected server error

---

## MCP Tools

In addition to REST endpoints, the same functionality is available as MCP tools for IDE integration:

- `list_servers_tool()` - List all servers
- `get_server_status_tool(server_name)` - Get server status
- `enable_server_tool(server_name)` - Enable a server
- `disable_server_tool(server_name)` - Disable a server

These tools are automatically available when connecting to the tool-router MCP server.

---

## Troubleshooting

### Connection Failures

**Symptoms:** API returns 500 errors, timeouts, or "Service Unavailable"

**Likely Causes:**
- Gateway service not running or unreachable
- Network connectivity issues
- Service endpoint misconfigured

**HTTP Status:** 500 (Internal Server Error), 503 (Service Unavailable)

**Quick Resolution:** Check service status (`docker compose ps gateway`), verify network connectivity, retry request after confirming endpoints are accessible.

### Permission Errors (virtual-servers.txt)

**Symptoms:** API returns 403/400 errors with "Permission denied" or "Cannot write to file"

**Likely Causes:**
- Insufficient file permissions on `config/virtual-servers.txt`
- Incorrect file ownership
- Read-only filesystem

**HTTP Status:** 403 (Forbidden), 400 (Bad Request)

**Quick Resolution:** Check file permissions (`ls -la config/virtual-servers.txt`), fix with `chmod 644 config/virtual-servers.txt`, ensure correct ownership (`chown user:group config/virtual-servers.txt`).

### Backup File Conflicts

**Symptoms:** API returns errors mentioning `.bak` files or "File exists"

**Likely Causes:**
- Previous backup files not cleaned up
- Concurrent operations creating conflicting backups
- Disk space issues

**HTTP Status:** 500 (Internal Server Error)

**Quick Resolution:** Remove stale backup files (`rm config/virtual-servers.txt.bak*`), ensure sufficient disk space, retry operation. For safe recovery, restore from backup if needed (`cp config/virtual-servers.txt.bak config/virtual-servers.txt`).

**Note:** All errors follow the Common Error Response Format with `error` and optional `detail` fields. Check response body for specific error messages.

---

## Notes

- Changes to server status are persisted to `config/virtual-servers.txt`
- Automatic backups are created before modifications (`.txt.bak`)
- After enabling/disabling servers, run `make register` to apply changes
- Disabled servers are not created during registration

---

**Last Updated:** 2026-02-15
**API Version:** 1.0.0
