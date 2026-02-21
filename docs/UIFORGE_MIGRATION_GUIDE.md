# 🚀 UIForge Projects Migration Guide

## 📋 Overview

This guide provides step-by-step instructions for migrating existing UIForge projects to use the centralized shared package structure from the MCP Gateway project.

**Target Projects:**
- `uiforge-webapp` (Next.js web application)
- `uiforge-mcp` (Node.js MCP server)

**Migration Benefits:**
- 40% reduction in duplicate configurations
- Standardized CI/CD pipelines
- Unified security scanning
- Consistent templates and workflows
- Reduced maintenance overhead

## 🎯 Migration Strategy

### Phase 1: Preparation (Day 1)
1. **Backup Current Configurations**
2. **Analyze Project Structure**
3. **Identify Customizations**

### Phase 2: Migration (Day 2-3)
1. **Copy Shared Package**
2. **Adapt Project-Specific Configurations**
3. **Update Workflows**
4. **Test Integration**

### Phase 3: Validation (Day 4)
1. **Run CI/CD Pipeline**
2. **Validate All Scripts**
3. **Test Documentation**
4. **Team Training**

## 📁 Step-by-Step Migration

### 1. Backup Current Configurations

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)-migration

# Backup GitHub configurations
cp -r .github/ backups/$(date +%Y%m%d)-migration/github-backup/

# Backup scripts if they exist
cp -r scripts/ backups/$(date +%Y%m%d)-migration/scripts-backup/ 2>/dev/null || true

# Backup root configurations
cp renovate*.yml renovate*.json5 backups/$(date +%Y%m%d)-migration/ 2>/dev/null || true
```

### 2. Copy Shared Package

```bash
# From forge-mcp-gateway project, copy shared package
rsync -av --progress \
  /path/to/forge-mcp-gateway/.github/shared/ \
  /path/to/target-project/.github/shared/

# Ensure correct permissions
chmod -R 755 .github/shared/
find .github/shared/ -name "*.sh" -exec chmod +x {} \;
```

### 3. Analyze Current Project Structure

```bash
# Identify existing GitHub configurations
find .github -name "*.yml" -o -name "*.yaml" | sort

# Identify existing templates
find .github -name "*.md" | grep -E "(template|issue|pr)" | sort

# Identify existing scripts
find scripts/ -name "*.sh" 2>/dev/null | sort

# Identify root configurations
ls -la | grep -E "(renovate|codecov|codeql)" 2>/dev/null || true
```

### 4. Remove Duplicates (Careful!)

```bash
# ⚠️ WARNING: Review each file before removal!

# Remove duplicate Renovate configs (keep one authoritative version)
# List them first:
find . -name "renovate*" -type f

# Remove duplicates (example - adjust based on your findings):
# rm .github/renovate.yml
# rm .github/workflows/renovate.yml
# rm renovate.json

# Remove duplicate base CI workflows
# List them first:
find .github/workflows -name "*base-ci*" -o -name "*ci-base*"

# Remove duplicates (example):
# rm .github/workflows/base-ci.yml

# Remove duplicate branch protection configs
# List them first:
find . -name "branch-protection*" -type f

# Remove duplicates (example):
# rm .github/configs/branch-protection.yml
```

### 5. Create Project-Specific Adaptations

#### 5.1 Adapt CI Workflow

Edit `.github/workflows/ci.yml`:

```yaml
# Replace existing content with:
name: CI Pipeline

on:
  push:
    branches: [main, master, dev, release/*, feature/*]
  pull_request:
    branches: [main, master, dev, release/*]

env:
  NODE_VERSION: "22"  # Adjust if different
  PYTHON_VERSION: "3.12"  # Adjust if needed
  COVERAGE_THRESHOLD: "80"
  CACHE_VERSION: "v1"

jobs:
  ci:
    name: Base CI Pipeline
    uses: ./.github/shared/workflows/base-ci.yml
    with:
      project-type: 'webapp'  # or 'mcp-server' or 'gateway'
      node-version: ${{ env.NODE_VERSION }}
      python-version: ${{ env.PYTHON_VERSION }}
      enable-docker: true
      enable-security: true
      enable-coverage: true
      coverage-threshold: ${{ env.COVERAGE_THRESHOLD }}
      test-parallel: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
      SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### 5.2 Adapt Renovate Configuration

Edit `.github/renovate.yml` (create symlink):

```bash
# Remove existing renovate configs
rm -f .github/renovate.yml renovate.json renovate.json5

# Create symlink to shared config
ln -s .github/shared/configs/renovate.json5 .github/renovate.yml
```

#### 5.3 Adapt Branch Protection

```bash
# Remove existing branch protection
rm -f .github/branch-protection.yml

# Create symlink to shared config
ln -s .github/shared/configs/branch-protection.yml .github/branch-protection.yml
```

#### 5.4 Adapt PR Template

```bash
# Remove existing PR template
rm -f .github/PULL_REQUEST_TEMPLATE.md

# Create symlink to shared template
ln -s .github/shared/templates/pr-template-master.md .github/PULL_REQUEST_TEMPLATE.md
```

### 6. Update Project-Specific Settings

#### 6.1 Project Type Configuration

Edit `.github/shared/configs/renovate.json5` to add project-specific rules:

```json5
{
  // ... existing config ...
  "packageRules": [
    // ... existing rules ...
    {
      "matchPackagePatterns": ["*"],
      "matchPaths": ["packages/webapp/**"],
      "groupName": "webapp dependencies",
      "groupSlug": "webapp"
    },
    {
      "matchPackagePatterns": ["*"],
      "matchPaths": ["packages/api/**"],
      "groupName": "api dependencies",
      "groupSlug": "api"
    }
  ]
}
```

#### 6.2 CI/CD Customization

Edit `.github/workflows/ci.yml` to add project-specific jobs:

```yaml
# Add after the main ci job
  webapp-specific-tests:
    name: Webapp E2E Tests
    runs-on: ubuntu-latest
    needs: ci
    if: github.event_name == 'pull_request'

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Node.js
        uses: actions/setup-node@v6
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run E2E tests
        run: npm run test:e2e
```

### 7. Run Setup Script

```bash
# Make setup script executable
chmod +x scripts/setup-shared-symlinks.sh

# Run setup script
./scripts/setup-shared-symlinks.sh
```

### 8. Validate Migration

#### 8.1 Check Symlinks

```bash
# Verify all symlinks are created
echo "🔍 Checking symlinks..."
ls -la .github/renovate.yml
ls -la .github/branch-protection.yml
ls -la .github/PULL_REQUEST_TEMPLATE.md
ls -la scripts/mcp-wrapper.sh 2>/dev/null || echo "MCP wrapper not needed for this project"
```

#### 8.2 Validate Workflows

```bash
# Check workflow syntax
echo "🔍 Validating workflows..."
for workflow in .github/workflows/*.yml; do
  echo "Checking $workflow..."
  python3 -c "import yaml; yaml.safe_load(open('$workflow'))"
  echo "✅ $workflow is valid"
done
```

#### 8.3 Test CI Pipeline Locally

```bash
# Use act to test GitHub Actions locally (if installed)
act -j ci  # Test main CI job

# Or use GitHub CLI to trigger workflow
gh workflow run "CI Pipeline"
```

## 🎯 Project-Specific Adaptations

### For uiforge-webapp (Next.js)

#### Additional CI Jobs
```yaml
  nextjs-build:
    name: Next.js Build Test
    runs-on: ubuntu-latest
    needs: ci

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Node.js
        uses: actions/setup-node@v6
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Export static files (if applicable)
        run: npm run export || true
```

#### Environment-Specific Configuration
```yaml
env:
  NODE_VERSION: "22"
  NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}
  NEXT_PUBLIC_ENVIRONMENT: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
```

### For uiforge-mcp (Node.js MCP Server)

#### Additional CI Jobs
```yaml
  mcp-server-tests:
    name: MCP Server Tests
    runs-on: ubuntu-latest
    needs: ci

    services:
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Node.js
        uses: actions/setup-node@v6
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run MCP server tests
        run: npm run test:mcp
        env:
          REDIS_URL: redis://localhost:6379
```

## 🚨 Troubleshooting

### Common Issues

#### Symlink Problems
```bash
# Issue: Broken symlinks
# Solution: Recreate symlinks
./scripts/setup-shared-symlinks.sh

# Issue: Permission denied
# Solution: Fix permissions
chmod -R 755 .github/shared/
```

#### Workflow Validation Errors
```bash
# Issue: YAML syntax errors
# Solution: Validate with Python
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

# Issue: Missing shared workflows
# Solution: Check file exists
ls -la .github/shared/workflows/base-ci.yml
```

#### CI Pipeline Failures
```bash
# Issue: Shared workflow not found
# Solution: Check path in workflow
grep "uses.*shared" .github/workflows/ci.yml

# Issue: Missing secrets
# Solution: Add required secrets to GitHub repository
gh secret set CODECOV_TOKEN
gh secret set SNYK_TOKEN
```

### Validation Checklist

- [ ] All symlinks created and working
- [ ] Workflow YAML syntax valid
- [ ] CI pipeline runs successfully
- [ ] Security scanning executes
- [ ] Coverage reporting works
- [ ] All scripts executable
- [ ] Documentation updated
- [ ] Team trained on new structure

## 📚 Post-Migration Tasks

### 1. Update Documentation
- Update README.md with shared package information
- Modify setup guides to reference new structure
- Update developer onboarding documentation

### 2. Team Communication
- Announce migration completion
- Provide training on new structure
- Document any project-specific customizations

### 3. Maintenance Setup
- Schedule regular shared package updates
- Establish review process for changes
- Set up monitoring for CI/CD performance

### 4. Continuous Improvement
- Collect feedback from team
- Monitor CI/CD performance metrics
- Plan future enhancements to shared package

## 🔄 Rollback Plan

If migration fails, rollback steps:

```bash
# Restore from backup
cp -r backups/$(date +%Y%m%d)-migration/github-backup/. .github/
cp -r backups/$(date +%Y%m%d)-migration/scripts-backup/. scripts/ 2>/dev/null || true

# Remove shared package
rm -rf .github/shared

# Test restored configuration
git status
git add .
git commit -m "Rollback migration - restore original configuration"
```

## 📞 Support

### Resources
- **Shared Package Documentation**: `.github/shared/README.md`
- **MCP Gateway Example**: Reference implementation in forge-mcp-gateway project
- **GitHub Actions Documentation**: https://docs.github.com/en/actions

### Getting Help
1. Check this migration guide
2. Review shared package documentation
3. Reference MCP Gateway implementation
4. Create issue in shared package repository

---

**Migration Success Criteria:**
- ✅ CI/CD pipeline runs successfully
- ✅ All security scans execute
- ✅ Coverage reporting works
- ✅ Team can use new structure
- ✅ Documentation is accurate
- ✅ Performance meets or exceeds previous metrics
