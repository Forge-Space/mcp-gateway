# Renovate Setup Guide

This guide will help you enable Renovate for automated dependency updates in the forge-mcp-gateway repository.

## What is Renovate?

Renovate is a bot that automatically creates pull requests to update your dependencies. It's already configured in this repository (`.github/renovate.json`), but needs to be enabled.

## Setup Steps

### Option 1: Enable via GitHub App (Recommended)

1. **Install Renovate GitHub App**
   - Visit: https://github.com/apps/renovate
   - Click "Install" or "Configure"
   - Select "LucasSantana-Dev" account
   - Choose "Only select repositories"
   - Select `forge-mcp-gateway`
   - Click "Install" or "Save"

2. **Verify Installation**
   - Renovate will automatically scan your repository
   - Within a few minutes, it should create an "Configure Renovate" onboarding PR
   - Review and merge the onboarding PR

3. **First Dependency Updates**
   - After merging the onboarding PR, Renovate will create dependency update PRs
   - Based on current scan, expect PRs for:
     - `@types/node`: 22.19.11 → 25.2.3
     - `rimraf`: 5.0.10 → 6.1.2
     - Python dependencies (if tracked in requirements.txt)

### Option 2: Self-Hosted Renovate (Advanced)

If you prefer to run Renovate yourself:

```bash
# Install Renovate CLI
npm install -g renovate

# Set GitHub token
export GITHUB_TOKEN="your_github_token"

# Run Renovate
renovate --platform=github --token=$GITHUB_TOKEN LucasSantana-Dev/forge-mcp-gateway
```

## Current Configuration

The repository is configured with:

- **Schedule**: Mondays before 3am UTC
- **Auto-merge**: Enabled for patch/minor updates (after 3-day stabilization)
- **Manual review**: Required for major updates
- **Security**: Immediate auto-merge for security patches
- **Grouping**: Dependencies grouped by type (Python, GitHub Actions, etc.)

## Expected Dependency Updates

Based on current scan:

### NPM Dependencies
- `@types/node`: 22.19.11 → **25.2.3** (major - manual review)
- `rimraf`: 5.0.10 → **6.1.2** (major - manual review)

### Python Dependencies
Multiple updates available (will be grouped in PRs)

## Troubleshooting

### Renovate Not Creating PRs

1. **Check if app is installed**: Visit https://github.com/apps/renovate
2. **Check repository access**: Ensure Renovate has access to `forge-mcp-gateway`
3. **Check logs**: Visit Renovate dashboard for error logs
4. **Manual trigger**: Create an empty commit to trigger Renovate

### Force Renovate to Run Now

Create an empty commit to trigger Renovate:

```bash
git commit --allow-empty -m "chore: trigger renovate scan"
git push origin main
```

## Managing Dependency Updates

### Auto-Merge Criteria

PRs will auto-merge if:
- Update type is patch or minor
- 3 days have passed since release
- All CI checks pass
- No breaking changes detected

### Manual Review Required

PRs require manual review if:
- Update type is major
- Breaking changes detected
- Security vulnerability with major version bump
- Context Forge gateway updates

## References

- [Renovate Documentation](https://docs.renovatebot.com/)
- [Configuration Options](https://docs.renovatebot.com/configuration-options/)
- [Repository Config](.github/renovate.json)
