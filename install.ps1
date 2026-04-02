# install.ps1 — copy claude-usage into $HOME\.claude\
# Windows installer (PowerShell)

$dest = Join-Path $HOME ".claude"
$src  = $PSScriptRoot

Copy-Item "$src\claude-usage.py"  "$dest\claude-usage.py"  -Force
Copy-Item "$src\claude-usage.ps1" "$dest\claude-usage.ps1" -Force

Write-Host "Installed to $dest"
Write-Host "Run: pwsh `$HOME\.claude\claude-usage.ps1"
Write-Host ""
Write-Host "Note: requires Windows Terminal or VS Code terminal for color output."
Write-Host "Plain cmd.exe does not support ANSI colors."
