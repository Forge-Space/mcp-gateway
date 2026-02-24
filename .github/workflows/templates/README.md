# UIForge GitHub Standardization Templates

This directory contains standardized GitHub workflow templates for UIForge projects to ensure consistent CI/CD patterns, security scanning, and dependency management across all repositories.

## 📋 Available Templates

### 1. `base-ci.yml`
**Purpose**: Base CI/CD pipeline with standardized jobs
**Includes**:
- Python linting (Ruff)
- TypeScript linting (ESLint)
- Shell script linting (Shellcheck)
- Python testing with coverage
- TypeScript testing with coverage
- Docker build verification
- Basic security scanning

**Usage**: Copy and adapt for project-specific needs

### 2. `security-scan.yml`
**Purpose**: Comprehensive security scanning workflow
**Includes**:
- CodeQL semantic analysis
- Trufflehog secret scanning
- npm audit for Node.js projects
- pip-audit for Python projects

**Usage**: Use as-is or customize severity thresholds

### 3. `renovate.yml`
**Purpose**: Automated dependency management with Renovate
**Includes**:
- Weekly dependency updates
- Auto-merge for safe updates
- Grouped PRs by dependency type
- Security vulnerability alerts
- Custom package rules

**Usage**: Configure Renovate token and customize rules

## 🚀 Quick Start

### For New Projects

1. **Copy templates to `.github/workflows/`**
   ```bash
   cp .github/workflows/templates/base-ci.yml .github/workflows/ci.yml
   cp .github/workflows/templates/security-scan.yml .github/workflows/security.yml
   cp .github/workflows/templates/renovate.yml .github/workflows/renovate.yml
   ```

2. **Configure required secrets**
   - `CODECOV_TOKEN`: Codecov upload token
   - `RENOVATE_TOKEN`: Renovate GitHub token

3. **Adapt to project structure**
   - Update file paths in coverage commands
   - Adjust build steps as needed
   - Customize security scanning rules

### For Existing Projects

1. **Gradual migration**
   - Start with security scanning template
   - Update existing CI to match base patterns
   - Replace Dependabot with Renovate

2. **Verify compatibility**
   - Test workflows in development branch
   - Monitor build times and resource usage
   - Adjust timeouts as needed

## 🔧 Configuration Details

### Standard Versions

| Tool | Version | Rationale |
|------|---------|-----------|
| GitHub Actions | Latest stable | Latest features and security |
| Node.js | v22 LTS | Long-term support, performance |
| Python | 3.12 | Latest stable with good library support |
| Codecov | v5 | Latest API and features |
| Trufflehog | v3.93.3 | Latest secret scanning |

### Quality Gates

- **Coverage**: 80% minimum threshold
- **Security**: High severity issues block merges
- **Dependencies**: Auto-merge safe updates after 3 days
- **Build**: All builds must pass
- **Linting**: Zero lint errors allowed

### Branch Protection

Recommended branch protection rules:
- **main**: 2 reviewers, all checks required, no force pushes
- **release/***: 2 reviewers (1 senior), conversation resolution
- **dev**: 1 reviewer, checks required, allow force pushes
- **feature/***: No protection, encourage PRs

## 📊 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| CI Pipeline Time | < 15 minutes | ~10-12 minutes |
| Security Scan Time | < 10 minutes | ~8-10 minutes |
| Coverage Upload | < 2 minutes | ~1 minute |
| Dependency Updates | Weekly | Configured |

## 🔒 Security Configuration

### CodeQL Settings
- **Query Suite**: Security-extended
- **Languages**: Python, TypeScript, JavaScript
- **Alert Threshold**: High or higher
- **Upload**: Always enabled

### Trufflehog Settings
- **Verified Secrets Only**: Enabled
- **Base Branch**: Main/master
- **Head Branch**: Current commit
- **Path**: Entire repository

## 🔄 Maintenance Procedures

### Weekly Tasks
- [ ] Review dependency update PRs
- [ ] Check security scan results
- [ ] Monitor CI/CD performance
- [ ] Update documentation as needed

### Monthly Tasks
- [ ] Review and update templates
- [ ] Audit security configurations
- [ ] Analyze quality metrics
- [ ] Update tool versions

### Quarterly Tasks
- [ ] Comprehensive pattern review
- [ ] Update standards documentation
- [ ] Team training and alignment
- [ ] Performance optimization

## 🚨 Troubleshooting

### Common Issues

1. **Coverage Upload Failures**
   - Check CODECOV_TOKEN configuration
   - Verify coverage file paths
   - Check network connectivity

2. **CodeQL Timeouts**
   - Increase timeout to 30 minutes
   - Exclude test files from analysis
   - Optimize code structure

3. **Renovate Failures**
   - Check RENOVATE_TOKEN permissions
   - Verify configuration syntax
   - Review package manager compatibility

### Debugging Procedures

1. **Local Testing**
   ```bash
   # Test coverage locally
   pytest --cov=src --cov-report=xml

   # Test linting
   ruff check .
   npm run lint
   ```

2. **Workflow Debugging**
   - Add `ACTIONS_STEP_DEBUG` secret with value `true`
   - Check workflow logs for detailed errors
   - Use `actions/upload-artifact` for debugging files

3. **Configuration Validation**
   - Use YAML linters for syntax checking
   - Validate secret names and permissions
   - Test with dry-run when possible

## 📚 Best Practices

### Workflow Design
- Use matrix builds for multiple environments
- Implement proper caching for dependencies
- Set appropriate timeouts for each job
- Use conditional execution for expensive jobs

### Security
- Never expose secrets in workflow logs
- Use least privilege principle for tokens
- Regularly rotate API keys and tokens
- Monitor for unusual activity

### Performance
- Parallelize independent jobs
- Use GitHub Actions cache effectively
- Optimize Docker layer caching
- Monitor and optimize build times

### Reliability
- Implement retry logic for flaky operations
- Use specific versions instead of `latest`
- Test workflows in development branches
- Monitor success rates and failures

## 📈 Success Metrics

### Quality Metrics
- **Template Consistency**: 100% of projects using shared templates
- **CI Performance**: < 15 minutes total pipeline time
- **Security Coverage**: 100% of projects with consistent scanning
- **Dependency Health**: < 5 outdated dependencies per project

### Process Metrics
- **Adoption Rate**: 100% of workflows standardized
- **Maintenance Efficiency**: 50% reduction in configuration overhead
- **Security Response**: < 24 hours for critical vulnerabilities
- **Documentation Coverage**: 90% of patterns documented

## 🤝 Contributing

### Adding New Templates
1. Create template in `templates/` directory
2. Follow existing naming conventions
3. Include comprehensive documentation
4. Test with multiple project types
5. Update this README

### Updating Existing Templates
1. Test changes in development branch
2. Update documentation
3. Communicate changes to team
4. Monitor impact on existing projects
5. Roll back if issues arise

### Reporting Issues
1. Document reproduction steps
2. Include workflow logs
3. Specify template version
4. Provide environment details
5. Suggest potential fixes

## 📞 Support

For questions or issues with these templates:
1. Check this documentation first
2. Review existing GitHub issues
3. Contact the DevOps team
4. Create an issue with detailed information
5. Join the weekly DevOps standup

---

**Last Updated**: 2025-01-19
**Version**: 1.0.0
**Maintainer**: UIForge DevOps Team
