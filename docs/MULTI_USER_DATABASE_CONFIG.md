# Multi-User Database Configuration

This guide explains how to configure PostgreSQL and MongoDB MCP servers for multi-user or multi-tenant scenarios.

## Problem Statement

By default, database connection strings in `.env` are **deployment-level** configuration:
- All users of a gateway instance share the same database credentials
- Changing credentials requires container restart
- Not suitable for scenarios where different users need different database access

## Solution Options

### Option 1: Per-Deployment Instances (Recommended)

**Best for:** Teams, organizations, or projects that need isolated infrastructure.

**How it works:**
1. Each team/organization deploys their own MCP Gateway instance
2. Each deployment has its own `.env` with team-specific credentials
3. Complete isolation between deployments

**Pros:**
- Simple architecture (no code changes)
- Strong security isolation
- Each team controls their own infrastructure
- Standard practice for self-hosted tools

**Setup:**
```bash
# Team A deployment
POSTGRES_CONNECTION_STRING=postgresql://team_a_user:pass@db-team-a:5432/team_a_db
MONGODB_CONNECTION_STRING=mongodb://team_a_user:pass@mongo-team-a:27017/team_a_db

# Team B deployment (separate instance)
POSTGRES_CONNECTION_STRING=postgresql://team_b_user:pass@db-team-b:5432/team_b_db
MONGODB_CONNECTION_STRING=mongodb://team_b_user:pass@mongo-team-b:27017/team_b_db
```

### Option 2: Admin UI Passthrough Headers (Advanced)

**Best for:** Shared gateway with per-user credentials.

**Current Limitation:** MCP servers like `@modelcontextprotocol/server-postgres` and `mongodb-mcp-server` accept connection strings at **startup time only**, not per-request. They cannot dynamically change database connections based on HTTP headers.

**Workaround (Requires Custom Implementation):**

To support per-user credentials, you would need to:

1. **Create a proxy MCP server** that:
   - Accepts connection strings via HTTP headers (e.g., `X-Database-Connection-String`)
   - Spawns ephemeral MCP server processes with user-specific credentials
   - Routes requests to the appropriate process

2. **Use Admin UI Passthrough Headers:**
   - Users configure their credentials in Admin UI when registering the gateway
   - Gateway forwards credentials as headers to your proxy server
   - Proxy server handles per-user database connections

**Example proxy architecture:**
```
User Request → Gateway (with X-Database-Connection-String header)
            → Proxy MCP Server
            → Spawns @modelcontextprotocol/server-postgres with user's credentials
            → Returns results
```

**Note:** This requires custom development and is not supported out-of-the-box.

### Option 3: Environment-Based Multi-Tenancy

**Best for:** Predefined set of tenants (e.g., dev/staging/prod).

**How it works:**
1. Deploy multiple database service containers in `docker-compose.yml`
2. Each container connects to a different database
3. Users select which database gateway to use

**Example docker-compose.yml:**
```yaml
postgres-dev:
  <<: *translate
  env_file: .env
  command:
    - sh
    - -c
    - 'python3 -m mcpgateway.translate --stdio "npx -y @modelcontextprotocol/server-postgres ${POSTGRES_DEV_CONNECTION_STRING}" --expose-sse --port 8031 --host 0.0.0.0'
  ports:
    - "8031:8031"

postgres-prod:
  <<: *translate
  env_file: .env
  command:
    - sh
    - -c
    - 'python3 -m mcpgateway.translate --stdio "npx -y @modelcontextprotocol/server-postgres ${POSTGRES_PROD_CONNECTION_STRING}" --expose-sse --port 8033 --host 0.0.0.0'
  ports:
    - "8033:8033"
```

**gateways.txt:**
```
postgres-dev|http://postgres-dev:8031/sse|SSE
postgres-prod|http://postgres-prod:8033/sse|SSE
```

Users then select which gateway to use in their MCP client configuration.

## Recommended Approach

For most use cases, **Option 1 (Per-Deployment Instances)** is recommended because:

1. **Security:** Complete isolation between teams/organizations
2. **Simplicity:** No custom code required
3. **Flexibility:** Each deployment can be customized independently
4. **Standard Practice:** Aligns with how most self-hosted tools work (GitLab, Jenkins, etc.)

## MCP Server Limitations

Current MCP servers have architectural constraints:

- **Startup-time configuration:** Connection strings are passed when the server starts
- **No per-request credentials:** Servers cannot change database connections per HTTP request
- **Process-level isolation:** Each server process connects to one database

This is by design for security and simplicity. To support true multi-tenancy, you would need to:
- Build a custom proxy/wrapper MCP server
- Implement connection pooling and credential management
- Handle security implications of dynamic credential passing

## Security Best Practices

Regardless of which option you choose:

1. **Never commit credentials** to version control (`.env` is gitignored)
2. **Use read-only credentials** for PostgreSQL when possible
3. **Apply principle of least privilege** for MongoDB users
4. **Rotate credentials regularly**
5. **Use SSL/TLS** for database connections in production
6. **Monitor database access** and audit logs
7. **Encrypt credentials at rest** if storing in Admin UI

## Example: Per-Deployment Setup

### Team A Deployment

```bash
# .env
POSTGRES_CONNECTION_STRING=postgresql://team_a_ro:secure_pass@db.team-a.internal:5432/team_a_db?sslmode=require
MONGODB_CONNECTION_STRING=mongodb://team_a_user:secure_pass@mongo.team-a.internal:27017/team_a_db?authSource=admin&tls=true
```

### Team B Deployment

```bash
# .env
POSTGRES_CONNECTION_STRING=postgresql://team_b_ro:different_pass@db.team-b.internal:5432/team_b_db?sslmode=require
MONGODB_CONNECTION_STRING=mongodb://team_b_user:different_pass@mongo.team-b.internal:27017/team_b_db?authSource=admin&tls=true
```

Each team deploys their own gateway instance with their own credentials.

## Future Enhancements

Potential improvements for multi-user support:

1. **Dynamic credential injection:** Modify `mcpgateway.translate` to support per-request environment variables
2. **Connection pooling proxy:** Build a proxy MCP server that manages multiple database connections
3. **Credential vault integration:** Integrate with HashiCorp Vault or AWS Secrets Manager
4. **User-scoped gateways:** Allow users to register their own database gateways in Admin UI with their credentials

## References

- [Admin UI Manual Registration](./ADMIN_UI_MANUAL_REGISTRATION.md) - Passthrough Headers documentation
- [MCP Specification](https://github.com/modelcontextprotocol/specification) - Protocol details
- [PostgreSQL MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/postgres) - Anthropic reference implementation
- [MongoDB MCP Server](https://github.com/mongodb-js/mongodb-mcp-server) - Official MongoDB implementation
