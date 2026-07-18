$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$appDir = Join-Path $projectRoot "release\AlgoPilot-Portable"
$exe = Join-Path $appDir "AlgoPilot.exe"
$port = 8765
$stdout = Join-Path $projectRoot "release\portable-test.stdout.log"
$stderr = Join-Path $projectRoot "release\portable-test.stderr.log"

if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw "Missing $exe" }
$env:ALGOPILOT_PORT = [string]$port
$startArgs = @{
    FilePath = $exe
    WorkingDirectory = $appDir
    WindowStyle = "Hidden"
    RedirectStandardOutput = $stdout
    RedirectStandardError = $stderr
    PassThru = $true
}
$process = Start-Process @startArgs

try {
    $health = $null
    for ($i = 0; $i -lt 90; $i++) {
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/api/health" -TimeoutSec 2
            break
        } catch {
            if ($process.HasExited) { throw "Packaged server exited with code $($process.ExitCode)" }
            Start-Sleep -Seconds 1
        }
    }
    if ($null -eq $health) { throw "Packaged server did not become healthy" }
    if ($health.status -ne "ok" -or -not $health.cpp_compiler -or -not $health.trace_cpp) {
        throw "Health capability check failed: $($health | ConvertTo-Json -Compress)"
    }

    $index = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/" -TimeoutSec 10
    if ($index.StatusCode -ne 200 -or $index.Content -notmatch '<div id="app"') {
        throw "Packaged frontend check failed"
    }
    $spa = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/learn/array" -TimeoutSec 10
    if ($spa.StatusCode -ne 200 -or $spa.Content -notmatch '<div id="app"') {
        throw "SPA fallback check failed"
    }

    Write-Output "HTTP_HEALTH=$($health | ConvertTo-Json -Compress)"
    Write-Output "HTTP_INDEX=200,$($index.RawContentLength) bytes"
    Write-Output "HTTP_SPA_FALLBACK=200"
} finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit()
    }
}

Push-Location $appDir
try {
    & $exe --exec-script (Join-Path $PSScriptRoot "verify_portable_runtime.py")
    if ($LASTEXITCODE -ne 0) { throw "Frozen runtime verification failed with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
