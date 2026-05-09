$ErrorActionPreference = "Stop"

try {
  $Host.UI.RawUI.WindowTitle = "JX JARVIS Desktop Installer"
} catch {
  # Some hosts do not allow setting the title.
}

$root = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $root "scripts\start-jarvis-oneclick.ps1"
$icon = Join-Path $root "assets\jx-jarvis.ico"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Start JX JARVIS.lnk"
$powershell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

if (-not (Test-Path $launcher)) {
  throw "Launcher not found: $launcher"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $powershell
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$launcher`""
$shortcut.WorkingDirectory = $root
$shortcut.WindowStyle = 1
$shortcut.Description = "Start JX JARVIS"
if (Test-Path $icon) {
  $shortcut.IconLocation = $icon
}
$shortcut.Save()

Write-Host ""
Write-Host "JX JARVIS desktop shortcut installed:" -ForegroundColor Green
Write-Host $shortcutPath
Write-Host ""
Write-Host "Double-click Start JX JARVIS on the Desktop. The launcher installs missing dependencies, prepares the backend, and opens the app."
