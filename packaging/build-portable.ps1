[CmdletBinding()]
param(
    [string]$ToolchainRoot = "H:\Dev\msys2\ucrt64",
    [switch]$SkipTests,
    [switch]$SkipToolchain
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backend = Join-Path $projectRoot "backend"
$frontend = Join-Path $projectRoot "frontend"
$releaseRoot = Join-Path $projectRoot "release"
$output = Join-Path $releaseRoot "AlgoPilot-Portable"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Missing build Python: $python"
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm.cmd is required on the build computer"
}
if (-not $SkipToolchain -and -not (Test-Path -LiteralPath (Join-Path $ToolchainRoot "bin\g++.exe"))) {
    throw "Portable MinGW toolchain not found: $ToolchainRoot"
}

if (-not $SkipTests) {
    Write-Host "[1/8] Verifying source database and application tests"
    & $python -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); r=c.execute('PRAGMA integrity_check').fetchone()[0]; print('source database integrity:',r); raise SystemExit(0 if r=='ok' else 1)" (Join-Path $backend "data\alp_learning.db")
    if ($LASTEXITCODE -ne 0) { throw "Source database integrity check failed" }
    Push-Location $backend
    $oldDatabaseUrl = $env:DATABASE_URL
    $testDb = Join-Path $releaseRoot "packaging-test.db"
    try {
        New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
        if (Test-Path -LiteralPath $testDb) { Remove-Item -LiteralPath $testDb -Force }
        $env:DATABASE_URL = "sqlite:///$($testDb.Replace('\', '/'))"
        & $python -m pytest
        if ($LASTEXITCODE -ne 0) { throw "Backend tests failed" }
    } finally {
        if ($null -eq $oldDatabaseUrl) { Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue } else { $env:DATABASE_URL = $oldDatabaseUrl }
        Pop-Location
    }
    Push-Location $frontend
    try { & npm.cmd run typecheck; if ($LASTEXITCODE -ne 0) { throw "Frontend typecheck failed" } }
    finally { Pop-Location }
} else {
    Write-Warning "Source tests skipped by request"
}

Write-Host "[2/8] Building production frontend"
Push-Location $frontend
try { & npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" } }
finally { Pop-Location }

Write-Host "[3/8] Ensuring PyInstaller is available"
& $python -m pip install "pyinstaller>=6.0,<7" --disable-pip-version-check -q
if ($LASTEXITCODE -ne 0) { throw "PyInstaller installation failed" }

Write-Host "[4/8] Freezing backend and production frontend"
Push-Location $backend
try {
    & $python -m PyInstaller --noconfirm --clean algpilot.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }
}
finally { Pop-Location }

Write-Host "[5/8] Assembling portable application"
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
if (Test-Path -LiteralPath $output) {
    $resolvedRelease = (Resolve-Path -LiteralPath $releaseRoot).Path
    $resolvedOutput = (Resolve-Path -LiteralPath $output).Path
    if (-not $resolvedOutput.StartsWith($resolvedRelease + [IO.Path]::DirectorySeparatorChar)) {
        throw "Refusing to replace output outside release directory: $resolvedOutput"
    }
    Remove-Item -LiteralPath $resolvedOutput -Recurse -Force
}
New-Item -ItemType Directory -Path $output -Force | Out-Null
Copy-Item -Path (Join-Path $backend "dist\AlgoPilot\*") -Destination $output -Recurse -Force
New-Item -ItemType Directory -Path (Join-Path $output "data") -Force | Out-Null

# sqlite3.Connection.backup creates a consistent snapshot even if the source
# database is being read while packaging.
$sourceDb = Join-Path $backend "data\alp_learning.db"
$packagedDb = Join-Path $output "data\alp_learning.db"
$backupCode = "import sqlite3,sys; src=sqlite3.connect(sys.argv[1]); dst=sqlite3.connect(sys.argv[2]); src.backup(dst); dst.close(); src.close()"
& $python -c $backupCode $sourceDb $packagedDb
if ($LASTEXITCODE -ne 0) { throw "Database snapshot failed" }

Copy-Item -LiteralPath (Join-Path $backend ".env") -Destination (Join-Path $output ".env") -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "start-portable.bat") -Destination (Join-Path $output "Start AlgoPilot.bat") -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "start-portable.bat") -Destination (Join-Path $output "Run AlgoPilot.bat") -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "PORTABLE_README.txt") -Destination (Join-Path $output "README.txt") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination $output -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "THIRD_PARTY_LICENSES.md") -Destination $output -Force

if (-not $SkipToolchain) {
    Write-Host "[6/8] Copying portable g++/gdb toolchain"
    $toolchainDest = Join-Path $output "mingw\ucrt64"
    New-Item -ItemType Directory -Path $toolchainDest -Force | Out-Null
    & robocopy.exe $ToolchainRoot $toolchainDest /E /R:2 /W:1 /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -ge 8) { throw "Toolchain copy failed with robocopy exit code $LASTEXITCODE" }
} else {
    Write-Warning "Toolchain omitted: C++ judging and Trace cannot work on a clean computer"
}

Write-Host "[7/8] Writing integrity manifest and verifying assembled files"
$manifestScript = Join-Path $PSScriptRoot "write_manifest.py"
& $python $manifestScript $output
if ($LASTEXITCODE -ne 0) { throw "Integrity manifest generation failed" }

& $python (Join-Path $PSScriptRoot "verify_release.py") $output
if ($LASTEXITCODE -ne 0) { throw "Portable runtime verification failed" }

Write-Host "[8/8] Creating ZIP and SHA-256 checksum"
$zip = Join-Path $releaseRoot "AlgoPilot-Portable-Windows-x64.zip"
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
if (Get-Command tar.exe -ErrorAction SilentlyContinue) {
    & tar.exe -a -cf $zip -C $output .
    if ($LASTEXITCODE -ne 0) { throw "ZIP creation failed with tar exit code $LASTEXITCODE" }
} else {
    Compress-Archive -Path (Join-Path $output "*") -DestinationPath $zip -CompressionLevel Optimal
}
$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $zip
"$($hash.Hash)  $([IO.Path]::GetFileName($zip))" | Set-Content -LiteralPath (Join-Path $releaseRoot "SHA256SUMS.txt") -Encoding ascii

Write-Host "Portable directory: $output"
Write-Host "ZIP: $zip"
Write-Host "SHA256: $($hash.Hash)"
