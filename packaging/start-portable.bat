@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

title AlgoPilot Launcher
set "APP_EXE=%CD%\AlgoPilot.exe"
if not exist "%APP_EXE%" (
  echo [错误] 找不到 AlgoPilot.exe
  echo 请完整解压发行包后再运行此文件。
  pause
  exit /b 1
)

rem Reuse an already-running AlgoPilot instance. This is especially useful
rem when the first launch finishes shortly after the launcher timeout.
for %%P in (8000 8001 8010 8080) do (
  call :health_check %%P
  if not errorlevel 1 (
    set "APP_URL=http://127.0.0.1:%%P/"
    echo AlgoPilot 已经在端口 %%P 运行，正在打开浏览器...
    start "" "!APP_URL!"
    endlocal
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
  echo [错误] 端口 8000、8001、8010、8080 均被占用。
  pause
  exit /b 1
)

set "APP_URL=http://127.0.0.1:!ALGOPILOT_PORT!/"
echo 正在启动 AlgoPilot（端口 !ALGOPILOT_PORT!）...
start "AlgoPilot Server - 关闭此窗口即可停止" /D "%CD%" cmd.exe /k ""%APP_EXE%""

set /a RETRY=0
:wait_server
set /a RETRY+=1
call :health_check !ALGOPILOT_PORT!
if not errorlevel 1 goto open_browser
if !RETRY! GEQ 180 goto start_failed
if !RETRY! EQU 30 echo 首次启动可能触发 Windows 安全扫描，请继续等待...
if !RETRY! EQU 90 echo 服务仍在初始化数据库，请继续等待...
ping -n 2 127.0.0.1 >nul
goto wait_server

:open_browser
echo 启动成功，正在打开默认浏览器：!APP_URL!
start "" "!APP_URL!"
endlocal
exit /b 0

:start_failed
echo [错误] 服务未能在 180 秒内启动，请查看 AlgoPilot Server 窗口中的错误信息。
pause
endlocal
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
