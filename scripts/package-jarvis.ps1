$ErrorActionPreference = "Stop"

try {
  $Host.UI.RawUI.WindowTitle = "JX JARVIS Packager"
} catch {
  # Some hosts do not allow setting the title.
}

$root = Split-Path -Parent $PSScriptRoot
$release = Join-Path $root "release"

function Write-Step($message) {
  Write-Host ""
  Write-Host "==> $message" -ForegroundColor Cyan
}

Set-Location $root

Write-Host "Packaging JX JARVIS from: $root" -ForegroundColor Green

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  throw "Node.js was not found. Install Node.js LTS first."
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
  throw "npm was not found. Reinstall Node.js LTS with npm enabled."
}

if (-not (Test-Path (Join-Path $root "node_modules"))) {
  Write-Step "Installing desktop dependencies"
  & npm.cmd install
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not (Test-Path (Join-Path $root "frontend\node_modules"))) {
  Write-Step "Installing frontend dependencies"
  & npm.cmd --prefix frontend install
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not (Test-Path (Join-Path $root "backend\.venv\Scripts\python.exe"))) {
  Write-Step "Setting up backend environment"
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "scripts\setup-backend.ps1")
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Step "Building installer"
& npm.cmd run dist
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Installer output:" -ForegroundColor Green
Get-ChildItem $release -Filter "*.exe" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5 FullName
