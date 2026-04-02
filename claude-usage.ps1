#!/usr/bin/env pwsh
# Windows launcher for claude-usage
# Requires: Windows Terminal, VS Code terminal, or any VT100-capable console
# Does NOT work in plain cmd.exe (no ANSI support)

$env:PYTHONIOENCODING = "utf-8"
python "$HOME\.claude\claude-usage.py"
