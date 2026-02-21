# Core Package Release Implementation Plan

This plan implements the comprehensive release workflow for @forgespace/core package with automation scripts and dependency update workflows.

## Current State Analysis

Based on my analysis, the forge-patterns repository already has:

### ✅ Existing Infrastructure
- **GitHub Actions**: Complete release workflow (release.yml) with automated publishing
- **npm Scripts**: `publish:npm` script for manual publishing
- **Integration Scripts**: `integrate.js` for updating dependent projects
- **Quality Gates**: Comprehensive testing, linting, and security scanning
- **Documentation**: CHANGELOG.md and README.md

### 📋 Identified Gaps
1. **Missing Release Scripts**: No centralized release automation script
2. **Dependency Update Workflow**: No automated dependency update for all projects
3. **Rollback Procedures**: No automated rollback capabilities
4. **Release Validation**: No post-release integration testing
5. **Team Communication**: No automated notification system

## Implementation Strategy

### Phase 1: Create Release Automation Scripts
**Objective**: Create centralized scripts for the release workflow

**Tasks**:
1. **Main Release Script** (`scripts/release-core.sh`)
   - Complete 5-phase release workflow
   - Quality gates and validation
   - Error handling and rollback capabilities
   - Progress reporting and logging

2. **Dependency Update Script** (`scripts/update-dependencies.sh`)
   - Update all dependent projects automatically
   - Version consistency validation
   - Build and test validation
   - Rollback capabilities

3. **Quality Validation Script** (`scripts/validate-release.sh`)
   - Pre-release quality checks
   - Post-release validation
   - Integration testing
   - Performance benchmarking

### Phase 2: Enhanced GitHub Actions
**Objective**: Extend existing workflows with dependency updates

**Tasks**:
1. **Update Release Workflow**
   - Add dependency update jobs
   - Add integration testing jobs
   - Add rollback procedures
   - Add team notification workflows

2. **Dependency Update Workflow**
   - Separate workflow for dependency updates
   - Triggered by core package releases
   - Parallel validation across projects

### Phase 3: Rollback and Recovery
**Objective**: Implement automated rollback procedures

**Tasks**:
1. **Rollback Script** (`scripts/rollback-release.sh`)
   - Unpublish problematic versions
   - Restore previous stable versions
   - Update dependent projects
   - Team notification

2. **Recovery Procedures**
   - Automated issue detection
   - Quick recovery scripts
   - Communication templates

### Phase 4: Monitoring and Reporting
**Objective**: Add comprehensive monitoring and reporting

**Tasks**:
1. **Release Metrics Dashboard**
   - Track release success rates
   - Monitor build times
   - Track rollback frequency

2. **Automated Reporting**
   - Release summary reports
   - Integration test results
   - Performance comparisons

## Implementation Details

### Script Specifications

#### 1. Main Release Script (`scripts/release-core.sh`)
```bash
#!/bin/bash
# Complete @forgespace/core package release workflow

set -e

# Configuration
CORE_REPO="/Users/lucassantana/Desenvolvimento/forge-patterns"
DEPENDENT_PROJECTS=(
    "/Users/lucassantana/Desenvolvimento/uiforge-mcp"
    "/Users/lucassantana/Desenvolvimento/uiforge-webapp"
)
QUALITY_GATES=true
ROLLBACK_ENABLED=true
TEAM_NOTIFICATIONS=true

# Phase 1: Pre-Release Preparation
echo "🚀 Starting @forgespace/core package release..."

# Navigate to core repository
cd "$CORE_REPO"

# Quality checks
if [ "$QUALITY_GATES" = true ]; then
    echo "📋 Running quality gates..."
    npm run test:all
    npm run lint:check
    npm run format:check
    npm run build
fi

# Version management
VERSION_TYPE=${1:-"patch"}
echo "📋 Version bump type: $VERSION_TYPE"
npm version "$VERSION_TYPE"

# Documentation updates
echo "📝 Updating documentation..."
# Add CHANGELOG.md updates here

# Phase 2: Publishing
echo "📦 Publishing package..."
npm run publish:npm

# Phase 3: Dependency Updates
echo "🔄 Updating dependent projects..."
for project in "${DEPENDENT_PROJECTS[@]}"; do
    echo "🔄 Updating $project..."
    cd "$project"
    npm install @forgespace/core@latest
    npm install  # Update lockfile
done

# Phase 4: Integration Testing
echo "🧪 Running integration tests..."
for project in "${DEPENDENT_PROJECTS[@]}"; do
    echo "🧪 Testing $project..."
    cd "$project"
    npm run build
    npm test
done

# Phase 5: Documentation and Communication
echo "📋 Creating release documentation..."
# Create GitHub release
# Send team notifications

echo "✅ Release completed successfully!"
```

#### 2. Dependency Update Script (`scripts/update-dependencies.sh`)
```bash
#!/bin/bash
# Update all dependent projects to use latest @forgespace/core

set -e

PROJECTS=(
    "/Users/lucassantana/Desenvolvimento/uiforge-mcp"
    "/Users/lucassantana/Desenvolvimento/uiforge-webapp"
)

echo "🔄 Updating all dependent projects..."

for project in "${PROJECTS[@]}"; do
    echo "🔄 Updating $project..."
    cd "$project"
    
    # Update core dependency
    npm install @forgespace/core@latest
    
    # Update lockfile
    npm install
    
    # Validate build
    npm run build
    
    # Run tests
    npm test
    
    echo "✅ $project updated successfully"
done

echo "✅ All dependencies updated!"
```

#### 3. Rollback Script (`scripts/rollback-release.sh`)
```bash
#!/bin/bash
# Rollback @forgespace/core package and dependencies

set -e

PREVIOUS_VERSION=${1:-"1.1.4"}
CORE_REPO="/Users/lucassantana/Desenvolvimento/forge-patterns"
DEPENDENT_PROJECTS=(
    "/Users/lucassantana/Desenvolvimento/uiforge-mcp"
    "/Users/lucassantana/Desenvolvimento/uiforge-webapp"
)

echo "🔄 Rolling back to version $PREVIOUS_VERSION..."

# Unpublish current version
echo "📦 Unpublishing current version..."
npm unpublish @forgespace/core@current --force

# Republish previous version
echo "📦 Republishing previous version..."
cd "$CORE_REPO"
npm version "$PREVIOUS_VERSION" --no-git-tag-version
npm run publish:npm

# Rollback dependencies
for project in "${DEPENDENT_PROJECTS[@]}"; do
    echo "🔄 Rolling back $project..."
    cd "$project"
    npm install @forgespace/core@$PREVIOUS_VERSION
    npm install
done

echo "✅ Rollback completed!"
```

### Enhanced GitHub Actions

#### 1. Updated Release Workflow
- Add dependency update jobs
- Add integration testing jobs
- Add rollback jobs
- Add team notification workflows

#### 2. New Dependency Update Workflow
- Triggered by core package releases
- Parallel validation
- Rollback capabilities

### Quality Gates and Validation

#### Pre-Release Checklist
- [ ] All tests pass (≥80% coverage)
- [ ] Linting passes with 0 errors
- [ ] Build succeeds without warnings
- [ ] Documentation is updated
- [ ] Version follows semantic versioning
- [ ] CHANGELOG.md is comprehensive

#### Post-Release Validation
- [ ] Core package available on npm
- [ ] All dependent projects build successfully
- [ ] Integration tests pass
- [ ] No breaking changes in production
- [ ] Performance benchmarks maintained

## Success Metrics

### Release Quality Metrics
- **Release Success Rate**: 100% (no rollback needed)
- **Build Success Rate**: 100% (all dependent projects build)
- **Test Pass Rate**: 100% (all tests pass)
- **Documentation Coverage**: 100% (all changes documented)

### Timeline Estimates
- **Script Implementation**: 2 hours
- **GitHub Actions Update**: 1 hour
- **Testing and Validation**: 1 hour
- **Documentation**: 30 minutes

**Total Implementation Time**: 4 hours 30 minutes

## Risk Mitigation

### Potential Issues
1. **Build Failures**: Projects may not build with new version
2. **Breaking Changes**: API changes may break dependent code
3. **Version Conflicts**: Dependency resolution issues
4. **Publishing Failures**: npm registry issues

### Mitigation Strategies
1. **Pre-Release Testing**: Comprehensive quality gates
2. **Rollback Procedures**: Automated rollback capabilities
3. **Version Validation**: Consistency checks across projects
4. **Communication**: Clear notification procedures

## Next Steps

1. **Create Release Scripts**: Implement the automation scripts
2. **Update GitHub Actions**: Enhance existing workflows
3. **Test Workflow**: Perform a practice release
4. **Document Procedures**: Create team documentation
5. **Monitor Releases**: Set up monitoring and reporting

This implementation will provide a robust, automated release workflow that ensures high-quality releases with minimal manual intervention and comprehensive rollback capabilities.