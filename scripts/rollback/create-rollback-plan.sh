#!/bin/bash

# Create comprehensive rollback plan for cleanup operations
set -euo pipefail

PROJECT_NAME=${1:-"forge-mcp-gateway"}
ROLLBACK_DIR="rollback-plans"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
ROLLBACK_FILE="${ROLLBACK_DIR}/${PROJECT_NAME}-${TIMESTAMP}-rollback.md"

echo "🔄 Creating rollback plan for ${PROJECT_NAME}..."

# Create rollback directory
mkdir -p "${ROLLBACK_DIR}"

# Create rollback plan
cat > "${ROLLBACK_FILE}" << EOF
# Rollback Plan: ${PROJECT_NAME}

**Created:** $(date)
**Timestamp:** ${TIMESTAMP}
**Project:** ${PROJECT_NAME}

## 🚨 Emergency Rollback Procedures

### Immediate Rollback (Critical Issues)

#### 1. Restore from Backup
\`\`\`bash
# Stop any running processes
docker-compose down 2>/dev/null || true

# Restore from latest backup
LATEST_BACKUP=\$(ls -t backups/${PROJECT_NAME}-*.tar.gz | head -1)
tar -xzf "\$LATEST_BACKUP"

# Reset git state
git checkout HEAD -- .
git clean -fd

# Restart services
docker-compose up -d
\`\`\`

#### 2. Git Reset (If backup not available)
\`\`\`bash
# Reset to last known good state
git reset --hard HEAD~1

# Clean untracked files
git clean -fd

# Restore dependencies
npm install
pip install -r requirements.txt
\`\`\`

## 📋 Detailed Rollback by Category

### Configuration Files Rollback

#### ESLint Configuration
\`\`\`bash
# Restore ESLint config
git checkout HEAD -- .eslintrc* eslint.config.*

# Verify configuration
npx eslint --print-config . > /tmp/eslint-check.json
\`\`\`

#### Prettier Configuration
\`\`\`bash
# Restore Prettier config
git checkout HEAD -- .prettierrc*

# Verify configuration
npx prettier --check . > /tmp/prettier-check.log
\`\`\`

#### CodeRabbit Configuration
\`\`\`bash
# Restore CodeRabbit config
git checkout HEAD -- .coderabbit.yaml

# Verify configuration
yamllint .coderabbit.yaml
\`\`\`

### Documentation Rollback

#### README Files
\`\`\`bash
# Restore README files
git checkout HEAD -- README*

# Verify documentation
grep -q "# " README.md
\`\`\`

#### Documentation Structure
\`\`\`bash
# Restore docs directory
git checkout HEAD -- docs/

# Verify structure
ls docs/ > /tmp/docs-check.txt
\`\`\`

### CI/CD Rollback

#### GitHub Actions Workflows
\`\`\`bash
# Restore workflows
git checkout HEAD -- .github/workflows/

# Verify workflows
yamllint .github/workflows/*.yml
\`\`\`

#### Pull Request Template
\`\`\`bash
# Restore PR template
git checkout HEAD -- .github/PULL_REQUEST_TEMPLATE.md

# Verify template
test -f .github/PULL_REQUEST_TEMPLATE.md
\`\`\`

### Environment Files Rollback

#### Environment Configurations
\`\`\`bash
# Restore environment files
git checkout HEAD -- .env*

# Verify environment files
ls .env* > /tmp/env-check.txt
\`\`\`

### Docker Configuration Rollback

#### Dockerfiles
\`\`\`bash
# Restore Dockerfiles
git checkout HEAD -- Dockerfile*

# Verify Dockerfiles
ls Dockerfile* > /tmp/docker-check.txt
docker build -t test-rollback .
\`\`\`

#### Docker Compose
\`\`\`bash
# Restore docker-compose
git checkout HEAD -- docker-compose.yml

# Verify configuration
docker-compose config > /tmp/compose-check.yml
\`\`\`

## 🧪 Validation Procedures

### Pre-Rollback Validation
\`\`\`bash
# Check current state
echo "Current git status:"
git status --porcelain

echo "Current working directory:"
pwd

echo "Running processes:"
ps aux | grep -E "(node|python|docker)" | grep -v grep

# Create rollback checkpoint
git add .
git commit -m "rollback-checkpoint-${TIMESTAMP}" || true
\`\`\`

### Post-Rollback Validation
\`\`\`bash
# Verify project builds
npm run build 2>/dev/null || echo "Build not configured"

# Verify linting works
npm run lint 2>/dev/null || echo "Lint not configured"

# Verify tests pass
npm test 2>/dev/null || echo "Tests not configured"

# Verify Docker works
docker-compose config > /dev/null

# Verify git status is clean
git status --porcelain
\`\`\`

## 📞 Contact Information

### Primary Contacts
- **Project Lead:** [Contact information]
- **DevOps Team:** [Contact information]
- **Infrastructure Team:** [Contact information]

### Escalation Path
1. **Level 1:** Project Lead
2. **Level 2:** DevOps Team
3. **Level 3:** Infrastructure Team
4. **Level 4:** Emergency Response Team

## 🔍 Troubleshooting

### Common Issues

#### 1. Git Reset Fails
\`\`\`bash
# Force reset
git reset --hard HEAD
git clean -fd

# If still fails, reclone repository
cd ..
rm -rf ${PROJECT_NAME}
git clone [repository-url] ${PROJECT_NAME}
cd ${PROJECT_NAME}
\`\`\`

#### 2. Dependencies Not Restored
\`\`\`bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install

# For Python
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
\`\`\`

#### 3. Docker Issues
\`\`\`bash
# Clean Docker
docker system prune -f
docker-compose down --volumes

# Rebuild
docker-compose build --no-cache
docker-compose up -d
\`\`\`

#### 4. Permission Issues
\`\`\`bash
# Fix permissions
chmod +x scripts/*.sh
chown -R $USER:$USER .

# For Docker
sudo chown -R $USER:$USER .docker
\`\`\`

## 📊 Rollback Metrics

### Success Indicators
- [ ] All configuration files restored
- [ ] All documentation restored
- [ ] All CI/CD workflows restored
- [ ] All Docker configurations restored
- [ ] Project builds successfully
- [ ] All tests pass
- [ ] Git status is clean

### Failure Indicators
- [ ] Configuration files missing
- [ ] Build failures
- [ ] Test failures
- [ ] Docker errors
- [ ] Git conflicts

## 🔄 Rollback Testing

### Test Rollback Procedure
\`\`\`bash
# Create test scenario
mkdir -p /tmp/rollback-test
cp -r . /tmp/rollback-test/${PROJECT_NAME}-test

# Test rollback in copy
cd /tmp/rollback-test/${PROJECT_NAME}-test
./rollback-cleanup.sh ${PROJECT_NAME} test-rollback

# Verify test results
if [ \$? -eq 0 ]; then
    echo "Rollback test successful"
else
    echo "Rollback test failed"
    exit 1
fi
\`\`\`

## 📝 Rollback Log

### Rollback History
| Date | Reason | Success | Notes |
|------|--------|---------|-------|
| ${TIMESTAMP} | Initial rollback plan | N/A | Plan created |

### Rollback Checklist
- [ ] Backup verified
- [ ] Rollback procedures tested
- [ ] Contact information updated
- [ ] Validation procedures confirmed
- [ ] Documentation updated

---

**Rollback plan created at:** $(date)
**Next review date:** $(date -v +1m)
**Plan version:** 1.0
EOF

echo "✅ Rollback plan created!"
echo "📍 Location: ${ROLLBACK_FILE}"
echo ""
echo "🔄 Key rollback procedures:"
echo "- Emergency backup restore"
echo "- Git reset procedures"
echo "- Configuration file restoration"
echo "- Validation procedures"
echo "- Troubleshooting guide"

# Create the actual rollback script
cat > "${ROLLBACK_DIR}/rollback-cleanup.sh" << 'EOF'
#!/bin/bash

# Execute rollback for cleanup operations
set -euo pipefail

PROJECT_NAME=${1:-"forge-mcp-gateway"}
ROLLBACK_TYPE=${2:-"backup"}

echo "🔄 Executing rollback for ${PROJECT_NAME} (type: ${ROLLBACK_TYPE})..."

case "${ROLLBACK_TYPE}" in
    "backup")
        echo "📦 Restoring from backup..."
        LATEST_BACKUP=$(ls -t backups/${PROJECT_NAME}-*.tar.gz 2>/dev/null | head -1)
        if [ -z "${LATEST_BACKUP}" ]; then
            echo "❌ No backup found for ${PROJECT_NAME}"
            exit 1
        fi

        echo "📍 Using backup: ${LATEST_BACKUP}"
        tar -xzf "${LATEST_BACKUP}"
        echo "✅ Backup restored"
        ;;

    "git")
        echo "🔄 Resetting git state..."
        git reset --hard HEAD~1
        git clean -fd
        echo "✅ Git reset completed"
        ;;

    "config")
        echo "⚙️ Restoring configuration files..."
        git checkout HEAD -- .eslintrc* eslint.config.* .prettierrc* .coderabbit.yaml
        echo "✅ Configuration files restored"
        ;;

    "docs")
        echo "📝 Restoring documentation..."
        git checkout HEAD -- README* docs/ .github/PULL_REQUEST_TEMPLATE.md
        echo "✅ Documentation restored"
        ;;

    "ci-cd")
        echo "🔄 Restoring CI/CD workflows..."
        git checkout HEAD -- .github/workflows/
        echo "✅ CI/CD workflows restored"
        ;;

    "docker")
        echo "🐳 Restoring Docker configuration..."
        git checkout HEAD -- Dockerfile* docker-compose.yml
        echo "✅ Docker configuration restored"
        ;;

    "full")
        echo "🔄 Full rollback..."
        ./rollback-cleanup.sh "${PROJECT_NAME}" backup
        ./rollback-cleanup.sh "${PROJECT_NAME}" git
        echo "✅ Full rollback completed"
        ;;

    *)
        echo "❌ Unknown rollback type: ${ROLLBACK_TYPE}"
        echo "Available types: backup, git, config, docs, ci-cd, docker, full"
        exit 1
        ;;
esac

echo ""
echo "🧪 Validating rollback..."

# Basic validation
if [ -f "package.json" ]; then
    echo "✅ package.json exists"
else
    echo "❌ package.json missing"
fi

if [ -d ".github" ]; then
    echo "✅ .github directory exists"
else
    echo "❌ .github directory missing"
fi

if [ -f "README.md" ]; then
    echo "✅ README.md exists"
else
    echo "❌ README.md missing"
fi

echo ""
echo "🔄 Rollback completed for ${PROJECT_NAME}"
echo "📋 Next steps:"
echo "1. Verify project builds: npm run build"
echo "2. Verify tests pass: npm test"
echo "3. Verify Docker works: docker-compose config"
echo "4. Commit rollback if needed: git add . && git commit -m 'rollback: ${ROLLBACK_TYPE}'"
EOF

chmod +x "${ROLLBACK_DIR}/rollback-cleanup.sh"

echo "📜 Rollback script created: ${ROLLBACK_DIR}/rollback-cleanup.sh"
