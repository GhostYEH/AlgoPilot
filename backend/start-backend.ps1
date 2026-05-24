# 启动判题 / API 后端（端口 9000）
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "未找到 .venv，请先执行: python -m venv .venv" -ForegroundColor Red
    exit 1
}

& $py -m pip install -r requirements.txt -q

function Test-BackendDevReady([int]$p) {
    try {
        $health = Invoke-WebRequest -Uri "http://127.0.0.1:$p/api/health" -UseBasicParsing -TimeoutSec 2
        if ($health.StatusCode -ne 200) { return $false }
        $openapi = Invoke-WebRequest -Uri "http://127.0.0.1:$p/openapi.json" -UseBasicParsing -TimeoutSec 3
        return $openapi.Content -match '/api/ai/oj/assistant'
    } catch {
        return $false
    }
}

$port = 9000
foreach ($p in @(9000, 9010, 9080, 8900)) {
    if (Test-BackendDevReady $p) {
        Write-Host "后端已在端口 $p 运行（含 OJ 智能体接口），无需重复启动。" -ForegroundColor Yellow
        exit 0
    }
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$p/api/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) {
            Write-Host "端口 $p 上的后端过旧（缺少 /api/ai/oj/assistant），将重启..." -ForegroundColor Yellow
            $conn = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($conn) {
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 1
            }
        }
    } catch { }
}

$conn = Get-NetTCPConnection -LocalPort 9000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    Write-Host "端口 9000 被 PID $($conn.OwningProcess) 占用，尝试结束..." -ForegroundColor Yellow
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Host "启动 API: http://127.0.0.1:$port  (Ctrl+C 停止)" -ForegroundColor Green
& $py -m uvicorn main:app --host 127.0.0.1 --port $port --reload
