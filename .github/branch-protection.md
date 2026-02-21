# Forge Space GitHub Branch Protection Configuration
# This file documents the branch protection rules for Forge Space projects
# Apply these settings via GitHub UI or GitHub API

## Branch Protection Rules

### Main Branch (Production)
- Target: main (and master for legacy compatibility)
- Purpose: Production-ready code, always deployable
- Rules:
  - Require pull request reviews before merging
  - Require status checks to pass before merging (CI pipeline)
  - Require conversation resolution before merging
  - Require up-to-date branch before merging
  - Do not allow force pushes
  - Do not allow deletions
  - Limit number of approvals: 2 (at least one senior reviewer)
  - Require review from Code Owners

### Release Branches
- Target: release/* (e.g., release/1.0.0, release/2.1.0)
- Purpose: Release preparation branches
- Rules:
  - Require pull request reviews before merging
  - Require status checks to pass before merging
  - Require conversation resolution before merging
  - Require up-to-date branch before merging
  - Allow force pushes (for automated releases)
  - Do not allow deletions
  - Limit number of approvals: 2 (at least one senior reviewer)
  - Require review from Code Owners

### Development Branch
- Target: dev
- Purpose: Development environment branch, continuously deployed
- Rules:
  - Require status checks to pass before merging
  - Allow force pushes (for hotfixes)
  - Do not allow deletions
  - No pull request required (direct pushes allowed)
  - No conversation resolution required

### Feature Branches
- Target: feature/* (e.g., feature/new-tool, feature/bug-fix)
- Purpose: Feature development branches
- Rules:
  - Require pull request reviews before merging
  - Require status checks to pass before merging
  - Allow force pushes (for development convenience)
  - Allow deletions (cleanup after merge)
  - No conversation resolution required
  - No up-to-date branch requirement

### Hotfix Branches
- Target: hotfix/* (e.g., hotfix/security-patch)
- Purpose: Critical fixes for production issues
- Rules:
  - Require pull request reviews before merging
  - Require status checks to pass before merging
  - Require conversation resolution before merging
  - Limit number of approvals: 2 (at least one senior reviewer)
  - Allow force pushes (for quick fixes)
  - Do not allow deletions

## Status Checks Required

### Required for All Branches
- CI Pipeline: All CI checks must pass
- Security Scan: CodeQL and Snyk scans must pass
- Code Coverage: Minimum 80% coverage maintained
- Build Verification: Docker build must succeed
- Lint Checks: All linting must pass

### Additional for Main/Release Branches
- Integration Tests: Full test suite must pass
- Performance Tests: Performance benchmarks must meet targets
- Security Review: Security team approval for sensitive changes
- Documentation Review: Documentation must be updated

## Implementation Steps

### 1. GitHub UI Setup
1. Go to repository Settings → Branches
2. Add branch protection rules for each branch pattern
3. Configure required status checks
4. Set up required reviewers
5. Configure merge options

### 2. GitHub API Setup
```bash
# Using GitHub CLI
gh repo edit LucasSantana-Dev/mcp-gateway --enable-merge-commits
gh api repos/LucasSantana-Dev/mcp-gateway/branches/main/protection
```

### 3. CODEOWNERS File
Create `.github/CODEOWNERS`:
```
# Code Owners Configuration

# Core Maintainers
* @LucasSantana-Dev

# Security Team
*.yml @security-team
Dockerfile* @security-team

# Documentation
docs/** @docs-team
README.md @docs-team

# Infrastructure
.github/** @devops-team
Dockerfile* @devops-team
docker-compose.yml @devops-team

# Core Application
src/** @core-team
tool_router/** @core-team
apps/** @core-team

# Configuration
config/** @core-team
scripts/** @core-team
```

---

Last Updated: 2025-01-19
Version: 1.0.0
Maintainer: Forge Space DevOps Team
Review Required: Yes
