#!/bin/bash

# Generate inventory of duplicate files and configurations
set -euo pipefail

PROJECT_NAME=${1:-"forge-mcp-gateway"}
OUTPUT_FILE="cleanup-inventory-${PROJECT_NAME}.json"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "🔍 Generating inventory of duplicates for ${PROJECT_NAME}..."

# Create inventory JSON
cat > "${OUTPUT_FILE}" << EOF
{
  "project": "${PROJECT_NAME}",
  "timestamp": "${TIMESTAMP}",
  "generated": "$(date)",
  "duplicates": {
EOF

# Find duplicate configuration files
echo "    \"configuration_files\": {" >> "${OUTPUT_FILE}"

# ESLint configurations
echo "      \"eslint\": {" >> "${OUTPUT_FILE}"
find . -name ".eslintrc*" -o -name "eslint.config.*" 2>/dev/null | while read file; do
    echo "        \"$(basename "$file\")\": {" >> "${OUTPUT_FILE}"
    echo "          \"path\": \"$file\"," >> "${OUTPUT_FILE}"
    echo "          \"size\": $(wc -c < "$file")," >> "${OUTPUT_FILE}"
    echo "          \"lines\": $(wc -l < "$file")" >> "${OUTPUT_FILE}"
    echo "        }," >> "${OUTPUT_FILE}"
done
echo "      }," >> "${OUTPUT_FILE}"

# Prettier configurations
echo "      \"prettier\": {" >> "${OUTPUT_FILE}"
find . -name ".prettierrc*" 2>/dev/null | while read file; do
    echo "        \"$(basename "$file\")\": {" >> "${OUTPUT_FILE}"
    echo "          \"path\": \"$file\"," >> "${OUTPUT_FILE}"
    echo "          \"size\": $(wc -c < "$file")," >> "${OUTPUT_FILE}"
    echo "          \"lines\": $(wc -l < "$file")" >> "${OUTPUT_FILE}"
    echo "        }," >> "${OUTPUT_FILE}"
done
echo "      }," >> "${OUTPUT_FILE}"

# CodeRabbit configurations
echo "      \"coderabbit\": {" >> "${OUTPUT_FILE}"
find . -name ".coderabbit*" 2>/dev/null | while read file; do
    echo "        \"$(basename "$file\")\": {" >> "${OUTPUT_FILE}"
    echo "          \"path\": \"$file\"," >> "${OUTPUT_FILE}"
    echo "          \"size\": $(wc -c < "$file")," >> "${OUTPUT_FILE}"
    echo "          \"lines\": $(wc -l < "$file")" >> "${OUTPUT_FILE}"
    echo "        }," >> "${OUTPUT_FILE}"
done
echo "      }" >> "${OUTPUT_FILE}"

echo "    }," >> "${OUTPUT_FILE}"

# Find duplicate documentation
echo "    \"documentation\": {" >> "${OUTPUT_FILE}"

# README files
echo "      \"readme_files\": [" >> "${OUTPUT_FILE}"
find . -name "README*" -type f 2>/dev/null | while read file; do
    echo "        {" >> "${OUTPUT_FILE}"
    echo "          \"name\": \"$(basename "$file")\"," >> "${OUTPUT_FILE}"
    echo "          \"path\": \"$file\"," >> "${OUTPUT_FILE}"
    echo "          \"size\": $(wc -c < "$file")," >> "${OUTPUT_FILE}"
    echo "          \"lines\": $(wc -l < "$file")" >> "${OUTPUT_FILE}"
    echo "        }," >> "${OUTPUT_FILE}"
done
echo "      ]" >> "${OUTPUT_FILE}"

echo "    }," >> "${OUTPUT_FILE}"

# Find duplicate environment files
echo "    \"environment_files\": [" >> "${OUTPUT_FILE}"
find . -name ".env*" -type f 2>/dev/null | while read file; do
    echo "      {" >> "${OUTPUT_FILE}"
    echo "        \"name\": \"$(basename "$file")\"," >> "${OUTPUT_FILE}"
    echo "        \"path\": \"$file\"," >> "${OUTPUT_FILE}"
    echo "        \"size\": $(wc -c < "$file")," >> "${OUTPUT_FILE}"
    echo "        \"lines\": $(wc -l < "$file")" >> "${OUTPUT_FILE}"
    echo "      }," >> "${OUTPUT_FILE}"
done
echo "    ]," >> "${OUTPUT_FILE}"

# Find duplicate CI/CD workflows
echo "    "ci_cd_workflows": [" >> "${OUTPUT_FILE}"
find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | while read file; do
    echo "      {" >> "${OUTPUT_FILE}"
    echo "        \"name\": \"$(basename "$file")\"," >> "${OUTPUT_FILE}"
    echo "        \"path\": \"$file\"," >> "${OUTPUT_FILE}"
    echo "        \"size\": $(wc -c < "$file")," >> "${OUTPUT_FILE}"
    echo "        \"lines\": $(wc -l < "$file")" >> "${OUTPUT_FILE}"
    echo "        \"jobs\": $(grep -c "^[[:space:]]*[a-zA-Z0-9_-]*:" "$file" 2>/dev/null || echo "0")" >> "${OUTPUT_FILE}"
    echo "      }," >> "${OUTPUT_FILE}"
done
echo "    ]," >> "${OUTPUT_FILE}"

# Find duplicate Docker files
echo "    "docker_files\": [" >> "${OUTPUT_FILE}"
find . -name "Dockerfile*" -type f 2>/dev/null | while read file; do
    echo "      {" >> "${OUTPUT_FILE}"
    echo "        \"name\": \"$(basename "$file")\"," >> "${OUTPUT_FILE}"
    echo "        \"path\": \"$file\"," >> "${OUTPUT_FILE}"
    echo "        \"size\": $(wc -c < "$file")," >> "${OUTPUT_FILE}"
    echo "        \"lines\": $(wc -l < "$file")" >> "${OUTPUT_FILE}"
    echo "        \"base_image\": \"$(grep "^FROM" "$file" | head -1 | cut -d' ' -f2- 2>/dev/null || echo "unknown")\"" >> "${OUTPUT_FILE}"
    echo "      }," >> "${OUTPUT_FILE}"
done
echo "    ]," >> "${OUTPUT_FILE}"

# Find duplicate package.json files
echo "    "package_files\": [" >> "${OUTPUT_FILE}"
find . -name "package.json" -type f 2>/dev/null | while read file; do
    echo "      {" >> "${OUTPUT_FILE}"
    echo "        \"name\": \"$(basename "$file")\"," >> "${OUTPUT_FILE}"
    echo "        \"path\": \"$file\"," >> "${OUTPUT_FILE}"
    echo "        \"size\": $(wc -c < "$file")," >> "${OUTPUT_FILE}"
    echo "        \"lines\": $(wc -l < "$file")" >> "${OUTPUT_FILE}"
    echo "        \"scripts\": $(cat "$file" 2>/dev/null | jq '.scripts | keys | length' 2>/dev/null || echo "0")" >> "${OUTPUT_FILE}"
    echo "      }," >> "${OUTPUT_FILE}"
done
echo "    ]" >> "${OUTPUT_FILE}"

echo "  }," >> "${OUTPUT_FILE}"

# Add summary statistics
echo "  \"summary\": {" >> "${OUTPUT_FILE}"
echo "    \"total_configuration_files\": $(find . -name ".*" -type f | wc -l)," >> "${OUTPUT_FILE}"
echo "    \"total_documentation_files\": $(find . -name "*.md" -type f | wc -l)," >> "${OUTPUT_FILE}"
echo "    \"total_ci_cd_files\": $(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l)," >> "${OUTPUT_FILE}"
echo "    \"total_docker_files\": $(find . -name "Dockerfile*" -type f | wc -l)," >> "${OUTPUT_FILE}"
echo "    \"total_package_files\": $(find . -name "package.json" -type f | wc -l)" >> "${OUTPUT_FILE}"
echo "  }" >> "${OUTPUT_FILE}"

echo "}" >> "${OUTPUT_FILE}"

# Clean up trailing commas
sed -i '' 's/,}/}/g' "${OUTPUT_FILE}"
sed -i '' 's/,]/]/g' "${OUTPUT_FILE}"

echo "✅ Duplicate inventory generated!"
echo "📍 Location: ${OUTPUT_FILE}"
echo ""
echo "📊 Summary:"
echo "- Configuration files: $(find . -name ".*" -type f | wc -l)"
echo "- Documentation files: $(find . -name "*.md" -type f | wc -l)"
echo "- CI/CD workflows: $(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l)"
echo "- Docker files: $(find . -name "Dockerfile*" -type f | wc -l)"
echo "- Package files: $(find . -name "package.json" -type f | wc -l)"

# Also create a human-readable summary
cat > "cleanup-inventory-${PROJECT_NAME}-summary.md" << EOF
# Duplicate Inventory Summary: ${PROJECT_NAME}

**Generated:** $(date)
**Timestamp:** ${TIMESTAMP}

## 📊 File Counts

| Category | Count | Details |
|-----------|-------|---------|
| Configuration Files | $(find . -name ".*" -type f | wc -l) | ESLint, Prettier, CodeRabbit, etc. |
| Documentation Files | $(find . -name "*.md" -type f | wc -l) | README, docs, guides |
| CI/CD Workflows | $(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l) | GitHub Actions |
| Docker Files | $(find . -name "Dockerfile*" -type f | wc -l) | Dockerfile variants |
| Package Files | $(find . -name "package.json" -type f | wc -l) | package.json files |

## 🔍 Potential Duplicates

### Configuration Files
\`\`\`
$(find . -name ".eslintrc*" -o -name "eslint.config.*" -o -name ".prettierrc*" -o -name ".coderabbit*" 2>/dev/null | sort)
\`\`\`

### Documentation Files
\`\`\`
$(find . -name "README*" -o -name "*.md" | sort | uniq -d)
\`\`\`

### Environment Files
\`\`\`
$(find . -name ".env*" | sort)
\`\`\`

## 📋 Next Steps

1. Review the detailed JSON inventory: \`${OUTPUT_FILE}\`
2. Identify specific duplicates to remove
3. Create cleanup plan for each category
4. Execute cleanup with proper validation

---

**Inventory completed at:** $(date)
EOF

echo "📄 Summary created: cleanup-inventory-${PROJECT_NAME}-summary.md"
