@echo off
rem *** This file MUST use Windows CRLF line endings ***
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PIP_DISABLE_PIP_VERSION_CHECK=1"
set "ROOT=%cd%"
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "BACKEND_PORT=9000"
set "FRONTEND_URL=http://127.0.0.1:5273/"
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

set "PYEXE="
if exist "%BACKEND%\.venv\Scripts\python.exe" set "PYEXE=%BACKEND%\.venv\Scripts\python.exe"
if not defined PYEXE if exist "%BACKEND%\.venv\bin\python.exe" set "PYEXE=%BACKEND%\.venv\bin\python.exe"
if not defined PYEXE (
  set "VENVCMD="
  where py >nul 2>&1
  if not errorlevel 1 set "VENVCMD=py -3.13 -m venv .venv"
  if not defined VENVCMD (
    where python >nul 2>&1
    if errorlevel 1 (
      echo [ERROR] Python not found. Install from https://www.python.org/ or run: py -3.13 -m venv backend\.venv
      goto fail
    )
    set "VENVCMD=python -m venv .venv"
  )
  echo [0/5] Creating backend\.venv ...
  pushd "%BACKEND%"
  call %VENVCMD%
  if errorlevel 1 (
    popd
    echo [ERROR] Failed to create .venv in %BACKEND%
    goto fail
  )
  popd
  if exist "%BACKEND%\.venv\Scripts\python.exe" set "PYEXE=%BACKEND%\.venv\Scripts\python.exe"
  if not defined PYEXE if exist "%BACKEND%\.venv\bin\python.exe" set "PYEXE=%BACKEND%\.venv\bin\python.exe"
  if not defined PYEXE (
    echo [ERROR] .venv created but python.exe not found
    goto fail
  )
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm not found. Install Node.js from https://nodejs.org/
  goto fail
)

where curl >nul 2>&1
if errorlevel 1 set "NO_CURL=1"

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

echo [2/5] pip install ...
"%PYEXE%" -m pip install -r "%BACKEND%\requirements.txt" -q
if errorlevel 1 (
  echo [ERROR] pip install failed
  goto fail
)

echo [3/5] backend port ...
call :pick_backend_port
if "!SKIP_BACKEND!"=="1" goto backend_skip

call :write_frontend_env
if exist "C:\msys64\ucrt64\bin" set "PATH=C:\msys64\ucrt64\bin;%PATH%"
if exist "H:\Dev\msys2\ucrt64\bin" set "PATH=H:\Dev\msys2\ucrt64\bin;%PATH%"
echo       starting backend on port !BACKEND_PORT! ...
start "ALP-Backend" /D "%BACKEND%" cmd /k ""%PYEXE%" -m uvicorn main:app --reload --host 127.0.0.1 --port !BACKEND_PORT!"
goto start_frontend

:backend_skip
echo       backend already running on port !BACKEND_PORT!
call :write_frontend_env

:start_frontend
echo [4/5] starting frontend ...
start "ALP-Frontend" /D "%FRONTEND%" cmd /k "npm run dev"

set "BACKEND_URL=http://127.0.0.1:!BACKEND_PORT!"
set "HEALTH_URL=!BACKEND_URL!/api/health"

if defined NO_CURL (
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
start "" "%FRONTEND_URL%"

echo.
echo Done. Keep these windows open:
echo   ALP-Backend   !BACKEND_URL!
echo   ALP-Frontend  %FRONTEND_URL%
echo.
call :sleep 4
goto ok

:pick_backend_port
set "SKIP_BACKEND=0"
for %%P in (9000 9010 9080) do call :scan_port %%P
if "!SKIP_BACKEND!"=="1" exit /b 0

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

:fail
echo.
pause
endlocal
exit /b 1

:ok
endlocal
exit /b 0
