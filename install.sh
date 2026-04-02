#!/usr/bin/env bash
# install.sh — copy claude-usage into ~/.claude/
# Works on macOS, Linux, and Windows (Git Bash / WSL)

set -e

DEST="$HOME/.claude"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$SCRIPT_DIR/claude-usage.py" "$DEST/claude-usage.py"
cp "$SCRIPT_DIR/claude-usage.sh" "$DEST/claude-usage.sh"
chmod +x "$DEST/claude-usage.sh"

echo "Installed to $DEST"
echo "Run: bash ~/.claude/claude-usage.sh"
