#!/bin/bash
set -euo pipefail

if command -v pre-commit >/dev/null 2>&1; then
    echo "pre-commit is available"
else
    if [ -f "/opt/homebrew/bin/pre-commit" ]; then
        export PATH="/opt/homebrew/bin:$PATH"
    else
        echo "pre-commit not found. Install: brew install pre-commit"
        exit 1
    fi
fi

pre-commit install
pre-commit --version
echo "Pre-commit setup complete!"
