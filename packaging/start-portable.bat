@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title AlgoPilot Server

set "APP_EXE=%CD%\AlgoPilot.exe"
if not exist "%APP_EXE%" (
  echo [ERROR] AlgoPilot.exe was not found.
  echo Please keep this BAT file beside AlgoPilot.exe and the data, mingw,
  echo and _internal folders.
  goto failed
)

rem If an instance is already running, open it and keep this window visible.
for %%P in (8000 8001 8010 8080) do (
  call :health_check %%P
  if not errorlevel 1 (
    echo AlgoPilot is already running at http://127.0.0.1:%%P/
    if not defined ALGOPILOT_NO_BROWSER start "" "http://127.0.0.1:%%P/"
    echo You may close this window.
    pause
    exit /b 0
  )
)

set "ALGOPILOT_PORT="
for %%P in (8000 8001 8010 8080) do (
  if not defined ALGOPILOT_PORT (
    netstat -ano -p tcp 2>nul | findstr /R /C:":%%P .*LISTENING" >nul
    if errorlevel 1 set "ALGOPILOT_PORT=%%P"
  )
)
if not defined ALGOPILOT_PORT (
  echo [ERROR] Ports 8000, 8001, 8010 and 8080 are all in use.
  goto failed
)

set "APP_URL=http://127.0.0.1:!ALGOPILOT_PORT!/"
echo.
echo Starting AlgoPilot at !APP_URL!
echo Keep this window open while using the application.
echo Press Ctrl+C or close this window to stop AlgoPilot.
echo.

rem Wait in the background and open the browser after the server is healthy.
if not defined ALGOPILOT_NO_BROWSER start "" /b powershell.exe -NoLogo -NoProfile -WindowStyle Hidden -Command "$u='!APP_URL!api/health'; for($i=0;$i -lt 180;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 2; if($r.StatusCode -eq 200){ Start-Process '!APP_URL!'; exit 0 } } catch {}; Start-Sleep -Seconds 1 }; exit 1" >nul 2>&1

rem Run in this window. If the application exits, the error remains visible.
"%APP_EXE%"
set "APP_EXIT=!ERRORLEVEL!"
echo.
echo AlgoPilot stopped with exit code !APP_EXIT!.
echo If this was unexpected, take a screenshot of the messages above.
pause
exit /b !APP_EXIT!

:failed
echo.
echo Startup failed. This window will remain open so you can read the error.
pause
exit /b 1

:health_check
set "CHECK_URL=http://127.0.0.1:%~1/api/health"
where curl.exe >nul 2>&1
if not errorlevel 1 (
  curl.exe -fsS --connect-timeout 2 --max-time 4 "%CHECK_URL%" >nul 2>&1
  exit /b !ERRORLEVEL!
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing -Uri '%CHECK_URL%' -TimeoutSec 4; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; exit 1" >nul 2>&1
exit /b !ERRORLEVEL!
