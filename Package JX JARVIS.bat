@echo off
setlocal

cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\package-jarvis.ps1"

if errorlevel 1 (
  echo.
  echo JX JARVIS packaging stopped with an error. Read the message above, then press any key.
  pause >nul
)
