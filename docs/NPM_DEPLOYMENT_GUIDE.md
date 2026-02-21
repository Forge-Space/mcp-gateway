# Core Package NPM Deployment Setup Guide

This guide provides a complete walkthrough for setting up automated NPM deployment for your Core Package (`@forge-mcp-gateway/client`).

## 🚀 Quick Start

### 1. Run the Setup Script
```bash
cd /path/to/mcp-gateway
./scripts/setup-npm-deployment.sh
```

### 2. Configure NPM Token
Add your NPM automation token as a GitHub repository secret:
- Go to: Repository Settings → Secrets and variables → Actions
- Add: `NPM_TOKEN` with your NPM automation token
- Generate token at: https://www.npmjs.com/settings/tokens
- Scope: automation
- Add to repository secrets

### 3. Create Release Branch
```bash
git checkout -b release/core main
git push -u origin release/core
```

### 4. Enable Branch Protection
```bash
# Use the workflow to enable branch protection
gh workflow run branch-protection-core.yml --field action=enable
```

## 📋 Files Created

### GitHub Workflows
- **`.github/workflows/npm-release-core.yml`** - Main NPM release workflow
- **.github/workflows/branch-protection-core.yml`** - Branch protection management

### Scripts
- **`scripts/setup-npm-deployment.sh`** - Automated setup script

### Configuration Files
- **`.npmignore`** - Files to exclude from NPM package
- Updated **`package.json`** - Added publish and prepack scripts

## 🔧 Workflow Triggers

The automated NPM deployment triggers on:

### Automatic Triggers
- **Push to `release/core` branch** - When changes are merged
- **Version tags** - When tags like `core-v1.0.0` are pushed
- **Manual dispatch** - For manual version bumps and dry runs

### Manual Triggers
```bash
# Manual version bump
gh workflow run npm-release-core.yml \
  --field version_type=minor \
  --field dry_run=false

# Dry run (no actual publish)
gh workflow run npm-release-core.yml \
  --field version_type=patch \
  --field dry_run=true
```

## 📦 Package Configuration

### Required package.json Fields
```json
{
  "name": "@forge-mcp-gateway/client",
  "version": "1.28.1",
  "description": "Forge MCP Gateway client - Connect to your Forge MCP Gateway instance via NPX",
  "main": "build/index.js",
  "bin": {
    "forge-mcp-gateway": "./build/index.js"
  },
  "scripts": {
    "build": "tsc",
    "prepack": "npm run build",
    "publish": "npm publish --access public"
  },
  "files": [
    "build",
    "README.md",
    "LICENSE"
  ],
  "repository": {
    "type": "git",
    "url": "https://github.com/lucassantana/forge-mcp-gateway.git"
  }
}
```

## 🛡️ Security & Quality Checks

The workflow includes comprehensive validation:

### Pre-Publish Validation
- **Linting**: ESLint checks
- **Type Checking**: TypeScript compilation
- **Build Validation**: Ensures build output exists
- **Package Validation**: Required fields and format checks

### Security Scanning
- **NPM Audit**: High-severity vulnerability checks
- **Dependency Validation**: Ensures no vulnerable dependencies

### Quality Testing
- **Local Installation Test**: Verifies package can be installed
- **Import Test**: Basic smoke test for package imports

## 🚀 Publishing Process

### Automated Publishing
1. **Validation**: All checks pass
2. **Build**: Package is built successfully
3. **Security**: No high-severity vulnerabilities
4. **Testing**: Local installation passes
5. **Publish**: Published to NPM with appropriate tag
6. **Release**: GitHub release created
- **Documentation**: Installation instructions updated

### Tag Management
- **Stable releases**: `latest` tag
- **Prereleases**: `next` tag (for versions like `1.28.1-alpha.0`)
- **Version tags**: `core-vX.Y.Z` format

## 🔐 Branch Protection Rules

### `release/core` Branch
- **Required Status Checks**: CI, validation, security, and testing must pass
- **Pull Request Reviews**: At least 1 approval required
- **Linear History**: No force pushes allowed
- **Conversation Resolution**: PR must be resolved
- **Admin Enforcement**: Only admins can bypass rules
- **Team Restrictions**: Limited to `core-maintainers` team

### Protection Benefits
- **Quality Control**: Only tested, validated code reaches release
- **Security**: Prevents accidental publishes
- **Traceability**: Clear audit trail for all changes
- **Collaboration**: Proper review process for releases

## 📊 Workflow Jobs

### 1. Validate
- Extracts version information
- Validates build output
- Checks package.json fields
- Determines if prerelease

### 2. Security & Quality
- Runs NPM security audit
- Validates package.json structure
- Checks for vulnerable dependencies

### 3. Test
- Builds the package
- Tests local installation
- Validates package imports

### 4. Publish
- Handles dry runs and actual publishing
- Manages prerelease vs stable tags
- Configures NPM token

### 5. GitHub Release
- Creates comprehensive release notes
- Links to NPM package and documentation
- Includes installation instructions

### 6. Update Documentation
- Updates README with latest version
- Updates documentation files
- Commits changes back to repository

### 7. Notify
- Success/failure notifications
- Links to published package and release

## 🔧 Manual Operations

### Manual Publishing
```bash
# Build and publish
npm run build
npm publish

# Dry run (no actual publish)
npm pack --dry-run
```

### Version Bumping
```bash
# Patch version
npm version patch

# Minor version
npm version minor

# Major version
npm version major
```

### Branch Management
```bash
# Create release branch
git checkout -b release/core main

# Merge to release branch
git checkout release/core
git merge main

# Push release branch
git push origin release/core
```

## 🚨 Troubleshooting

### Common Issues

#### Build Failures
```bash
# Check TypeScript errors
npm run lint:types

# Clean and rebuild
npm run clean
npm run build
```

#### Publishing Failures
```bash
# Check NPM token
npm whoami

# Test dry run first
npm pack --dry-run
```

#### Branch Protection Issues
```bash
# Check branch protection status
gh api repos/lucassantana/forge-mcp-gateway/branches/release/core/protection

# Remove branch protection (if needed)
gh workflow run branch-protection-core.yml --field action=disable
```

### Debug Mode
```bash
# Run workflow with debug logging
gh workflow view npm-release-core.yml
```

## 📈 Environment Variables

### Required Secrets
- **`NPM_TOKEN`**: NPM automation token for publishing
- **`GITHUB_TOKEN`**: GitHub token for API calls (auto-provided)

### Optional Environment Variables
- **`NODE_VERSION`**: Node.js version (default: 22)
- **`NPM_REGISTRY`**: NPM registry URL (default: https://registry.npmjs.org)

## 🔄 Release Process Flow

### Development Workflow
1. **Develop**: Make changes on main branch
2. **Test**: Run local tests and validation
3. **Merge**: Create PR to `release/core`
4. **Review**: PR review and approval
5. **Merge**: Merge to `release/core`
6. **Deploy**: Automatic publishing process

### Manual Release
1. **Version Bump**: `npm version patch/minor/major`
2. **Tag**: `git tag core-vX.Y.Z`
3. **Push**: `git push --tags`
4. **Publish**: `npm publish`

### Emergency Rollback
1. **Unpublish**: `npm unpublish @forge-mcp-gateway/client`
2. **Revert**: `git revert` or `git reset`
3. **Re-publish**: `npm publish` with corrected version

## 📊 Monitoring & Notifications

### Success Indicators
- ✅ Package published to NPM
- ✅ GitHub release created
- ✅ Documentation updated
- ✅ All quality checks passed

### Failure Indicators
- ❌ Build failures
- ❌ Security vulnerabilities found
- ❌ Test failures
- ❌ Publishing errors

### Notification Channels
- GitHub Actions workflow status
- GitHub releases
- Team notifications (if configured)

## 🎯 Best Practices

### Version Management
- **Semantic Versioning**: Follow semver (major.minor.patch)
- **Prereleases**: Use `-alpha`, `-beta`, `-rc` suffixes
- **Release Tags**: Use `core-vX.Y.Z` format

### Quality Assurance
- **Always test before publishing**
- **Maintain high test coverage**
- **Fix security issues promptly**
- **Keep documentation updated**

### Security
- **Use repository secrets for tokens**
- **Never commit sensitive data**
- **Rotate tokens regularly**
- **Monitor for vulnerabilities**

### Collaboration
- **Use pull requests for releases**
- **Require code reviews**
- **Maintain clear commit messages**
- **Document breaking changes**

## 📞 Support

For issues with the NPM deployment setup:

1. **Check the workflow logs** in GitHub Actions
2. **Review this setup guide** for troubleshooting steps
3. **Run the setup script** with `./scripts/setup-npm-deployment.sh`
4. **Check the workflow files** in `.github/workflows/`

## 🚀 Next Steps

1. **Run the setup script**: `./scripts/setup-npm-deployment.sh`
2. **Configure NPM token**: Add NPM_TOKEN to repository secrets
3. **Test the workflow**: Create a test PR to `release/core`
4. **Monitor releases**: Check GitHub Actions and NPM registry

Your Core Package is now ready for automated NPM publishing! 🎉