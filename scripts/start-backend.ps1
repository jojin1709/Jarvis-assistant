$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$venvPython = Join-Path $backend ".venv\Scripts\python.exe"

Push-Location $backend
if (Test-Path $venvPython) {
  & $venvPython -m app.main
} else {
  py -3 -m app.main
}
Pop-Location
