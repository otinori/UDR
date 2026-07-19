@echo off
REM UDR skills build wrapper (regenerates plugins\udr\skills and plugins\udr\
REM deploy files from .claude\skills / .claude\deploy via build.ps1). Requires
REM PowerShell 7+ (pwsh).
setlocal
where pwsh >nul 2>nul
if errorlevel 1 goto nopwsh
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" %*
exit /b %ERRORLEVEL%
:nopwsh
echo [ERROR] PowerShell 7+ (pwsh) not found. Install: https://aka.ms/powershell
echo         or run: pwsh -File "%~dp0build.ps1"
exit /b 1
