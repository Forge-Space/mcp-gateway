#!/bin/bash
# Setup script for Core Package NPM Deployment
# This script helps configure all necessary components for automated NPM publishing

set -e

echo "🚀 Setting up Core Package NPM Deployment"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if we're in the right directory
    if [ ! -f "package.json" ]; then
        print_error "package.json not found. Please run this script from the project root."
        exit 1
    fi

    # Check if this is the core package
    PACKAGE_NAME=$(jq -r '.name' package.json 2>/dev/null || echo "unknown")
    if [[ "$PACKAGE_NAME" != "@forge-mcp-gateway/client" ]]; then
        print_warning "This script is designed for @forge-mcp-gateway/client package"
        echo "Current package: $PACKAGE_NAME"
        read -p "Continue anyway? (y/N): " -n -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Check if GitHub CLI is installed
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed"
        echo "Install it with: brew install gh or npm install -g @github/cli/cli"
        exit 1
    fi

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is not installed"
        echo "Install it with: brew install jq or sudo apt-get install jq"
        exit 1
    fi

    print_status "Prerequisites check passed"
}

# Setup NPM token
setup_npm_token() {
    print_info "Setting up NPM token..."

    if [ -z "$NPM_TOKEN" ]; then
        echo "NPM_TOKEN environment variable not set."
        echo "You can:"
        echo "1. Set it as a repository secret (recommended):"
        echo "   - Go to GitHub repository > Settings > Secrets and variables > Actions"
        echo "   - Add NPM_TOKEN with your NPM automation token"
        echo "2. Set it temporarily:"
        echo "   export NPM_TOKEN=your_npm_token_here"
        echo "3. Use npm login: npm login"
        echo ""
        echo "For automated publishing, option 1 (repository secret) is recommended."
        read -p "Press Enter to continue or Ctrl+C to exit..."
    fi

    print_status "NPM token setup complete"
}

# Create release branch
create_release_branch() {
    print_info "Setting up release branch..."

    # Check if release/core branch exists
    if git branch --list | grep -q "release/core"; then
        print_status "release/core branch already exists"
    else
        print_info "Creating release/core branch..."
        git checkout -b release/core main
        git push -u origin release/core
        print_status "release/core branch created and pushed"
    fi
}

# Setup GitHub workflows
setup_workflows() {
    print_info "Setting up GitHub workflows..."

    # Check if workflows exist
    if [ ! -f ".github/workflows/npm-release-core.yml" ]; then
        print_error "npm-release-core.yml workflow not found"
        exit 1
    fi

    if [ ! -f ".github/workflows/branch-protection-core.yml" ]; then
        print_error "branch-protection-core.yml workflow not found"
        exit 1
    fi

    print_status "GitHub workflows are in place"
}

# Configure package.json for publishing
configure_package_json() {
    print_info "Configuring package.json for publishing..."

    # Check if publish script exists
    if ! jq -e '.scripts.publish' package.json > /dev/null; then
        print_warning "No publish script found in package.json"
        print_info "Adding publish script..."

        # Add publish script
        jq '.scripts.publish = "npm publish --access public"' package.json > package.json.tmp && \
        mv package.json.tmp package.json

        print_status "Added publish script to package.json"
    else
        print_status "Publish script already exists"
    fi

    # Check if prepack script exists
    if ! jq -e '.scripts.prepack' package.json > /dev/null; then
        print_warning "No prepack script found in package.json"
        print_info "Adding prepack script..."

        # Add prepack script
        jq '.scripts.prepack = "npm run build"' package.json > package.json.tmp && \
        mv package.json.tmp package.json

        print_status "Added prepack script to package.json"
    else
        print_status "Prepack script already exists"
    fi

    # Validate package.json fields
    print_info "Validating package.json fields..."

    REQUIRED_FIELDS=("name" "version" "description" "main" "keywords" "author" "license" "repository")
    MISSING_FIELDS=()

    for field in "${REQUIRED_FIELDS[@]}"; do
        if ! jq -e ".$field" package.json > /dev/null; then
            MISSING_FIELDS+=("$field")
        fi
    done

    if [ ${#MISSING_FIELDS[@]} -gt 0 ]; then
        print_error "Missing required fields in package.json: ${MISSING_FIELDS[*]}"
        exit 1
    fi

    print_status "package.json validation passed"
}

# Create .npmignore
create_npmignore() {
    print_info "Creating .npmignore..."

    if [ ! -f ".npmignore" ]; then
        cat > .npmignore << 'EOF'
# Dependencies
node_modules/
npm-debug.log*
yarn-error.log*
yarn.lock

# Build outputs
build/
dist/
*.tsbuildinfo

# Environment files
.env
.env.*
!.env.example

# Test files
test/
tests/
**/*.test.ts
**/*.spec.ts

# Documentation
docs/
*.md
!README.md

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
logs/
EOF
        print_status "Created .npmignore file"
    else
        print_status ".npmignore already exists"
    fi
}

# Setup GitHub secrets guide
setup_secrets_guide() {
    print_info "GitHub Secrets Setup Guide"
    echo ""
    echo "🔐 Required GitHub Secrets:"
    echo "1. NPM_TOKEN - Your NPM automation token"
    echo "   - Generate at: https://www.npmjs.com/settings/tokens"
    echo "   - Scope: automation"
    echo "   - Add to repository secrets"
    echo ""
    echo "2. GITHUB_TOKEN - GitHub token (for API calls)"
    echo "   - Usually automatically provided by GitHub Actions"
    echo "   - Ensure it has 'repo' scope"
    echo ""
    echo "📋 Setup Steps:"
    echo "1. Go to your repository on GitHub"
    echo "2. Navigate to Settings > Secrets and variables > Actions"
    echo "3. Click 'New repository secret'"
    echo "4. Name: NPM_TOKEN"
    echo "5. Value: your_npm_automation_token"
    echo "6. Click 'Add secret'"
    echo ""
    echo "🔒 Security Note:"
    echo "- Never commit tokens to your repository"
    echo "- Use repository secrets for automated workflows"
    echo "- Rotate tokens regularly"
}

# Test the setup
test_setup() {
    print_info "Testing the setup..."

    # Test build
    echo "Testing build..."
    if npm run build; then
        print_status "Build test passed"
    else
        print_error "Build test failed"
        exit 1
    fi

    # Test dry run publish
    echo "Testing dry run publish..."
    if npm pack --dry-run; then
        print_status "Dry run publish test passed"
    else
        print_error "Dry run publish test failed"
        exit 1
    fi

    print_status "All tests passed! 🎉"
}

# Main setup function
main() {
    echo "📦 Core Package NPM Deployment Setup"
    echo "=================================="
    echo ""

    check_prerequisites
    setup_npm_token
    create_release_branch
    setup_workflows
    configure_package_json
    create_npmignore
    setup_secrets_guide

    echo ""
    print_status "Setup complete! 🎉"
    echo ""
    print_info "Next steps:"
    echo "1. Push your changes to main branch"
    echo "2. Create a pull request to merge into release/core"
    echo "3. The workflow will automatically:"
    echo "   - Validate the package"
    echo "   - Run security and quality checks"
    echo "   - Test the package locally"
    "   - Publish to NPM"
    echo "   - Create a GitHub release"
    echo "   - Update documentation"
    echo ""
    print_info "Manual publishing (if needed):"
    echo "npm run build"
    echo "npm publish"
    echo ""
    echo "📚 For more information, see the workflow documentation:"
    echo "   - .github/workflows/npm-release-core.yml"
    echo "   - .github/workflows/branch-protection-core.yml"
}

# Run main function
main "$@"
