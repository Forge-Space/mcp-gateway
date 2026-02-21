# CodeRabbit Setup Guide

This guide covers setting up CodeRabbit for IDE, GitHub, and terminal usage in the forge-mcp-gateway project.

## Overview

CodeRabbit provides AI-powered code reviews across multiple platforms:

- **GitHub Integration**: Automated PR reviews
- **IDE Extension**: Real-time code feedback in your editor
- **CLI**: Terminal-based code reviews

## Configuration

The project uses `.coderabbit.yaml` for centralized configuration that works across all platforms.

**Key settings:**

- **Profile**: `assertive` - Strict reviews focusing on quality
- **Request changes workflow**: Enabled - Blocks PR merges until issues resolved
- **Enabled tools**: shellcheck, ruff, markdownlint, yamllint, hadolint, gitleaks, trufflehog, actionlint
- **Pre-merge checks**: Enforces conventional commit format in PR titles

## GitHub Integration

### Installation

1. Visit [CodeRabbit GitHub Marketplace](https://github.com/marketplace/coderabbitai)
2. Click "Install" or "Configure"
3. Select repositories (grant access to `forge-mcp-gateway`)
4. CodeRabbit will automatically review new PRs

### Usage

**Automatic reviews:**

- CodeRabbit reviews all PRs automatically on base branches: `main`, `master`, `develop`
- Reviews appear as PR comments with line-by-line feedback
- Draft PRs are not auto-reviewed (configurable)

**Manual commands in PR comments:**

```text
@coderabbitai summary
@coderabbitai review
@coderabbitai configuration
@coderabbitai help
```

**Review workflow:**

1. Create PR
2. CodeRabbit posts review within minutes
3. Address feedback
4. Request re-review: `@coderabbitai review`
5. Merge when approved

## IDE Extension

### IDE Installation

**VS Code / Cursor / Windsurf:**

1. Open Extensions marketplace
2. Search "CodeRabbit"
3. Install "CodeRabbit" extension
4. Authenticate with GitHub account

**JetBrains IDEs:**

1. Go to Settings → Plugins
2. Search "CodeRabbit"
3. Install and restart IDE
4. Authenticate when prompted

### IDE Usage

**Features:**

- Real-time code suggestions as you type
- Inline code reviews on-demand
- Chat interface for code questions
- Context-aware feedback using project configuration

**Commands:**

- Right-click code → "CodeRabbit: Review Selection"
- Command palette → "CodeRabbit: Review File"
- Chat panel → Ask questions about code

## CLI (Terminal)

### CLI Installation

**macOS / Linux:**
```bash
curl -fsSL https://cli.coderabbit.ai/install.sh | sh
```

**Manual installation:**
```bash
# Download binary for your platform
# Add to PATH
export PATH="$HOME/.coderabbit/bin:$PATH"
```

**Verify installation:**

```bash
coderabbit --version
```

### CLI Authentication

First-time setup:

```bash
coderabbit auth login
```

This opens a browser for GitHub authentication. The CLI stores credentials locally.

### CLI Usage

**Review uncommitted changes:**

```bash
coderabbit review
```

**Review specific files:**

```bash
coderabbit review scripts/start.sh tool_router/gateway_client.py
```

**Review with plain output (for piping):**

```bash
coderabbit review --plain
```

**Review with custom prompt:**

```bash
coderabbit review --prompt "Focus on security issues"
```

**Interactive mode:**

```bash
coderabbit review --interactive
```

**Common workflows:**

```bash
# Quick review before commit
coderabbit review

# Review specific changes
git diff | coderabbit review --stdin

# Review and save to file
coderabbit review --plain > review.txt

# Review with focus area
coderabbit review --prompt "Check for shell script best practices"
```

### CLI Options

```text
coderabbit review [options] [files...]

Options:
  --plain              Plain text output (no interactive UI)
  --interactive        Interactive review mode
  --prompt <text>      Custom review instructions
  --stdin              Read diff from stdin
  --help               Show help
```

## Configuration Customization

### Modify Review Behavior

Edit `.coderabbit.yaml`:

```yaml
reviews:
  profile: "chill"  # Change to "chill" for less strict reviews
  poem: true        # Enable fun poems in reviews
```

### Add Custom Path Instructions

```yaml
reviews:
  path_instructions:
    - path: "scripts/**/*.sh"
      instructions: "Focus on error handling and logging"
```

### Enable/Disable Tools

```yaml
reviews:
  tools:
    shellcheck:
      enabled: false  # Disable specific tool
```

### Adjust Pre-merge Checks

```yaml
reviews:
  pre_merge_checks:
    title:
      status: "warning"  # Change from "error" to "warning"
```

## Best Practices

1. **Review before commit**: Use CLI to catch issues early
2. **Address feedback promptly**: Don't let review comments pile up
3. **Use custom prompts**: Guide reviews for specific concerns
4. **Leverage path instructions**: Tailor reviews per file type
5. **Keep configuration updated**: Adjust as project evolves

## Troubleshooting

### CLI not found after installation

```bash
# Add to shell profile (~/.bashrc, ~/.zshrc, etc.)
export PATH="$HOME/.coderabbit/bin:$PATH"
source ~/.zshrc  # or ~/.bashrc
```

### Authentication issues

```bash
# Re-authenticate
coderabbit auth logout
coderabbit auth login
```

### GitHub integration not working

- Verify CodeRabbit app has repository access
- Check `.coderabbit.yaml` syntax (use schema validation)
- Ensure PR targets configured base branches

### IDE extension not responding

- Restart IDE
- Check extension logs
- Re-authenticate if needed

## Resources

- **Official Documentation**: <https://docs.coderabbit.ai/>
- **CLI Documentation**: <https://www.coderabbit.ai/cli>
- **Configuration Reference**: <https://docs.coderabbit.ai/reference/configuration>
- **GitHub Marketplace**: <https://github.com/marketplace/coderabbitai>
- **Example Configs**: <https://github.com/coderabbitai/awesome-coderabbit/tree/main/configs>

## Support

- **Discord**: <https://discord.gg/GsXnASn26c>
- **GitHub Issues**: Report bugs via CodeRabbit's support channels
- **Documentation**: Check docs for detailed guides and troubleshooting
