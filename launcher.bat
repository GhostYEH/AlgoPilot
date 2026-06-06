@echo off
chcp 65001 >nul 2>&1
title AlgoPilot

set "DIR=%~dp0"
if "%DIR:~-1%"=="\" set "DIR=%DIR:~0,-1%"

:: Set working directory to exe location (ensures .env / data/ paths work)
cd /d "%DIR%"

echo ============================================================
echo   AlgoPilot - Algorithm Intelligent Learning Platform
echo ============================================================
echo.

:: Add portable MinGW to PATH for OJ and Trace
if exist "%DIR%\_internal\mingw\bin" (
    set "PATH=%DIR%\_internal\mingw\bin;%PATH%"
    echo   [OK] MinGW loaded
) else if exist "%DIR%\mingw\bin" (
    set "PATH=%DIR%\mingw\bin;%PATH%"
    echo   [OK] MinGW loaded
) else (
    echo   [WARN] MinGW not found, C++ judge and trace unavailable
)

:: Create .env on first run
if not exist "%DIR%\.env" (
    if exist "%DIR%\.env.example" (
        copy "%DIR%\.env.example" "%DIR%\.env" >nul 2>&1
        echo   [INFO] .env created from .env.example
    )
)

:: Ensure data directory exists
if not exist "%DIR%\data" mkdir "%DIR%\data"

:: Check if port 8000 is already in use; if so, kill the process
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [WARN] Port 8000 is already in use, attempting to free it ...
    for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%P >nul 2>&1
    )
    timeout /t 2 /nobreak >nul 2>&1
    netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo   [ERROR] Port 8000 still in use. Please close the conflicting program and retry.
        pause
        exit /b 1
    )
    echo   [OK] Port 8000 freed
)

echo.
echo   Starting server ...
echo   Browser will open http://127.0.0.1:8000 in a few seconds
echo.

:: Open browser after delay
powershell -Command "Start-Sleep -Seconds 4; Start-Process 'http://127.0.0.1:8000'" >nul 2>&1

:: Start backend
if not exist "%DIR%\AlgoPilot.exe" (
    echo   [ERROR] AlgoPilot.exe not found
    pause
    exit /b 1
)

"%DIR%\AlgoPilot.exe"
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% neq 0 (
    echo   [ERROR] Exited with code %EXIT_CODE%
) else (
    echo   Server stopped.
)
pause
