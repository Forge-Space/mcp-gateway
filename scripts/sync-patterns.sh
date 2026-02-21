#!/bin/bash
# Sync patterns from the shared repository
# Usage: ./scripts/sync-patterns.sh [version]

set -euo pipefail

PATTERNS_REPO="uiforge-patterns/patterns"
PATTERNS_VERSION=${1:-"v1.0"}
PROJECT_TYPE=${2:-"gateway"}

echo "🔄 Syncing patterns from $PATTERNS_REPO@$PATTERNS_VERSION"
echo "🎯 Project type: $PROJECT_TYPE"

# Function to sync a file
sync_file() {
    local source_path="$1"
    local target_path="$2"
    local backup_path="${target_path}.backup"

    echo "📥 Syncing $source_path -> $target_path"

    # Create backup if target exists
    if [[ -f "$target_path" ]]; then
        cp "$target_path" "$backup_path"
        echo "📋 Created backup: $backup_path"
    fi

    # Download new version
    if curl -fsSL "https://raw.githubusercontent.com/$PATTERNS_REPO/$PATTERNS_VERSION/$source_path" -o "$target_path.tmp"; then
        mkdir -p "$(dirname "$target_path")"
        mv "$target_path.tmp" "$target_path"
        echo "✅ Updated $target_path"

        # Remove backup if successful
        if [[ -f "$backup_path" ]]; then
            rm -f "$backup_path"
            echo "🗑️  Removed backup: $backup_path"
        fi
    else
        echo "❌ Failed to download $source_path"
        # Restore backup if exists
        if [[ -f "$backup_path" ]]; then
            mv "$backup_path" "$target_path"
            echo "🔄 Restored backup: $backup_path"
        fi
        return 1
    fi
}

# Function to sync directory
sync_directory() {
    local source_dir="$1"
    local target_dir="$2"

    echo "📁 Syncing directory $source_dir -> $target_dir"

    # Create target directory
    mkdir -p "$target_dir"

    # Get list of files in source directory
    local files=$(curl -fsSL "https://api.github.com/repos/$PATTERNS_REPO/contents/$source_dir?ref=$PATTERNS_VERSION" | \
               grep -o '"name":"[^"]*"' | \
               sed 's/"name":"//g' | sed 's/"//g' || true)

    for file in $files; do
        if [[ "$file" != *.md ]] && [[ "$file" != *.yml ]] && [[ "$file" != *.json ]]; then
            continue
        fi

        sync_file "$source_dir/$file" "$target_dir/$file"
    done
}

# Sync workflows
echo "📋 Syncing workflows..."
sync_file ".github/workflows/base/ci.yml" ".github/workflows/ci.yml"
sync_file ".github/workflows/base/security.yml" ".github/workflows/security.yml"
sync_file ".github/workflows/base/dependencies.yml" ".github/workflows/dependencies.yml"

# Sync reusable workflows
mkdir -p .github/workflows/reusable
sync_file ".github/workflows/reusable/setup-node.yml" ".github/workflows/reusable/setup-node.yml"
sync_file ".github/workflows/reusable/setup-python.yml" ".github/workflows/reusable/setup-python.yml"
sync_file ".github/workflows/reusable/upload-coverage.yml" ".github/workflows/reusable/upload-coverage.yml"

# Sync templates
echo "📄 Syncing templates..."
sync_file ".github/templates/PULL_REQUEST_TEMPLATE.md" ".github/PULL_REQUEST_TEMPLATE.md"
sync_file ".github/templates/ISSUE_TEMPLATE/bug_report.md" ".github/ISSUE_TEMPLATE/bug_report.md"
sync_file ".github/templates/ISSUE_TEMPLATE/feature_request.md" ".github/ISSUE_TEMPLATE/feature_request.md"

# Sync project-specific template
sync_file ".github/templates/project-setup/$PROJECT_TYPE.md" ".github/templates/project-setup/$PROJECT_TYPE.md"

# Sync configurations
echo "⚙️  Syncing configurations..."
sync_file ".github/configs/codecov.yml" ".codecov.yml"
sync_file ".github/configs/renovate.json" "renovate.json"
sync_file ".github/configs/codeql-config.yml" ".github/configs/codeql-config.yml"
sync_file ".github/configs/branch-protection.yml" ".github/configs/branch-protection.yml"

# Create validation script
echo "🔍 Creating validation script..."
cat > scripts/validate-patterns.sh << 'EOF'
#!/bin/bash
# Validate that patterns are properly configured

set -euo pipefail

echo "🔍 Validating patterns configuration..."

# Check required files exist
required_files=(
    ".github/workflows/ci.yml"
    ".github/PULL_REQUEST_TEMPLATE.md"
    ".codecov.yml"
    "renovate.json"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    echo "❌ Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

# Validate YAML syntax
echo "📋 Validating YAML files..."
yaml_files=(
    ".github/workflows/ci.yml"
    ".codecov.yml"
    "renovate.json"
)

for file in "${yaml_files[@]}"; do
    if [[ -f "$file" ]]; then
        if command -v yq >/dev/null 2>&1; then
            if yq eval '.' "$file" >/dev/null 2>&1; then
                echo "✅ $file: Valid YAML"
            else
                echo "❌ $file: Invalid YAML"
                exit 1
            fi
        else
            echo "⚠️  yq not found, skipping YAML validation for $file"
        fi
    fi
done

# Validate JSON syntax
echo "📋 Validating JSON files..."
json_files=(
    "renovate.json"
)

for file in "${json_files[@]}"; do
    if [[ -f "$file" ]]; then
        if python3 -m json.tool "$file" >/dev/null 2>&1; then
            echo "✅ $file: Valid JSON"
        else
            echo "❌ $file: Invalid JSON"
            exit 1
        fi
    fi
done

echo "🎉 All validations passed!"
EOF

chmod +x scripts/validate-patterns.sh

# Run validation
echo "🔍 Running validation..."
./scripts/validate-patterns.sh

echo ""
echo "🎉 Pattern synchronization completed!"
echo "📋 Summary:"
echo "   - Workflows updated from patterns repository"
echo "   - Templates synchronized"
echo "   - Configurations updated"
echo "   - Validation script created"
echo ""
echo "📝 Next steps:"
echo "   1. Review the changes with 'git diff'"
echo "   2. Test the CI/CD pipeline"
echo "   3. Commit and push the updates"
echo ""
echo "🔄 To sync again: ./scripts/sync-patterns.sh $PATTERNS_VERSION"
