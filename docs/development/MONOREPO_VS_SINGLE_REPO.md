# Monorepo vs Single-Repo Configuration

Choosing the right MCP stack profile based on your project architecture.

## Quick Decision

**Use Monorepo Profile if:**
- Multiple packages/apps in one repository
- Shared libraries or components
- Using Nx, Turborepo, Lerna, or Yarn Workspaces
- Cross-project dependencies

**Use Single-Repo Profile if:**
- One application per repository
- Standalone projects
- Traditional project structure
- No workspace management

## Architecture Comparison

### Single-Repo Structure

```
my-project/
├── src/
│   ├── components/
│   ├── services/
│   └── utils/
├── tests/
├── package.json
└── README.md
```

**Characteristics:**
- One application
- Single package.json
- Straightforward dependencies
- Simple build process

**Recommended Profiles:**
- `nodejs-typescript` / `nodejs-typescript-minimal`
- `react-nextjs` / `react-nextjs-minimal`
- `python-dev` / `python-dev-minimal`
- `java-spring` / `java-spring-minimal`

### Monorepo Structure

```
my-monorepo/
├── apps/
│   ├── web/          (Next.js app)
│   ├── mobile/       (React Native app)
│   └── api/          (Node.js API)
├── packages/
│   ├── ui/           (Shared components)
│   ├── utils/        (Shared utilities)
│   └── types/        (Shared types)
├── package.json      (Root workspace)
└── nx.json / turbo.json
```

**Characteristics:**
- Multiple applications
- Shared packages
- Workspace management
- Complex build orchestration
- Cross-project dependencies

**Recommended Profiles:**
- `monorepo-universal` / `monorepo-universal-minimal`
- `fullstack-universal` / `fullstack-universal-minimal`

## Configuration Differences

### Single-Repo Configuration

**Focus:** Individual project needs

```json
{
  "mcpServers": {
    "react-nextjs": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "react-nextjs"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"
      }
    }
  }
}
```

**Tools Included:**
- GitHub (project-level operations)
- Filesystem (single project navigation)
- Chrome DevTools (UI debugging)
- Git (single repo operations)

### Monorepo Configuration

**Focus:** Workspace management and cross-project operations

```json
{
  "mcpServers": {
    "monorepo-universal": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "monorepo-universal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx",
        "SNYK_TOKEN": "xxx",
        "TAVILY_API_KEY": "tvly_xxx"
      }
    }
  }
}
```

**Tools Included:**
- GitHub (multi-project operations)
- Filesystem (workspace navigation)
- Memory (cross-project context)
- Git (workspace-aware operations)
- Snyk (workspace-wide security)
- Tavily (documentation search)
- Context7 (framework docs)
- Playwright (E2E across apps)

## Use Case Examples

### Example 1: Single-Repo React App

**Project:**
```
my-app/
├── src/
├── public/
├── package.json
└── README.md
```

**Best Profile:** `react-nextjs-minimal`

**Why:**
- Single application
- No workspace complexity
- Fast performance needed
- Minimal tool overhead

**Configuration:**
```json
{
  "mcpServers": {
    "react-nextjs-minimal": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "react-nextjs-minimal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"
      }
    }
  }
}
```

### Example 2: Nx Monorepo

**Project:**
```
my-workspace/
├── apps/
│   ├── web/
│   ├── mobile/
│   └── api/
├── libs/
│   ├── shared-ui/
│   └── shared-utils/
├── nx.json
└── package.json
```

**Best Profile:** `monorepo-universal`

**Why:**
- Multiple applications
- Shared libraries
- Complex dependencies
- Need comprehensive tooling

**Configuration:**
```json
{
  "mcpServers": {
    "monorepo-universal": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "monorepo-universal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx",
        "SNYK_TOKEN": "xxx",
        "TAVILY_API_KEY": "tvly_xxx"
      }
    }
  }
}
```

### Example 3: Turborepo Full-Stack

**Project:**
```
my-turborepo/
├── apps/
│   ├── web/          (Next.js)
│   └── docs/         (Docusaurus)
├── packages/
│   ├── ui/
│   ├── config/
│   └── tsconfig/
├── turbo.json
└── package.json
```

**Best Profile:** `fullstack-universal`

**Why:**
- Full-stack applications
- Shared packages
- Database integration
- Comprehensive development

**Configuration:**
```json
{
  "mcpServers": {
    "fullstack-universal": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "fullstack-universal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx",
        "POSTGRES_CONNECTION_STRING": "postgresql://...",
        "MONGODB_CONNECTION_STRING": "mongodb://...",
        "SNYK_TOKEN": "xxx",
        "TAVILY_API_KEY": "tvly_xxx"
      }
    }
  }
}
```

### Example 4: Python Microservices

**Project:**
```
my-services/
├── services/
│   ├── auth-service/
│   ├── user-service/
│   └── payment-service/
├── shared/
│   ├── models/
│   └── utils/
└── pyproject.toml
```

**Best Profile:** `monorepo-universal` or `python-dev`

**Why:**
- Multiple services
- Shared code
- Python-specific tooling

**Configuration:**
```json
{
  "mcpServers": {
    "monorepo-universal": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "monorepo-universal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx",
        "SNYK_TOKEN": "xxx",
        "TAVILY_API_KEY": "tvly_xxx"
      }
    }
  }
}
```

## Tool Differences

### Single-Repo Tools

| Tool | Purpose | Why Needed |
|------|---------|------------|
| GitHub | Code management | Single repo operations |
| Filesystem | File operations | Project navigation |
| Git | Version control | Single repo commits |
| Chrome DevTools | Debugging | UI development |

### Monorepo Tools

| Tool | Purpose | Why Needed |
|------|---------|------------|
| GitHub | Code management | Multi-project operations |
| Filesystem | File operations | Workspace navigation |
| Memory | Context retention | Cross-project context |
| Git | Version control | Workspace-aware commits |
| Snyk | Security | Workspace-wide scanning |
| Tavily | Search | Documentation across projects |
| Context7 | Framework docs | Multi-framework support |
| Playwright | E2E testing | Cross-app testing |

## Performance Considerations

### Single-Repo

**Advantages:**
- Faster tool loading (fewer tools)
- Simpler context management
- Lower memory usage
- Quicker response times

**Best For:**
- Small to medium projects
- Single-purpose applications
- Performance-critical scenarios

### Monorepo

**Advantages:**
- Comprehensive tooling
- Cross-project awareness
- Better for complex workflows
- Unified development experience

**Best For:**
- Large-scale applications
- Multi-team projects
- Shared component libraries
- Complex dependencies

## Migration Guide

### From Single-Repo to Monorepo

**Step 1:** Restructure project
```bash
# Before
my-app/
├── src/
└── package.json

# After
my-workspace/
├── apps/
│   └── my-app/
│       ├── src/
│       └── package.json
├── packages/
└── package.json (workspace root)
```

**Step 2:** Update IDE configuration
```json
{
  "mcpServers": {
    "monorepo-universal": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "monorepo-universal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx",
        "SNYK_TOKEN": "xxx",
        "TAVILY_API_KEY": "tvly_xxx"
      }
    }
  }
}
```

**Step 3:** Register new profile
```bash
make register
```

### From Monorepo to Single-Repo

**Step 1:** Extract application
```bash
# Extract one app from monorepo
cp -r my-workspace/apps/my-app ./my-app
cd my-app
```

**Step 2:** Update IDE configuration
```json
{
  "mcpServers": {
    "react-nextjs": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "react-nextjs"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"
      }
    }
  }
}
```

**Step 3:** Restart IDE

## Best Practices

### For Single-Repos

1. **Use Minimal variants** for faster performance
2. **Keep dependencies simple** - avoid workspace complexity
3. **Focus on project-specific tools** - don't over-configure
4. **Regular updates** - keep dependencies current

### For Monorepos

1. **Use Full variants** for comprehensive tooling
2. **Leverage Memory tool** for cross-project context
3. **Configure workspace-aware tools** - Snyk, Playwright
4. **Document shared dependencies** - maintain clarity
5. **Use consistent naming** - across packages/apps

## Troubleshooting

### Issue: "Wrong profile for my project"

**Symptoms:**
- Missing tools for monorepo operations
- Too many tools for simple project
- Performance issues

**Solution:**
1. Assess project structure
2. Choose appropriate profile
3. Update IDE configuration
4. Restart IDE

### Issue: "Cross-project operations not working"

**Cause:** Using single-repo profile for monorepo

**Solution:** Switch to `monorepo-universal`:
```json
{
  "mcpServers": {
    "monorepo-universal": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "monorepo-universal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx",
        "SNYK_TOKEN": "xxx",
        "TAVILY_API_KEY": "tvly_xxx"
      }
    }
  }
}
```

### Issue: "Slow performance in monorepo"

**Cause:** Using Full variant with many tools

**Solution:** Switch to Minimal variant:
```json
{
  "mcpServers": {
    "monorepo-universal-minimal": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "monorepo-universal-minimal"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"
      }
    }
  }
}
```

## Next Steps

- [MCP Stack Configurations](MCP_STACK_CONFIGURATIONS.md) - Choose your stack
- [IDE Setup Guide](IDE_SETUP_GUIDE.md) - Configure your IDE
- [Tool Router Guide](TOOL_ROUTER_GUIDE.md) - How routing works
