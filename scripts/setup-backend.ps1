$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$venv = Join-Path $backend ".venv"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
  py -3 -m venv $venv
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m pip install -r (Join-Path $backend "requirements.txt")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
