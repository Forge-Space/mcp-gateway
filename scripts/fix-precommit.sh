#!/bin/bash

# Fix pre-commit installation and configuration
set -euo pipefail

echo "🔧 Fixing pre-commit installation..."

# Check if pre-commit is available
if command -v pre-commit >/dev/null 2>&1; then
    echo "✅ pre-commit is available"
else
    echo "❌ pre-commit not found in PATH"
    echo "📍 Trying common installation paths..."

    # Check homebrew installation
    if [ -f "/opt/homebrew/bin/pre-commit" ]; then
        echo "🍺 Found pre-commit via homebrew, adding to PATH..."
        export PATH="/opt/homebrew/bin:$PATH"
        echo "PATH updated: $PATH"
    else
        echo "❌ pre-commit not found, please install it first:"
        echo "   brew install pre-commit"
        echo "   or"
        echo "   pip install pre-commit"
        exit 1
    fi
fi

# Install pre-commit hooks
echo "📦 Installing pre-commit hooks..."
pre-commit install

# Test pre-commit
echo "🧪 Testing pre-commit..."
pre-commit --version

echo "✅ Pre-commit setup complete!"
