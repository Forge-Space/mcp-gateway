# Tool Router Guide

Understanding how the tool-router works and why it's essential for IDE compatibility.

## Table of Contents

- [Overview](#overview)
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Examples](#examples)

## Overview

The **tool-router** is a smart routing layer that solves IDE tool limits by exposing only 1-2 tools to your IDE while intelligently routing requests to dozens of upstream MCP servers.

**Key Benefits:**
- ✅ Works with any IDE (Cursor, VSCode, Windsurf, JetBrains)
- ✅ Bypasses IDE tool limits (~60 tools in Cursor)
- ✅ Single connection point for all MCP servers
- ✅ Intelligent tool selection based on task context
- ✅ Transparent to the user

## The Problem

### IDE Tool Limits

Most IDEs have limits on how many MCP tools they can handle:

```
Cursor: ~60 tools maximum
VSCode: Similar limits
Windsurf: Similar limits
JetBrains: Varies by IDE
```

### Without Tool-Router

```
IDE
├── GitHub MCP (15 tools)
├── Filesystem MCP (8 tools)
├── Snyk MCP (12 tools)
├── Tavily MCP (5 tools)
├── PostgreSQL MCP (10 tools)
├── MongoDB MCP (8 tools)
├── Playwright MCP (18 tools)
└── ... (76 tools total) ❌ EXCEEDS LIMIT
```

**Problems:**
- IDE becomes slow or unresponsive
- Tools may not load correctly
- Connection failures
- Poor user experience

## The Solution

### With Tool-Router

```
IDE
└── Tool-Router (2 tools)
    ├── execute_task → Routes to best upstream tool
    └── search_tools → Finds relevant tools

Tool-Router (behind the scenes)
├── GitHub MCP (15 tools)
├── Filesystem MCP (8 tools)
├── Snyk MCP (12 tools)
├── Tavily MCP (5 tools)
├── PostgreSQL MCP (10 tools)
├── MongoDB MCP (8 tools)
├── Playwright MCP (18 tools)
└── ... (76 tools available) ✅ ALL ACCESSIBLE
```

**Benefits:**
- IDE sees only 2 tools (well under limit)
- All 76 upstream tools remain accessible
- Fast IDE performance
- Seamless user experience

## How It Works

### 1. Task Submission

User requests a task through the IDE:

```
User: "Search GitHub for authentication issues"
IDE → Tool-Router: execute_task(task="search GitHub for authentication issues")
```

### 2. Tool Selection

Tool-router analyzes the task and selects the best upstream tool:

```python
# Scoring algorithm
task_tokens = ["search", "github", "authentication", "issues"]

# Score each available tool
github_search_issues: 0.95  # High match
github_list_repos: 0.45     # Medium match
tavily_search: 0.30         # Low match
filesystem_read: 0.05       # Very low match

# Select best match: github_search_issues
```

### 3. Tool Execution

Tool-router calls the selected upstream tool:

```
Tool-Router → GitHub MCP: search_issues(query="authentication")
GitHub MCP → Tool-Router: [results]
Tool-Router → IDE: [results]
```

### 4. User Sees Results

The IDE displays results as if it called the tool directly:

```
Found 15 issues matching "authentication":
1. Issue #123: Authentication fails on mobile
2. Issue #124: OAuth token refresh bug
...
```

## Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────┐
│                    IDE                          │
│  (Cursor, VSCode, Windsurf, JetBrains)         │
└────────────────┬────────────────────────────────┘
                 │ MCP Protocol
                 │ (2 tools visible)
┌────────────────▼────────────────────────────────┐
│              Tool-Router                        │
│  ┌──────────────────────────────────────────┐  │
│  │  execute_task(task, context)             │  │
│  │  - Analyzes task description             │  │
│  │  - Scores available tools                │  │
│  │  - Selects best match                    │  │
│  │  - Calls upstream tool                   │  │
│  │  - Returns results                       │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  search_tools(query)                     │  │
│  │  - Searches available tools              │  │
│  │  - Returns matching tools                │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │ Gateway API
                 │ (requires GATEWAY_JWT)
┌────────────────▼────────────────────────────────┐
│            MCP Gateway                          │
│  ┌──────────┬──────────┬──────────┬─────────┐  │
│  │ GitHub   │Filesystem│  Snyk    │ Tavily  │  │
│  │ (15)     │  (8)     │  (12)    │  (5)    │  │
│  └──────────┴──────────┴──────────┴─────────┘  │
│  ┌──────────┬──────────┬──────────┬─────────┐  │
│  │PostgreSQL│ MongoDB  │Playwright│ Memory  │  │
│  │  (10)    │  (8)     │  (18)    │  (6)    │  │
│  └──────────┴──────────┴──────────┴─────────┘  │
└─────────────────────────────────────────────────┘
```

### Component Details

**Tool-Router Components:**
1. **Task Analyzer**: Parses task description into tokens
2. **Scoring Engine**: Scores each available tool against task
3. **Tool Selector**: Picks highest-scoring tool
4. **Gateway Client**: Communicates with MCP Gateway
5. **Result Formatter**: Returns results to IDE

**Scoring Factors:**
- Tool name similarity (40% weight)
- Tool description match (40% weight)
- Gateway name match (20% weight)
- Synonym matching (e.g., "find" → "search")

## Configuration

### Prerequisites

1. **Gateway Running**: `make start`
2. **Gateway JWT**: `make jwt` (copy to .env as GATEWAY_JWT)
3. **Gateways Registered**: `make register`

### Stack Profile Configuration

All stack profiles automatically use tool-router:

```bash
# In config/virtual-servers.txt
nodejs-typescript|tool-router,github,filesystem,memory,git-mcp,snyk,tavily,Context7
```

The first gateway in the list (`tool-router`) is the entry point. All other gateways are accessible through it.

### IDE Configuration

Configure your IDE to connect to the tool-router:

```json
{
  "mcpServers": {
    "nodejs-typescript": {
      "command": "/path/to/cursor-mcp-wrapper.sh",
      "args": ["--server-name", "nodejs-typescript"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"
      }
    }
  }
}
```

The wrapper script automatically:
1. Generates fresh GATEWAY_JWT
2. Connects to tool-router virtual server
3. Routes all requests through tool-router

## Examples

### Example 1: GitHub Search

**User Request:**
```
"Find all open issues labeled 'bug' in my repository"
```

**Tool-Router Process:**
```
1. Parse task: ["find", "open", "issues", "labeled", "bug", "repository"]
2. Score tools:
   - github_search_issues: 0.92 ✓ SELECTED
   - github_list_repos: 0.35
   - tavily_search: 0.15
3. Call: github_search_issues(state="open", labels=["bug"])
4. Return: [list of issues]
```

### Example 2: File Operations

**User Request:**
```
"Read the package.json file and check dependencies"
```

**Tool-Router Process:**
```
1. Parse task: ["read", "package.json", "file", "check", "dependencies"]
2. Score tools:
   - filesystem_read_file: 0.88 ✓ SELECTED
   - github_get_file_contents: 0.45
   - memory_search: 0.10
3. Call: filesystem_read_file(path="package.json")
4. Return: [file contents]
```

### Example 3: Security Scan

**User Request:**
```
"Scan the project for security vulnerabilities"
```

**Tool-Router Process:**
```
1. Parse task: ["scan", "project", "security", "vulnerabilities"]
2. Score tools:
   - snyk_test: 0.95 ✓ SELECTED
   - github_list_issues: 0.25
   - filesystem_search: 0.15
3. Call: snyk_test(path=".")
4. Return: [vulnerability report]
```

### Example 4: Database Query

**User Request:**
```
"Query the users table in PostgreSQL"
```

**Tool-Router Process:**
```
1. Parse task: ["query", "users", "table", "postgresql"]
2. Score tools:
   - postgres_execute_query: 0.90 ✓ SELECTED
   - mongodb_find: 0.20
   - filesystem_search: 0.10
3. Call: postgres_execute_query(query="SELECT * FROM users")
4. Return: [query results]
```

## Advanced Features

### Context-Aware Routing

Tool-router considers previous context:

```
User: "Search for authentication code"
Router: Uses filesystem_search (code context)

User: "Now search for related issues"
Router: Uses github_search_issues (issue context)
```

### Fallback Mechanisms

If primary tool fails, router tries alternatives:

```
1. Try: github_search_issues → FAILS (rate limit)
2. Fallback: tavily_search → SUCCESS
3. Return: [search results from Tavily]
```

### Tool Discovery

Use `search_tools` to find available tools:

```
User: "What tools are available for testing?"
Router: search_tools(query="testing")
Returns:
- playwright_navigate
- playwright_click
- chrome_devtools_evaluate
- snyk_test
```

## Performance

### Response Times

**Without Tool-Router:**
- IDE loads 76 tools: ~5-10 seconds
- Tool selection: Instant (IDE handles)
- Execution: Varies by tool

**With Tool-Router:**
- IDE loads 2 tools: ~1 second ✓
- Tool selection: ~50-100ms
- Execution: Varies by tool

**Net Result:** Faster IDE startup, minimal routing overhead

### Caching

Tool-router caches:
- Available tools list (refreshed every 60s)
- Tool descriptions (refreshed on gateway restart)
- Scoring results (per session)

## Troubleshooting

### Issue: "Gateway JWT not set"

**Cause**: GATEWAY_JWT missing from .env

**Solution**:
```bash
make jwt
# Add to .env: GATEWAY_JWT=<token>
```

### Issue: "No tools available"

**Cause**: Gateways not registered

**Solution**:
```bash
make register
```

### Issue: "Wrong tool selected"

**Cause**: Task description unclear

**Solution**: Be more specific:
- ❌ "Search for stuff"
- ✓ "Search GitHub issues for authentication bugs"

### Issue: "Tool execution failed"

**Cause**: Upstream tool error or missing API key

**Solution**: Check upstream tool configuration (see [IDE Setup Guide](IDE_SETUP_GUIDE.md))

## Best Practices

### 1. Clear Task Descriptions

**Good:**
- "Search GitHub for open issues labeled 'bug'"
- "Read the package.json file"
- "Run security scan with Snyk"

**Bad:**
- "Do something"
- "Check stuff"
- "Fix it"

### 2. Provide Context

Include relevant context in your request:
- File names
- Repository names
- Specific tools to use
- Expected output format

### 3. Verify Tool Selection

If router selects wrong tool, rephrase your request:
- Add more specific keywords
- Mention the tool name explicitly
- Provide examples of expected behavior

### 4. Monitor Performance

Check tool-router logs for:
- Slow tool selection (>500ms)
- Frequent fallbacks
- High error rates

## Next Steps

- [MCP Stack Configurations](MCP_STACK_CONFIGURATIONS.md) - Choose your stack
- [IDE Setup Guide](IDE_SETUP_GUIDE.md) - Configure your IDE
- [Environment Configuration](ENVIRONMENT_CONFIGURATION.md) - Minimal .env approach
