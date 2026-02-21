#!/bin/bash

# Document current state of project before cleanup
set -euo pipefail

PROJECT_NAME=${1:-"forge-mcp-gateway"}
STATE_DIR="state-documentation"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
STATE_FILE="${STATE_DIR}/${PROJECT_NAME}-${TIMESTAMP}-state.md"

echo "📋 Documenting current state for ${PROJECT_NAME}..."

# Create state directory
mkdir -p "${STATE_DIR}"

# Create state documentation
cat > "${STATE_FILE}" << EOF
# Project State Documentation: ${PROJECT_NAME}

**Generated:** $(date)
**Timestamp:** ${TIMESTAMP}

## 📊 Project Overview

### Basic Information
- **Project Name:** ${PROJECT_NAME}
- **Working Directory:** $(pwd)
- **Git Branch:** $(git branch --show-current 2>/dev/null || echo "Not a git repository")
- **Git Status:** $(git status --porcelain 2>/dev/null | wc -l) files modified

### File Structure Analysis
\`\`\`
$(find . -type f -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.js" -o -name "*.ts" -o -name "*.md" | head -50)
\`\`\`

## 🔧 Configuration Files

### Code Quality Configuration

#### ESLint Configuration
\`\`\`json
$(cat .eslintrc* 2>/dev/null || echo "No ESLint configuration found")
\`\`\`

#### Prettier Configuration
\`\`\`json
$(cat .prettierrc* 2>/dev/null || echo "No Prettier configuration found")
\`\`\`

#### CodeRabbit Configuration
\`\`\`yaml
$(cat .coderabbit.yaml 2>/dev/null || echo "No CodeRabbit configuration found")
\`\`\`

### Environment Files
$(find . -name ".env*" -type f | while read file; do
    echo "#### $file"
    echo '```bash'
    head -20 "$file" | grep -v "SECRET\|KEY\|TOKEN\|PASSWORD" || echo "File exists but content hidden for security"
    echo '```'
    echo ""
done)

## 📝 Documentation Files

### README Files
$(find . -name "README*" -type f | while read file; do
    echo "#### $file"
    echo "- Size: $(wc -l < "$file") lines"
    echo "- Last modified: $(stat -f "%Sm" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null)"
    echo ""
done)

### Documentation Structure
\`\`\`
$(find docs -type f 2>/dev/null | head -20 || echo "No docs directory found")
\`\`\`

## 🔄 CI/CD Configuration

### GitHub Actions Workflows
\`\`\`
$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | while read file; do
    echo "### $file"
    echo "- Size: $(wc -l < "$file") lines"
    echo "- Jobs: $(grep -c "jobs:" "$file" 2>/dev/null || echo "0")"
    echo ""
done)
\`\`\`

### Pull Request Template
\`\`\`markdown
$(cat .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null || echo "No PR template found")
\`\`\`

## 📦 Package Configuration

### package.json
\`\`\`json
$(cat package.json 2>/dev/null | jq '.scripts' 2>/dev/null || echo "No package.json found")
\`\`\`

### Dependencies
\`\`\`
$(cat package.json 2>/dev/null | jq '.dependencies + .devDependencies | keys' 2>/dev/null || echo "No dependencies found")
\`\`\`

## 🐳 Docker Configuration

### Dockerfiles
\`\`\`
$(find . -name "Dockerfile*" -type f | while read file; do
    echo "### $file"
    echo "- Size: $(wc -l < "$file") lines"
    echo "- Base image: $(grep "^FROM" "$file" | head -1)"
    echo ""
done)
\`\`\`

### Docker Compose
\`\`\`yaml
$(head -50 docker-compose.yml 2>/dev/null || echo "No docker-compose.yml found")
\`\`\`

## 🧪 Testing Configuration

### Test Files
\`\`\`
$(find . -name "*.test.*" -o -name "*.spec.*" -type f | head -20)
\`\`\`

### Test Scripts in package.json
\`\`\`json
$(cat package.json 2>/dev/null | jq '.scripts | keys | map(select(test("test")))' 2>/dev/null || echo "No test scripts found")
\`\`\`

## 📈 Metrics Summary

### File Counts
- **Total files:** $(find . -type f | wc -l)
- **Configuration files:** $(find . -name ".*" -type f | wc -l)
- **Documentation files:** $(find . -name "*.md" -type f | wc -l)
- **Code files:** $(find . -name "*.js" -o -name "*.ts" -o -name "*.py" -type f | wc -l)

### Size Analysis
- **Total size:** $(du -sh . | cut -f1)
- **Largest files:** $(find . -type f -exec du -h {} + | sort -hr | head -10)

## 🚨 Potential Issues

### Duplicate Files
\`\`\`
$(find . -name "*.json" -o -name "*.yaml" -o -name "*.yml" | sort | uniq -d)
\`\`\`

### Large Files (>1MB)
\`\`\`
$(find . -type f -size +1M -exec ls -lh {} + | head -10)
\`\`\`

---

**Documentation completed at:** $(date)
**Total documentation time:** $(date +%s)
EOF

echo "✅ State documentation created!"
echo "📍 Location: ${STATE_FILE}"
echo ""
echo "📊 Summary:"
echo "- Configuration files documented"
echo "- File structure analyzed"
echo "- Dependencies cataloged"
echo "- CI/CD workflows documented"
echo "- Docker configuration documented"
