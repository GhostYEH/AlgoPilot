@echo off
rem *** This file MUST use Windows CRLF line endings ***
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PIP_DISABLE_PIP_VERSION_CHECK=1"
set "ROOT=%cd%"
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "RUNTIME=%ROOT%\runtime"
set "BACKEND_PORT=9000"
set "FRONTEND_URL=http://127.0.0.1:5173/"
set "SKIP_BACKEND=0"
set "CURL_OPTS=-sf --connect-timeout 2 --max-time 5"

echo.
echo ============================================
echo   Algorithm Learning Platform - Start
echo ============================================
echo.

if not exist "%FRONTEND%\package.json" (
  echo [ERROR] Frontend not found:
  echo   %FRONTEND%
  goto fail
)

if not exist "%BACKEND%\main.py" (
  echo [ERROR] Backend not found:
  echo   %BACKEND%
  goto fail
)

rem ---- Use bundled portable runtimes ----
set "PYEXE=%RUNTIME%\python\python.exe"
set "NODE_DIR=%RUNTIME%\nodejs"

if not exist "!PYEXE!" (
  echo [ERROR] Portable Python not found at:
  echo   !PYEXE!
  goto fail
)
if not exist "!NODE_DIR!\node.exe" (
  echo [ERROR] Portable Node.js not found at:
  echo   !NODE_DIR!\node.exe
  goto fail
)

rem ---- Add portable Node.js to PATH ----
set "PATH=!NODE_DIR!;!PATH!"

rem ---- Frontend dependencies ----
if not exist "%FRONTEND%\node_modules\.bin\vite.cmd" (
  echo [1/5] npm install ...
  pushd "%FRONTEND%"
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed
    goto fail
  )
  popd
  if not exist "%FRONTEND%\node_modules\.bin\vite.cmd" (
    echo [ERROR] vite not found after npm install
    goto fail
  )
) else (
  echo [1/5] frontend deps OK
)

rem ---- Python backend dependencies ----
echo [2/5] pip install ...
"!PYEXE!" -m pip install -r "%BACKEND%\requirements.txt" -q --no-warn-script-location
if errorlevel 1 (
  echo [ERROR] pip install failed
  goto fail
)

rem ---- Check port availability ----
echo [3/5] backend port ...
call :pick_backend_port
if "!SKIP_BACKEND!"=="1" goto backend_skip

call :write_frontend_env
echo       starting backend on port !BACKEND_PORT! ...
start "" /B /D "%BACKEND%" "!PYEXE!" -m uvicorn main:app --reload --host 127.0.0.1 --port !BACKEND_PORT!
goto start_frontend

:backend_skip
echo       backend already running on port !BACKEND_PORT!
call :write_frontend_env

:start_frontend
echo [4/5] starting frontend ...
start "" /B /D "%FRONTEND%" cmd /d /c "npm run dev"

set "BACKEND_URL=http://127.0.0.1:!BACKEND_PORT!"
set "HEALTH_URL=!BACKEND_URL!/api/health"

where curl >nul 2>&1
if errorlevel 1 (
  echo [5/5] waiting 15s then opening browser ...
  call :sleep 15
  goto open_browser
)

echo [5/5] waiting for services ...
set /a WAIT=0
:wait_backend
if "!SKIP_BACKEND!"=="1" goto backend_ready
set /a WAIT+=1
if !WAIT! GTR 40 (
  echo [WARN] backend slow, continuing ...
  goto wait_frontend
)
curl !CURL_OPTS! "!HEALTH_URL!" >nul 2>&1
if errorlevel 1 (
  call :sleep 2
  goto wait_backend
)
:backend_ready
echo       backend OK  !BACKEND_URL!

set /a WAIT=0
:wait_frontend
set /a WAIT+=1
if !WAIT! GTR 40 goto open_browser
curl !CURL_OPTS! "%FRONTEND_URL%" >nul 2>&1
if errorlevel 1 (
  call :sleep 2
  goto wait_frontend
)
echo       frontend OK

:open_browser
echo       browser auto-open disabled

echo.
echo Done. Services are running in this window:
echo   Backend   !BACKEND_URL!
echo   Frontend  %FRONTEND_URL%
echo Press Ctrl+C or close this window to stop both services.
echo.
goto keep_running

:pick_backend_port
set "SKIP_BACKEND=0"
for %%P in (9000 9010 9080) do call :scan_port %%P
if "!SKIP_BACKEND!"=="1" exit /b 0

where curl >nul 2>&1
if errorlevel 1 exit /b 0

netstat -ano | findstr ":9000 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  set "BACKEND_PORT=9010"
  echo       port 9000 busy, using 9010
) else (
  set "BACKEND_PORT=9000"
)
exit /b 0

:scan_port
if "!SKIP_BACKEND!"=="1" exit /b 0
set "SCAN_PORT=%~1"
call :backend_ready_check !SCAN_PORT!
if not errorlevel 1 (
  set "BACKEND_PORT=!SCAN_PORT!"
  set "SKIP_BACKEND=1"
  exit /b 0
)
exit /b 0

:backend_ready_check
set "CHK_PORT=%~1"
where curl >nul 2>&1
if errorlevel 1 exit /b 1
curl !CURL_OPTS! "http://127.0.0.1:!CHK_PORT!/api/health" >nul 2>&1
if errorlevel 1 exit /b 1
exit /b 0

:write_frontend_env
if "!BACKEND_PORT!"=="9000" (
  if exist "%FRONTEND%\.env.development.local" del /f /q "%FRONTEND%\.env.development.local" >nul 2>&1
) else (
  echo VITE_BACKEND_PORT=!BACKEND_PORT!> "%FRONTEND%\.env.development.local"
  echo       vite proxy -^> port !BACKEND_PORT!
)
exit /b 0

:sleep
set /a "_PINGS=%~1+1"
ping -n !_PINGS! 127.0.0.1 >nul 2>&1
exit /b 0

:keep_running
call :sleep 60
goto keep_running

:fail
echo.
pause
endlocal
exit /b 1

:ok
endlocal
exit /b 0
