@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set "PYEXE="
if exist ".venv\Scripts\python.exe" set "PYEXE=.venv\Scripts\python.exe"
if not defined PYEXE if exist ".venv\bin\python.exe" set "PYEXE=.venv\bin\python.exe"
if not defined PYEXE (
  echo [ERROR] Missing .venv
  echo   python -m venv .venv
  echo   .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)

rem 注入常见 MSYS2/MinGW 路径，避免 IDE 启动时 PATH 不含 g++/gdb
if exist "C:\msys64\ucrt64\bin" set "PATH=C:\msys64\ucrt64\bin;%PATH%"
if exist "H:\Dev\msys2\ucrt64\bin" set "PATH=H:\Dev\msys2\ucrt64\bin;%PATH%"

echo Starting backend: http://127.0.0.1:9000
echo Press Ctrl+C to stop.
"%PYEXE%" -m uvicorn main:app --reload --host 127.0.0.1 --port 9000
