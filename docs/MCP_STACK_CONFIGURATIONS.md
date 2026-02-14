# MCP Stack Configurations

Complete guide to optimal MCP configurations for various tech stacks, all compatible with any IDE (Cursor, VSCode, Windsurf, JetBrains, AntiGRAVITY).

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Stack Profiles](#stack-profiles)
  - [Node.js/TypeScript](#nodejstypescript)
  - [React/Next.js](#reactnextjs)
  - [Mobile Development](#mobile-development)
  - [Database Development](#database-development)
  - [Java/Spring Boot](#javaspring-boot)
  - [Python Development](#python-development)
  - [AWS Cloud](#aws-cloud)
  - [Testing & QA](#testing--qa)
  - [Code Quality & Security](#code-quality--security)
  - [Full-Stack Universal](#full-stack-universal)
  - [Monorepo Universal](#monorepo-universal)
  - [DevOps & CI/CD](#devops--cicd)
- [Full vs Minimal Variants](#full-vs-minimal-variants)
- [Configuration Guide](#configuration-guide)

## Overview

Each stack profile is optimized for specific development workflows and includes:

- **Tool-Router Integration**: All profiles route through `tool-router` for IDE compatibility
- **Full & Minimal Variants**: Choose between comprehensive tooling or streamlined performance
- **IDE Agnostic**: Works with Cursor, VSCode, Windsurf, JetBrains, and AntiGRAVITY
- **API Keys in IDE**: Stack-specific credentials configured in IDE's mcp.json, not .env

## Quick Start

1. **Choose your stack profile** from the list below
2. **Configure API keys** in your IDE's mcp.json (see [IDE Setup Guide](IDE_SETUP_GUIDE.md))
3. **Register the profile**: `make register`
4. **Connect your IDE** to the generated URL

## Stack Profiles

### Node.js/TypeScript

**Purpose**: Full-stack JavaScript/TypeScript development with Node.js runtime

**Full Variant** (`nodejs-typescript`):
- **Included Tools**: GitHub, Filesystem, Memory, Git, Snyk, Tavily, Context7
- **Use Cases**:
  - Building Node.js APIs and services
  - TypeScript application development
  - Package management and dependencies
  - Security scanning and vulnerability detection
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`nodejs-typescript-minimal`):
- **Included Tools**: GitHub, Filesystem, Git
- **Use Cases**: Quick edits, code reviews, lightweight development
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN

---

### React/Next.js

**Purpose**: Modern web application development with React and Next.js

**Full Variant** (`react-nextjs`):
- **Included Tools**: GitHub, Filesystem, Memory, Git, Chrome DevTools, Playwright, Snyk, Tavily, Context7
- **Use Cases**:
  - React component development
  - Next.js application building
  - Browser testing and debugging
  - UI/UX development with live preview
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`react-nextjs-minimal`):
- **Included Tools**: GitHub, Filesystem, Chrome DevTools
- **Use Cases**: Component editing, quick debugging, code reviews
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN

---

### Mobile Development

**Purpose**: React Native and Flutter mobile application development

**Full Variant** (`mobile-dev`):
- **Included Tools**: GitHub, Filesystem, Memory, Git, Snyk, Tavily, Context7
- **Use Cases**:
  - React Native app development
  - Flutter application building
  - Mobile-specific debugging
  - Cross-platform development
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`mobile-dev-minimal`):
- **Included Tools**: GitHub, Filesystem, Git
- **Use Cases**: Quick fixes, code reviews, lightweight mobile dev
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN

---

### Database Development

**Purpose**: Database design, queries, and ORM management

**Full Variant** (`database-dev`):
- **Included Tools**: PostgreSQL, MongoDB, Prisma, Memory, Filesystem, Git
- **Use Cases**:
  - Database schema design
  - SQL/NoSQL query development
  - Prisma ORM integration
  - Migration management
- **Required API Keys**: POSTGRES_CONNECTION_STRING, MONGODB_CONNECTION_STRING

**Minimal Variant** (`database-dev-minimal`):
- **Included Tools**: PostgreSQL, MongoDB, Prisma
- **Use Cases**: Quick queries, schema checks, ORM operations
- **Required API Keys**: POSTGRES_CONNECTION_STRING, MONGODB_CONNECTION_STRING

---

### Java/Spring Boot

**Purpose**: Enterprise Java development with Spring Boot framework

**Full Variant** (`java-spring`):
- **Included Tools**: GitHub, Filesystem, Memory, Git, Snyk, Tavily, Context7
- **Use Cases**:
  - Spring Boot application development
  - RESTful API creation
  - Dependency injection and configuration
  - Security and testing
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`java-spring-minimal`):
- **Included Tools**: GitHub, Filesystem, Git
- **Use Cases**: Code reviews, quick fixes, lightweight Java dev
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN

---

### Python Development

**Purpose**: Python application development and data science

**Full Variant** (`python-dev`):
- **Included Tools**: GitHub, Filesystem, Memory, Git, Snyk, Tavily, Context7
- **Use Cases**:
  - Python application development
  - Data science and ML projects
  - Script automation
  - Package management
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`python-dev-minimal`):
- **Included Tools**: GitHub, Filesystem, Git
- **Use Cases**: Quick scripts, code reviews, lightweight Python dev
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN

---

### AWS Cloud

**Purpose**: AWS cloud infrastructure and serverless development

**Full Variant** (`aws-cloud`):
- **Included Tools**: GitHub, Filesystem, Memory, Git, Snyk, Tavily
- **Use Cases**:
  - AWS Lambda development
  - Infrastructure as Code (CloudFormation, CDK)
  - Serverless application building
  - Cloud security scanning
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`aws-cloud-minimal`):
- **Included Tools**: GitHub, Filesystem, Git
- **Use Cases**: Quick IaC edits, code reviews, lightweight cloud dev
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN

---

### Testing & QA

**Purpose**: Comprehensive testing and quality assurance

**Full Variant** (`testing-qa`):
- **Included Tools**: GitHub, Filesystem, Playwright, Chrome DevTools, Snyk, Memory, Git
- **Use Cases**:
  - E2E test development
  - Browser automation
  - Security testing
  - Test coverage analysis
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN

**Minimal Variant** (`testing-qa-minimal`):
- **Included Tools**: GitHub, Playwright, Snyk
- **Use Cases**: Quick test runs, basic E2E testing, security scans
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN

---

### Code Quality & Security

**Purpose**: Code analysis, security scanning, and quality enforcement

**Full Variant** (`code-quality`):
- **Included Tools**: GitHub, Snyk, Filesystem, Memory, Git, Tavily
- **Use Cases**:
  - Security vulnerability scanning
  - Code quality analysis
  - Dependency auditing
  - Best practices enforcement
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`code-quality-minimal`):
- **Included Tools**: GitHub, Snyk, Git
- **Use Cases**: Quick security scans, basic quality checks
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN

---

### Full-Stack Universal

**Purpose**: Comprehensive full-stack development with all tools

**Full Variant** (`fullstack-universal`):
- **Included Tools**: GitHub, PostgreSQL, MongoDB, Prisma, Filesystem, Memory, Git, Snyk, Tavily, Context7
- **Use Cases**:
  - Complete full-stack applications
  - Frontend + Backend + Database
  - Monolithic applications
  - Comprehensive development workflows
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, POSTGRES_CONNECTION_STRING, MONGODB_CONNECTION_STRING, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`fullstack-universal-minimal`):
- **Included Tools**: GitHub, PostgreSQL, MongoDB, Filesystem, Git
- **Use Cases**: Quick full-stack edits, code reviews
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, POSTGRES_CONNECTION_STRING, MONGODB_CONNECTION_STRING

---

### Monorepo Universal

**Purpose**: Optimized for monorepo architectures (Nx, Turborepo, Lerna)

**Full Variant** (`monorepo-universal`):
- **Included Tools**: GitHub, Filesystem, Memory, Git, Snyk, Tavily, Context7, Playwright
- **Use Cases**:
  - Multi-package monorepos
  - Shared libraries and components
  - Cross-project dependencies
  - Workspace management
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`monorepo-universal-minimal`):
- **Included Tools**: GitHub, Filesystem, Git, Memory
- **Use Cases**: Quick monorepo navigation, code reviews
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN

---

### DevOps & CI/CD

**Purpose**: DevOps workflows, CI/CD pipelines, and infrastructure automation

**Full Variant** (`devops-cicd`):
- **Included Tools**: GitHub, Filesystem, Memory, Git, Snyk, Tavily
- **Use Cases**:
  - CI/CD pipeline development
  - Infrastructure automation
  - Deployment scripts
  - Security scanning in pipelines
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN, SNYK_TOKEN, TAVILY_API_KEY

**Minimal Variant** (`devops-cicd-minimal`):
- **Included Tools**: GitHub, Filesystem, Git
- **Use Cases**: Quick pipeline edits, config reviews
- **Required API Keys**: GITHUB_PERSONAL_ACCESS_TOKEN

---

## Full vs Minimal Variants

| Aspect | Full Variant | Minimal Variant |
|--------|-------------|-----------------|
| **Tool Count** | 7-11 tools | 3-4 tools |
| **Performance** | Comprehensive, may be slower | Fast, streamlined |
| **Use Cases** | Complete development workflows | Quick edits, code reviews |
| **API Keys Required** | 3-5 keys | 1-2 keys |
| **Best For** | Primary development environment | Secondary/lightweight use |

**When to use Full**:
- Primary development environment
- Need comprehensive tooling
- Complex workflows requiring multiple integrations
- Don't mind slightly slower response times

**When to use Minimal**:
- Quick edits and code reviews
- Performance-critical scenarios
- Limited API key availability
- Secondary development environment

## Configuration Guide

### Step 1: Choose Your Profile

Select the profile that matches your tech stack from the list above.

### Step 2: Configure API Keys

Configure required API keys in your IDE's mcp.json file:

```json
{
  "mcpServers": {
    "nodejs-typescript": {
      "command": "/path/to/mcp-gateway/scripts/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "nodejs-typescript"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here",
        "SNYK_TOKEN": "your_snyk_token_here",
        "TAVILY_API_KEY": "tvly_your_key_here"
      }
    }
  }
}
```

See [IDE Setup Guide](IDE_SETUP_GUIDE.md) for IDE-specific examples.

### Step 3: Register the Profile

```bash
cd /path/to/mcp-gateway
make register
```

This will create/update the virtual server and print the connection URL.

### Step 4: Connect Your IDE

Use the URL printed by `make register` to connect your IDE to the stack profile.

## Troubleshooting

**Issue**: "Gateway not found" error
- **Solution**: Ensure all required gateways are registered in `config/gateways.txt`
- **Solution**: Run `make register` to register gateways

**Issue**: "Authentication failed" error
- **Solution**: Check that GATEWAY_JWT is set in .env (run `make jwt`)
- **Solution**: Verify API keys are correctly configured in IDE's mcp.json

**Issue**: "Tool limit exceeded" warning
- **Solution**: Switch to Minimal variant of your stack profile
- **Solution**: Use tool-router (all profiles already use it)

**Issue**: Slow response times
- **Solution**: Use Minimal variant for faster performance
- **Solution**: Reduce number of active tools in your profile

## Next Steps

- [IDE Setup Guide](IDE_SETUP_GUIDE.md) - Configure your IDE
- [Environment Configuration](ENVIRONMENT_CONFIGURATION.md) - Minimal .env approach
- [Tool Router Guide](TOOL_ROUTER_GUIDE.md) - How routing works
- [Monorepo vs Single-Repo](MONOREPO_VS_SINGLE_REPO.md) - Architecture decisions
