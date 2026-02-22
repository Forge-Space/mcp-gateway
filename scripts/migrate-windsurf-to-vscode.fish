#!/usr/bin/env fish
# Wrapper fish para o migrador Windsurf -> VS Code
# Uso:
#   migrate-windsurf-to-vscode.fish --dry-run

set SCRIPT_DIR (dirname (realpath (status -f)))
python3 "$SCRIPT_DIR/migrate-windsurf-to-vscode.py" $argv
