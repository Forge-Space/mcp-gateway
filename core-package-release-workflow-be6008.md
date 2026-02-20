# Core Package Release Workflow Plan

This plan outlines a comprehensive workflow for releasing new versions of the @forgespace/core package and updating all dependent projects in the Forge ecosystem.

## Current State Analysis

Based on the project analysis, here's the current dependency landscape:

### Core Package: @forgespace/core
- **Current Version**: 1.1.5
- **Repository**: forge-patterns
- **Type**: TypeScript/JavaScript package
- **Publishing**: npm registry with public access

### Dependent Projects
1. **@forgespace/ui-mcp** (uiforge-mcp)
   - Current: ^1.1.5 (dependencies), ^1.1.4 (devDependencies)
   - Type: TypeScript MCP server
   - Integration: Direct npm dependency

2. **uiforge-webapp**
   - Current: ^1.1.5 (devDependencies)
   - Type: Next.js application (monorepo)
   - Integration: Development dependency via workspace

3. **mcp-gateway**
   - Current: No direct @forgespace/core dependency
   - Type: Python MCP gateway
   - Integration: Uses mcp-contextforge-gateway (separate package)

## Release Workflow Strategy

### Phase 1: Pre-Release Preparation
**Objective**: Ensure core package is ready for release with quality gates

**Tasks**:
1. **Version Management**
   - Determine semantic version bump (patch/minor/major)
   - Update version in package.json
   - Update CHANGELOG.md with release notes

2. **Quality Assurance**
   - Run complete test suite: `npm run test:all`
   - Validate linting: `npm run lint:check`
   - Check formatting: `npm run format:check`
   - Build validation: `npm run build`

3. **Documentation Updates**
   - Update README.md if API changes
   - Update any pattern documentation
   - Verify integration guides are current

### Phase 2: Core Package Release
**Objective**: Publish the updated core package to npm

**Tasks**:
1. **Build Process**
   - Clean build: `npm run clean && npm run build`
   - Validate build output
   - Test package locally

2. **Publishing**
   - Publish to npm: `npm run publish:npm`
   - Verify package availability
   - Check npm registry for correct version

3. **Release Verification**
   - Install fresh copy in test environment
   - Validate basic functionality
   - Check package integrity

### Phase 3: Dependency Updates
**Objective**: Update all dependent projects to use the new core version

**Tasks**:
1. **@forgespace/ui-mcp Updates**
   ```bash
   cd /Users/lucassantana/Desenvolvimento/uiforge-mcp
   npm install @forgespace/core@latest
   npm install  # Update lockfile
   ```

2. **uiforge-webapp Updates**
   ```bash
   cd /Users/lucassantana/Desenvolvimento/uiforge-webapp
   npm install @forgespace/core@latest
   npm install  # Update workspace lockfiles
   ```

3. **Version Consistency Check**
   - Verify all projects use same version
   - Check for version conflicts
   - Validate peer dependency requirements

### Phase 4: Integration Testing
**Objective**: Ensure all dependent projects work correctly with new core version

**Tasks**:
1. **Build Validation**
   - uiforge-mcp: `npm run build`
   - uiforge-webapp: `npm run build`

2. **Test Execution**
   - uiforge-mcp: `npm run test`
   - uiforge-webapp: `npm run test`

3. **Integration Testing**
   - Test MCP server functionality
   - Validate UI generation workflows
   - Check cross-project compatibility

### Phase 5: Documentation and Communication
**Objective**: Document release and communicate changes to team

**Tasks**:
1. **Release Documentation**
   - Create GitHub release with changelog
   - Update project documentation
   - Document any breaking changes

2. **Team Communication**
   - Notify team of new release
   - Share migration guide if needed
   - Update project status dashboards

## Quality Gates and Validation

### Pre-Release Checklist
- [ ] All tests pass (≥80% coverage)
- [ ] Linting passes with 0 errors
- [ ] Build succeeds without warnings
- [ ] Documentation is updated
- [ ] Version follows semantic versioning
- [ ] CHANGELOG.md is comprehensive

### Post-Release Validation
- [ ] Core package available on npm
- [ ] All dependent projects build successfully
- [ ] Integration tests pass
- [ ] No breaking changes in production
- [ ] Performance benchmarks maintained

## Risk Management and Rollback

### Potential Issues
1. **Build Failures**: Projects may not build with new version
2. **Breaking Changes**: API changes may break dependent code
3. **Version Conflicts**: Dependency resolution issues
4. **Publishing Failures**: npm registry issues

### Rollback Strategy
1. **Immediate Rollback**
   ```bash
   # Unpublish problematic version
   npm unpublish @forgespace/core@version --force
   
   # Republish previous stable version
   npm publish @forgespace/core@previous-version --tag latest
   ```

2. **Dependency Rollback**
   ```bash
   # Revert dependent projects
   npm install @forgespace/core@previous-version
   ```

3. **Communication**
   - Immediate team notification
   - Issue documentation
   - Recovery timeline

## Automation Opportunities

### GitHub Actions Workflow
```yaml
name: Core Package Release
on:
  push:
    tags:
      - 'core/v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Release Core Package
        run: |
          cd /Users/lucassantana/Desenvolvimento/forge-patterns
          npm run publish:npm
      
      - name: Update Dependencies
        run: |
          # Update uiforge-mcp
          cd /Users/lucassantana/Desenvolvimento/uiforge-mcp
          npm install @forgespace/core@latest
          
          # Update uiforge-webapp
          cd /Users/lucassantana/Desenvolvimento/uiforge-webapp
          npm install @forgespace/core@latest
      
      - name: Validate Integration
        run: |
          # Test all projects
          cd /Users/lucassantana/Desenvolvimento/uiforge-mcp && npm test
          cd /Users/lucassantana/Desenvolvimento/uiforge-webapp && npm test
```

### Release Scripts
```bash
#!/bin/bash
# release-core.sh - Complete core package release workflow

set -e

echo "🚀 Starting @forgespace/core package release..."

# Phase 1: Preparation
echo "📋 Preparing release..."
cd /Users/lucassantana/Desenvolvimento/forge-patterns
npm run test:all
npm run lint:check
npm run format:check
npm run build

# Phase 2: Publishing
echo "📦 Publishing package..."
npm run publish:npm

# Phase 3: Dependencies
echo "🔄 Updating dependencies..."
cd /Users/lucassantana/Desenvolvimento/uiforge-mcp
npm install @forgespace/core@latest

cd /Users/lucassantana/Desenvolvimento/uiforge-webapp
npm install @forgespace/core@latest

# Phase 4: Validation
echo "🧪 Validating integration..."
cd /Users/lucassantana/Desenvolvimento/uiforge-mcp
npm run build && npm test

cd /Users/lucassantana/Desenvolvimento/uiforge-webapp
npm run build && npm test

echo "✅ Release completed successfully!"
```

## Success Metrics

### Release Quality Metrics
- **Release Success Rate**: 100% (no rollback needed)
- **Build Success Rate**: 100% (all dependent projects build)
- **Test Pass Rate**: 100% (all tests pass)
- **Documentation Coverage**: 100% (all changes documented)

### Timeline Estimates
- **Phase 1 (Preparation)**: 30 minutes
- **Phase 2 (Publishing)**: 15 minutes
- **Phase 3 (Dependencies)**: 20 minutes
- **Phase 4 (Testing)**: 45 minutes
- **Phase 5 (Documentation)**: 30 minutes

**Total Estimated Time**: 2 hours 20 minutes

## Next Steps

1. **Implement Release Scripts**: Create automation scripts for the workflow
2. **Set Up CI/CD**: Configure GitHub Actions for automated releases
3. **Test Workflow**: Perform a practice release with patch version
4. **Document Procedures**: Create team documentation for release process
5. **Monitor Releases**: Set up monitoring for release success metrics

This comprehensive plan ensures reliable, high-quality releases of the @forgespace/core package with minimal disruption to dependent projects and clear rollback procedures if issues arise.