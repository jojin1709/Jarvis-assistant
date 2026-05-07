@echo off
setlocal

cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-jarvis-oneclick.ps1"

if errorlevel 1 (
  echo.
  echo JX JARVIS stopped with an error. Read the message above, then press any key.
  pause >nul
)
