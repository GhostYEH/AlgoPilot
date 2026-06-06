@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: ============================================================
::  AlgoPilot Build Script
::  Output: dist/ directory, runnable without Python/Node/g++
:: ============================================================

set "PROJECT=%~dp0"
set "PROJECT=%PROJECT:~0,-1%"
set "DIST=%PROJECT%\dist"
set "BACKEND=%PROJECT%\backend"
set "FRONTEND=%PROJECT%\frontend"
set "VENV=%BACKEND%\.venv"

echo ============================================================
echo   AlgoPilot Build Start
echo ============================================================

:: ---------- 0. Prerequisites ----------
if not exist "%VENV%\Scripts\python.exe" (
    echo [ERROR] Python venv not found: %VENV%
    echo Please run: cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

if not exist "%FRONTEND%\package.json" (
    echo [ERROR] Frontend not found: %FRONTEND%
    exit /b 1
)

:: ---------- 1. Install PyInstaller ----------
echo.
echo [1/7] Installing PyInstaller ...
"%VENV%\Scripts\pip.exe" install pyinstaller --quiet 2>nul

:: ---------- 2. Build Frontend ----------
echo.
echo [2/7] Building frontend ...
cd /d "%FRONTEND%"
if not exist "node_modules" (
    echo   Installing frontend deps ...
    call npm install --prefer-offline 2>nul
    if errorlevel 1 (
        echo [ERROR] npm install failed
        exit /b 1
    )
)
echo   Running npm run build ...
call npm run build 2>nul
if errorlevel 1 (
    echo [ERROR] Frontend build failed
    exit /b 1
)
echo   Frontend build done: %FRONTEND%\dist

:: ---------- 3. PyInstaller Backend ----------
echo.
echo [3/7] PyInstaller packaging backend ...
cd /d "%BACKEND%"
if exist "build" rmdir /s /q "build"

"%VENV%\Scripts\python.exe" -m PyInstaller algpilot.spec --noconfirm --clean 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller failed
    exit /b 1
)
echo   Backend packaged: %BACKEND%\dist\AlgoPilot

:: ---------- 4. Assemble dist ----------
echo.
echo [4/7] Assembling dist directory ...

if exist "%DIST%" rmdir /s /q "%DIST%"
mkdir "%DIST%"

echo   Copying backend ...
copy "%BACKEND%\dist\AlgoPilot\AlgoPilot.exe" "%DIST%\" >nul
xcopy "%BACKEND%\dist\AlgoPilot\_internal" "%DIST%\_internal\" /E /I /Q /Y >nul

echo   Copying frontend ...
if exist "%DIST%\_internal\frontend\oj" rmdir /s /q "%DIST%\_internal\frontend\oj"
xcopy "%FRONTEND%\dist\*" "%DIST%\_internal\frontend\" /E /I /Q /Y >nul

if exist "%BACKEND%\.env.example" (
    copy "%BACKEND%\.env.example" "%DIST%\.env.example" >nul
)

:: ---------- 5. Portable MinGW ----------
echo.
echo [5/7] Preparing portable MinGW-w64 (g++ + gdb)
set "MINGW_DIR=%DIST%\_internal\mingw"
call :setup_mingw
goto :mingw_done

:setup_mingw
set "LOCAL_MINGW="
if exist "C:\msys64\ucrt64\bin\g++.exe" (
    set "LOCAL_MINGW=C:\msys64\ucrt64"
    goto :mingw_found
)
if exist "C:\msys64\mingw64\bin\g++.exe" (
    set "LOCAL_MINGW=C:\msys64\mingw64"
    goto :mingw_found
)
if exist "%USERPROFILE%\msys64\ucrt64\bin\g++.exe" (
    set "LOCAL_MINGW=%USERPROFILE%\msys64\ucrt64"
    goto :mingw_found
)
if exist "%USERPROFILE%\scoop\apps\msys2\current\ucrt64\bin\g++.exe" (
    set "LOCAL_MINGW=%USERPROFILE%\scoop\apps\msys2\current\ucrt64"
    goto :mingw_found
)
echo   [WARN] Local MinGW not found, C++ judge will be limited
echo   To enable C++ support, install MinGW-w64 and copy to: %MINGW_DIR%
goto :eof

:mingw_found
echo   Copying local MinGW: %LOCAL_MINGW%
mkdir "%MINGW_DIR%\bin" 2>nul
for %%E in (g++.exe gcc.exe ld.exe as.exe objdump.exe strip.exe dlltool.exe nm.exe ar.exe ranlib.exe gdb.exe addr2line.exe size.exe strings.exe windres.exe) do (
    if exist "%LOCAL_MINGW%\bin\%%E" copy "%LOCAL_MINGW%\bin\%%E" "%MINGW_DIR%\bin\" >nul 2>&1
)
for %%D in (libiconv*.dll libintl*.dll zlib*.dll libwinpthread*.dll "libstdc++*.dll" libgcc_s_seh-1.dll libmpfr*.dll libgmp*.dll libzstd*.dll libcrypto*.dll libssl*.dll libexpat*.dll libffi*.dll msys-2.0.dll) do (
    if exist "%LOCAL_MINGW%\bin\%%D" copy "%LOCAL_MINGW%\bin\%%D" "%MINGW_DIR%\bin\" >nul 2>&1
)
xcopy "%LOCAL_MINGW%\include" "%MINGW_DIR%\include\" /E /I /Q /Y >nul 2>&1
xcopy "%LOCAL_MINGW%\lib" "%MINGW_DIR%\lib\" /E /I /Q /Y >nul 2>&1
echo   MinGW copy done
goto :eof

:mingw_done

:: ---------- 6. Verify ----------
echo.
echo [6/7] Verifying package integrity ...

set "VERIFY_OK=1"
if not exist "%DIST%\AlgoPilot.exe" (
    echo   [ERROR] AlgoPilot.exe not found
    set "VERIFY_OK=0"
)
if not exist "%DIST%\_internal\frontend\index.html" (
    echo   [ERROR] Frontend index.html not found
    set "VERIFY_OK=0"
)
if exist "%DIST%\_internal\mingw\bin\g++.exe" (
    echo   [OK] MinGW g++ available
) else (
    echo   [WARN] MinGW g++ not available, C++ judge will be limited
)
if exist "%DIST%\_internal\mingw\bin\gdb.exe" (
    echo   [OK] MinGW gdb available
) else (
    echo   [WARN] MinGW gdb not available, C++ trace will be limited
)
if "!VERIFY_OK!"=="0" (
    echo   [ERROR] Verification failed, check errors above
    exit /b 1
)
echo   Verification passed

:: ---------- 7. Create Launcher ----------
echo.
echo [7/7] Creating launcher ...
copy "%PROJECT%\launcher.bat" "%DIST%\AlgoPilot.bat" >nul 2>&1

:: ---------- Done ----------
echo.
echo ============================================================
echo   Build Complete!
echo.
echo   Output: %DIST%
echo.
echo   Usage:
echo     1. Copy dist folder to target machine
echo     2. Double-click AlgoPilot.bat to start
echo     3. Browser opens http://127.0.0.1:8000
echo.
echo   For AI features, edit dist\.env with your API keys
echo ============================================================

cd /d "%PROJECT%"
endlocal
