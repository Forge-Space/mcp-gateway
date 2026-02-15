# CodeRabbit Configuration Guide

**Version:** 1.0.0
**Last Updated:** 2026-02-14
**Audience:** Contributors, Maintainers, AI Agents

---

## Overview

This document explains the CodeRabbit configuration for the MCP Gateway project and provides manual review guidelines for patterns that cannot be automated through the configuration file.

### Purpose

CodeRabbit is configured to enforce:

- **Cost Constraint Compliance** - No paid APIs or commercial services
- **Quality Gates** - 100% test coverage, zero lint errors
- **Security Standards** - No hardcoded secrets, proper authentication
- **Performance Targets** - <100ms cached operations, <500ms uncached
- **Documentation Requirements** - Type hints, docstrings, CHANGELOG updates

---

## Configuration File

**Location:** `@/.coderabbit.yaml`

### Key Settings

#### 1. Review Profile

```yaml
profile: "assertive"
request_changes_workflow: true
```

- **Assertive mode** enforces strict quality gates
- **Request changes** blocks PR merge until issues resolved

#### 2. Auto-Review

```yaml
auto_review:
  enabled: true
  drafts: false
  base_branches:
    - main
    - develop
```

- Automatically reviews PRs to `main` and `develop`
- Skips draft PRs (manual review only)

#### 3. Enabled Tools

- **shellcheck** - Shell script linting
- **ruff** - Python linting (primary language)
- **markdownlint** - Documentation quality
- **yamllint** - Configuration validation
- **hadolint** - Docker best practices
- **gitleaks** - Secret detection
- **trufflehog** - Additional secret scanning
- **actionlint** - GitHub Actions validation

---

## Path-Based Instructions

### Python - Tool Router (`tool_router/**/*.py`)

**Critical Requirements:**

- ✅ Type hints required (strict mypy compliance)
- ✅ Google-style docstrings with Args, Returns, Raises
- ✅ 100% test coverage for new code
- ✅ Thread-safe implementations (check locks, race conditions)
- ✅ No external paid APIs (cost constraint)
- ✅ Prefer stdlib over dependencies
- ✅ Error handling with descriptive messages
- ✅ Performance: <100ms for cached operations

**Example:**

```python
def select_top_matching_tools(
    tools: list[dict[str, Any]],
    task: str,
    context: str,
    top_n: int = 1
) -> list[dict[str, Any]]:
    """Select the most relevant tools for a given task.

    Args:
        tools: List of available tool definitions
        task: Natural language task description
        context: Additional context to help selection
        top_n: Maximum number of tools to return

    Returns:
        List of top N matching tools, sorted by relevance

    Raises:
        ValueError: If tools list is empty or invalid
    """
```

### Python - Tests (`tool_router/tests/**/*.py`)

**Test Quality Requirements:**

- ✅ Use pytest fixtures for reusability
- ✅ Parametrize tests for edge cases
- ✅ Mock external dependencies (gateway, network)
- ✅ Test both success and failure paths
- ✅ Integration tests for end-to-end flows
- ✅ Performance tests for latency-critical paths
- ✅ 100% coverage for testable code

**Example:**

```python
@pytest.fixture
def sample_tools() -> list[dict]:
    """Sample tools for testing."""
    return [
        {
            "name": "web_search",
            "description": "Search the web",
            "inputSchema": {"properties": {"query": {"type": "string"}}}
        }
    ]

@pytest.mark.parametrize("task,expected_tool", [
    ("search for Python docs", "web_search"),
    ("calculate 2+2", "calculate"),
])
def test_tool_selection(sample_tools, task, expected_tool):
    """Test tool selection for various tasks."""
    result = select_top_matching_tools(sample_tools, task, "", top_n=1)
    assert result[0]["name"] == expected_tool
```

### Shell Scripts (`scripts/**/*.sh`)

**Requirements:**

- ✅ Shellcheck compliance (no warnings)
- ✅ Proper error handling (`set -euo pipefail`)
- ✅ POSIX compatibility where possible
- ✅ Descriptive error messages
- ✅ No hardcoded secrets
- ✅ Use `lib/` functions for reusability

**Example:**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Source error handling library
source "$(dirname "$0")/../lib/errors.sh"

register_gateway() {
    local gateway_url="${1:-}"

    if [[ -z "$gateway_url" ]]; then
        error "Gateway URL is required"
        return 1
    fi

    info "Registering gateway: $gateway_url"
    # Implementation...
}
```

### Docker (`**/Dockerfile*`)

**Security & Efficiency:**

- ✅ Multi-stage builds for smaller images
- ✅ Non-root user execution
- ✅ Minimal base images (alpine preferred)
- ✅ No secrets in layers
- ✅ Proper HEALTHCHECK directives
- ✅ Layer caching optimization

**Example:**

```dockerfile
# Multi-stage build
FROM python:3.11-alpine AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-alpine
# Non-root user
RUN adduser -D appuser
USER appuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:8000/health', timeout=3)"
CMD ["python", "-m", "tool_router"]
```

### Documentation (`docs/**/*.md`)

**Standards:**

- ✅ Clear, concise, with examples
- ✅ Cross-link related docs
- ✅ Keep CHANGELOG.md updated
- ✅ Verify technical accuracy
- ✅ Include troubleshooting sections
- ✅ AI-agent friendly structure

---

## Manual Review Patterns

These patterns cannot be automated in the CodeRabbit schema but should be enforced during manual reviews:

### 1. Cost Constraint Violations

**Pattern:** `(openai|anthropic|google\.ai|aws|gcp|azure)`

**Check for:**

- Paid API references (OpenAI, Anthropic, Google AI)
- Managed cloud services (AWS, GCP, Azure)
- Commercial dependencies

**Action:** ❌ **REJECT** - All features must be costless (self-hosted, open-source)

**Example Violations:**

```python
# ❌ BAD - Paid API
import openai
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ GOOD - Self-hosted alternative
from tool_router.gateway.client import HTTPGatewayClient
client = HTTPGatewayClient(config)
```

### 2. Missing Type Hints

**Pattern:** `def \w+\([^)]*\)\s*:`

**Check for:**

- Functions without parameter type hints
- Functions without return type annotations
- Use of `Any` instead of specific types

**Action:** ⚠️ **REQUEST CHANGES** - Add type hints

**Example:**

```python
# ❌ BAD - No type hints
def process_data(data):
    return data.upper()

# ✅ GOOD - Full type hints
def process_data(data: str) -> str:
    return data.upper()
```

### 3. Hardcoded Secrets

**Pattern:** `(password|secret|key|token)\s*=\s*['"][^'"]+['"]`

**Check for:**

- Hardcoded passwords, API keys, tokens
- Secrets in configuration files
- Credentials in code

**Action:** ❌ **BLOCK** - Use environment variables

**Example:**

```python
# ❌ BAD - Hardcoded secret
JWT_SECRET = "my-super-secret-key-12345"

# ✅ GOOD - Environment variable
JWT_SECRET = os.getenv("GATEWAY_JWT")
if not JWT_SECRET:
    raise ValueError("GATEWAY_JWT environment variable is required")
```

### 4. Missing Docstrings

**Pattern:** `^\s*(def|class)\s+\w+`

**Check for:**

- Public functions without docstrings
- Classes without docstrings
- Complex logic without explanation

**Action:** ⚠️ **REQUEST CHANGES** - Add docstrings

**Example:**

```python
# ❌ BAD - No docstring
class MetricsCollector:
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples

# ✅ GOOD - Complete docstring
class MetricsCollector:
    """Thread-safe metrics collector for performance monitoring.

    Collects timing metrics and counters with bounded memory usage.
    Uses locks for thread safety and FIFO eviction for memory bounds.

    Args:
        max_samples: Maximum samples per metric (default: 1000)
        max_metric_names: Maximum unique metric names (default: 100)
    """
    def __init__(self, max_samples: int = 1000, max_metric_names: int = 100):
        self.max_samples = max_samples
        self.max_metric_names = max_metric_names
```

---

## Quality Gates Checklist

Before approving any PR, verify:

### Code Quality

- [ ] All tests passing (100% for new code)
- [ ] Zero ruff/mypy errors
- [ ] Shellcheck compliance for scripts
- [ ] Type hints on all functions
- [ ] Docstrings on public APIs

### Security

- [ ] No hardcoded secrets
- [ ] No gitleaks/trufflehog violations
- [ ] Input validation present
- [ ] JWT authentication maintained

### Performance

- [ ] No performance regressions
- [ ] Caching used where appropriate
- [ ] Thread-safe implementations
- [ ] Metrics collection added

### Documentation

- [ ] CHANGELOG.md updated
- [ ] README.md updated if needed
- [ ] Code comments for complex logic
- [ ] Examples provided

### Cost Constraint

- [ ] No paid APIs introduced
- [ ] No commercial dependencies
- [ ] Self-hosted deployment maintained
- [ ] Stdlib-first approach followed

---

## Performance Targets

### Tool Router

- **Tool Selection:** <100ms (cached), <500ms (uncached)
- **Gateway Latency:** <50ms overhead per request
- **Startup Time:** <5s tool router ready

### Testing

- **Test Execution:** <30s full suite
- **Coverage:** 100% for testable code
- **Build Time:** <30s full build

### Quality

- **Zero Regressions:** All tests pass on main
- **Lint Clean:** No ruff/mypy errors
- **Documentation:** Every feature documented before release

---

## Conventional Commits

All commits must follow Angular conventional commits format:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style (formatting, no logic change)
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `test` - Test additions/changes
- `chore` - Build/tooling changes
- `ci` - CI/CD changes

### Examples

```text
feat(router): add caching for tool metadata

Implement in-memory cache with 5-minute TTL to reduce
gateway API calls and improve response times.

Closes #123

---

fix(client): handle network timeout gracefully

Add exponential backoff retry logic for transient
network failures. Prevents cascading failures.

---

docs(ops): add monitoring guide

Document Prometheus metrics, Grafana dashboards,
and health check endpoints for production ops.
```

### Rules

- ❌ **No AI attribution** in commits (mandatory)
- ✅ Subject: imperative mood, lowercase start, max 50 chars
- ✅ Body: what and why (not how), max 72 chars per line
- ✅ Footer: issues, breaking changes

---

## Integration with Development Workflow

### 1. Before Creating PR

```bash
# Run quality checks locally
make lint          # Ruff + mypy
make test          # All tests
make coverage      # Coverage report

# Verify no secrets
git diff | grep -i "password\|secret\|key\|token"
```

### 2. PR Creation

- CodeRabbit auto-reviews within minutes
- Address all comments before requesting human review
- Update CHANGELOG.md with changes
- Ensure all CI checks pass

### 3. PR Review

- Human reviewer checks manual patterns
- Verify cost constraint compliance
- Check performance implications
- Approve only if all gates pass

### 4. Merge

- Squash commits for clean history
- Ensure conventional commit format
- Update version if needed
- Tag releases appropriately

---

## Troubleshooting

### CodeRabbit Not Reviewing

**Check:**

1. PR targets `main` or `develop` branch
2. PR is not in draft mode
3. GitHub App permissions are correct
4. `.coderabbit.yaml` is valid YAML

**Fix:**

```bash
# Validate YAML syntax
yamllint .coderabbit.yaml

# Check GitHub App installation
# Go to: Settings → Integrations → CodeRabbit
```

### False Positives

**If CodeRabbit flags valid code:**

1. Add comment explaining why it's correct
2. Request human review override
3. Update path_instructions if pattern is common

### Missing Reviews

**If CodeRabbit misses an issue:**

1. Report in PR comments
2. Add to manual review checklist
3. Consider updating configuration

---

## References

- **CodeRabbit Docs:** <https://docs.coderabbit.ai/>
- **Project PLAN:** `@/PLAN.md`
- **Architecture:** `@/docs/architecture/OVERVIEW.md`
- **Tool Router Guide:** `@/docs/architecture/TOOL_ROUTER_GUIDE.md`
- **CHANGELOG:** `@/CHANGELOG.md`

---

## Maintenance

### Updating Configuration

When updating `.coderabbit.yaml`:

1. Test changes in a feature branch PR
2. Verify all tools still work
3. Update this guide if instructions change
4. Get team approval before merging

### Adding New Tools

To add a new linting tool:

1. Add to `reviews.tools` section
2. Document in this guide
3. Update CI/CD to run tool
4. Add to pre-commit hooks if applicable

---

**Remember:** Every feature must be costless. If it requires money, find another way or skip it.
