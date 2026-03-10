#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="$SCRIPT_DIR/build-result.txt"

cd "$SCRIPT_DIR"
npm run build >"$OUTPUT_FILE" 2>&1
echo "EXIT:$?" >>"$OUTPUT_FILE"
