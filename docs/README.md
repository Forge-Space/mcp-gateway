# MCP Gateway Documentation

Complete documentation for the MCP Gateway (Context Forge) project.

## 📚 Documentation Structure

### Getting Started

Start here if you're new to the project.

- **[Quick Start Guide](../README.md#quick-start)** - Get up and running in 5 minutes
- **[Installation & Setup](setup/INSTALLATION.md)** - Detailed installation instructions
- **[IDE Setup Guide](setup/IDE_SETUP_GUIDE.md)** - Configure your IDE (Cursor, VS Code, Windsurf)
- **[Environment Configuration](setup/ENVIRONMENT_CONFIGURATION.md)** - Configure .env and environment variables

### Core Concepts

Understand the architecture and key concepts.

- **[Architecture Overview](architecture/OVERVIEW.md)** - System architecture and components
- **[Tool Router Guide](architecture/TOOL_ROUTER_GUIDE.md)** - Single entry point pattern
- **[Virtual Servers](architecture/VIRTUAL_SERVERS.md)** - Managing tool collections

### Configuration & Deployment

Configure and deploy the gateway.

- **[MCP Stack Configurations](configuration/MCP_STACK_CONFIGURATIONS.md)** - Stack-specific setups
- **[Multi-User Database Config](configuration/MULTI_USER_DATABASE_CONFIG.md)** - PostgreSQL/MongoDB setup
- **[Admin UI Manual Registration](configuration/ADMIN_UI_MANUAL_REGISTRATION.md)** - Manual gateway registration

### Development

Contributing and developing the project.

- **[Development Guide](development/DEVELOPMENT.md)** - Local development setup
- **[Implementation Summary](development/IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[Monorepo vs Single Repo](development/MONOREPO_VS_SINGLE_REPO.md)** - Repository structure decisions

### Operations & Maintenance

Running and maintaining the gateway.

- **[AI Usage Guide](operations/AI_USAGE.md)** - Using AI tools effectively
- **[Troubleshooting](operations/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Monitoring & Observability](operations/MONITORING.md)** - Health checks and metrics

### Migration & Upgrades

Migrating from older versions or other setups.

- **[IDE Agnostic Migration](migration/IDE_AGNOSTIC_MIGRATION.md)** - Migrate to IDE-agnostic configuration
- **[Upgrade Guide](migration/UPGRADE_GUIDE.md)** - Version upgrade instructions

### Tools & Automation

CI/CD, code quality, and automation.

- **[CodeRabbit Setup](tools/CODERABBIT_SETUP.md)** - AI code review configuration
- **[Scripts Reference](../scripts/README.md)** - Available automation scripts

## 🔍 Quick Links

### Common Tasks

- [Start the gateway](../README.md#quick-start)
- [Register gateways](../README.md#registering-url-based-mcp-servers)
- [Connect to Cursor](../README.md#connect-cursor)
- [Generate JWT token](setup/ENVIRONMENT_CONFIGURATION.md#jwt-token-generation)
- [Add new MCP server](configuration/ADMIN_UI_MANUAL_REGISTRATION.md)

### Troubleshooting

- [Gateway won't start](operations/TROUBLESHOOTING.md#gateway-startup-issues)
- [Connection timeouts](operations/TROUBLESHOOTING.md#connection-timeouts)
- [JWT authentication errors](operations/TROUBLESHOOTING.md#jwt-errors)
- [Tool limit exceeded](operations/AI_USAGE.md#tool-limit-and-virtual-servers)

## 📖 External Resources

- [IBM Context Forge](https://github.com/IBM/mcp-context-forge) - Upstream project
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [NPM Package](https://www.npmjs.com/package/@mcp-gateway/client) - TypeScript client

## 🤝 Contributing

See [DEVELOPMENT.md](development/DEVELOPMENT.md) for contribution guidelines.

## 📝 License

[MIT License](../LICENSE)
