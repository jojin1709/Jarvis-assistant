$ErrorActionPreference = "Stop"

try {
  $Host.UI.RawUI.WindowTitle = "JX JARVIS Launcher"
} catch {
  # Some hosts do not allow setting the title.
}

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"
$envExample = Join-Path $root ".env.example"
$rootNodeModules = Join-Path $root "node_modules"
$frontendNodeModules = Join-Path $root "frontend\node_modules"
$backendPython = Join-Path $root "backend\.venv\Scripts\python.exe"

function Write-Step($message) {
  Write-Host ""
  Write-Host "==> $message" -ForegroundColor Cyan
}

function Stop-WithHelp($message) {
  Write-Host ""
  Write-Host $message -ForegroundColor Red
  Write-Host ""
  Write-Host "Press any key to close this window."
  $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
  exit 1
}

function Test-Command($name) {
  return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

Set-Location $root

Write-Host "Starting JX JARVIS from: $root" -ForegroundColor Green

if (-not (Test-Command "node")) {
  Stop-WithHelp "Node.js was not found. Install Node.js LTS, then double-click Start JX JARVIS again."
}

if (-not (Test-Command "npm.cmd")) {
  Stop-WithHelp "npm was not found. Reinstall Node.js LTS with npm enabled, then try again."
}

if (-not (Test-Path $envFile)) {
  if (Test-Path $envExample) {
    Copy-Item $envExample $envFile
    Stop-WithHelp ".env was created for you. Open it, add your GROQ_API_KEY, then start JX JARVIS again."
  }

  Stop-WithHelp ".env is missing. Create it with GROQ_API_KEY before starting JX JARVIS."
}

$envContent = Get-Content $envFile -Raw
if ($envContent -notmatch "(?m)^GROQ_API_KEY\s*=\s*\S+" -or $envContent -match "(?m)^GROQ_API_KEY\s*=\s*your_real_groq_api_key_here\s*$") {
  Stop-WithHelp "GROQ_API_KEY is missing in .env. Add your Groq key so JX JARVIS can answer commands."
}

if (-not (Test-Path $rootNodeModules)) {
  Write-Step "Installing desktop app dependencies"
  & npm.cmd install
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not (Test-Path $frontendNodeModules)) {
  Write-Step "Installing frontend dependencies"
  & npm.cmd --prefix frontend install
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not (Test-Path $backendPython)) {
  if (-not (Test-Command "py")) {
    Stop-WithHelp "Python launcher was not found. Install Python 3.11 or newer, then start JX JARVIS again."
  }

  Write-Step "Setting up Python voice/backend environment"
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "scripts\setup-backend.ps1")
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Step "Launching JX JARVIS"
Write-Host "When the window opens, use 'Hey Jarvis', the Speak button, or the text command bar." -ForegroundColor Gray
Write-Host ""

& npm.cmd run dev
exit $LASTEXITCODE
