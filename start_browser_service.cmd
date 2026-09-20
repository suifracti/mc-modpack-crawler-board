@echo off
setlocal
cd /d "%~dp0"

echo [1/2] Building the browser dashboard...
where node >nul 2>nul
if errorlevel 1 goto :missing_node
where npm >nul 2>nul
if errorlevel 1 goto :missing_node

call npm.cmd --prefix apps\web run build:desktop
if errorlevel 1 goto :failed

echo [2/2] Starting the local browser service...
echo Close this window to stop the service.
call npm.cmd --prefix apps\desktop start
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo Browser service stopped with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%

:missing_node
echo.
echo Node.js and npm are required. Install Node.js LTS, then double-click this file again.
pause
exit /b 1

:failed
echo.
echo The browser dashboard could not be built. See the error above.
pause
exit /b 1
