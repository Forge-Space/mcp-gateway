#!/usr/bin/env bash
# Enable and trigger Renovate for dependency updates

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Renovate Setup for forge-mcp-gateway ===${NC}\n"

# Check if Renovate config exists
if [ ! -f "$REPO_ROOT/.github/renovate.json" ]; then
    echo -e "${RED}Error: Renovate configuration not found at .github/renovate.json${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Renovate configuration found"

# Validate Renovate config
echo -e "\n${BLUE}Validating Renovate configuration...${NC}"
if command -v npx &> /dev/null; then
    if npx --yes renovate-config-validator "$REPO_ROOT/.github/renovate.json" 2>&1 | grep -q "Config validated successfully"; then
        echo -e "${GREEN}✓${NC} Configuration is valid"
    else
        echo -e "${YELLOW}⚠${NC}  Could not validate configuration (this is okay)"
    fi
else
    echo -e "${YELLOW}⚠${NC}  npx not available, skipping validation"
fi

# Show current outdated dependencies
echo -e "\n${BLUE}Checking for outdated dependencies...${NC}"

echo -e "\n${YELLOW}NPM Dependencies:${NC}"
if command -v npm &> /dev/null; then
    npm outdated || echo "  All npm dependencies are up to date"
else
    echo "  npm not available"
fi

# Instructions for enabling Renovate
echo -e "\n${BLUE}=== How to Enable Renovate ===${NC}\n"

echo -e "${YELLOW}Option 1: GitHub App (Recommended)${NC}"
echo "1. Visit: https://github.com/apps/renovate"
echo "2. Click 'Install' or 'Configure'"
echo "3. Select 'LucasSantana-Dev' account"
echo "4. Choose 'Only select repositories'"
echo "5. Select 'forge-mcp-gateway'"
echo "6. Click 'Install' or 'Save'"
echo ""
echo "After installation, Renovate will:"
echo "  - Create an onboarding PR within minutes"
echo "  - Scan for dependency updates"
echo "  - Create PRs based on the schedule (Mondays before 3am UTC)"

echo -e "\n${YELLOW}Option 2: Trigger Manually${NC}"
echo "Create an empty commit to trigger Renovate scan:"
echo "  git commit --allow-empty -m 'chore: trigger renovate scan'"
echo "  git push origin main"

echo -e "\n${YELLOW}Option 3: Self-Hosted${NC}"
echo "Run Renovate locally (requires GITHUB_TOKEN):"
echo "  npm install -g renovate"
echo "  export GITHUB_TOKEN='your_token'"
echo "  renovate --platform=github LucasSantana-Dev/forge-mcp-gateway"

# Offer to create trigger commit
echo -e "\n${BLUE}=== Quick Actions ===${NC}\n"
read -p "Create an empty commit to trigger Renovate? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Creating trigger commit...${NC}"
    git commit --allow-empty -m "chore: trigger renovate scan"

    read -p "Push to origin/main? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin main
        echo -e "${GREEN}✓${NC} Pushed to origin/main"
        echo -e "\n${GREEN}Renovate should scan the repository within a few minutes.${NC}"
        echo -e "Check: https://github.com/LucasSantana-Dev/forge-mcp-gateway/pulls"
    else
        echo -e "${YELLOW}Commit created but not pushed.${NC}"
        echo "Push manually with: git push origin main"
    fi
else
    echo -e "${YELLOW}No commit created.${NC}"
fi

echo -e "\n${BLUE}=== Next Steps ===${NC}\n"
echo "1. Ensure Renovate GitHub App is installed (Option 1 above)"
echo "2. Wait for onboarding PR or dependency update PRs"
echo "3. Review and merge PRs as they arrive"
echo "4. Check Renovate dashboard: https://app.renovatebot.com/dashboard"
echo ""
echo -e "${GREEN}For detailed setup instructions, see:${NC}"
echo "  docs/setup/RENOVATE_SETUP.md"
