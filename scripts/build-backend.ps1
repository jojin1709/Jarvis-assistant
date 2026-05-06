$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$venvPython = Join-Path $backend ".venv\Scripts\python.exe"
$dist = Join-Path $root "backend-dist"

if (-not (Test-Path $venvPython)) {
  & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "setup-backend.ps1")
}

& $venvPython -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (Test-Path $dist) {
  Remove-Item -LiteralPath $dist -Recurse -Force
}

Push-Location $backend
& $venvPython -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name jx-jarvis-backend `
  --distpath $dist `
  --workpath (Join-Path $backend "build") `
  --specpath (Join-Path $backend "build") `
  --collect-all speech_recognition `
  --collect-all edge_tts `
  --hidden-import waitress `
  --hidden-import flask_cors `
  app\main.py
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) { exit $code }
