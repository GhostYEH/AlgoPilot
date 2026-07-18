[CmdletBinding()]
param(
    [string]$ToolchainRoot = "H:\Dev\msys2\ucrt64",
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
    throw "Missing backend virtual environment: $python"
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm.cmd is required on the build computer"
}
if (-not $SkipToolchain -and -not (Test-Path -LiteralPath (Join-Path $ToolchainRoot "bin\g++.exe"))) {
    throw "Portable MinGW toolchain not found: $ToolchainRoot"
}

Write-Host "[1/6] Building frontend"
Push-Location $frontend
try { & npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" } }
finally { Pop-Location }

Write-Host "[2/6] Installing PyInstaller in the build venv"
& $python -m pip install "pyinstaller>=6.0,<7" --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { throw "PyInstaller installation failed" }

Write-Host "[3/6] Freezing backend"
Push-Location $backend
try {
    & $python -m PyInstaller --noconfirm --clean algpilot.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }
}
finally { Pop-Location }

Write-Host "[4/6] Assembling portable directory"
if (Test-Path -LiteralPath $output) {
    $resolvedRelease = (Resolve-Path -LiteralPath $releaseRoot).Path
    $resolvedOutput = (Resolve-Path -LiteralPath $output).Path
    if (-not $resolvedOutput.StartsWith($resolvedRelease + [IO.Path]::DirectorySeparatorChar)) {
        throw "Refusing to remove output outside release directory: $resolvedOutput"
    }
    Remove-Item -LiteralPath $resolvedOutput -Recurse -Force
}
New-Item -ItemType Directory -Path $output -Force | Out-Null
Copy-Item -Path (Join-Path $backend "dist\AlgoPilot\*") -Destination $output -Recurse -Force
New-Item -ItemType Directory -Path (Join-Path $output "data") -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $backend "data\alp_learning.db") -Destination (Join-Path $output "data\alp_learning.db") -Force
Copy-Item -LiteralPath (Join-Path $backend ".env") -Destination (Join-Path $output ".env") -Force
# Keep generated file names ASCII so Windows PowerShell 5.1 can execute this
# UTF-8 source file correctly even when its legacy code page is not UTF-8.
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "start-portable.bat") -Destination (Join-Path $output "Start AlgoPilot.bat") -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "PORTABLE_README.txt") -Destination (Join-Path $output "README.txt") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination $output -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "THIRD_PARTY_LICENSES.md") -Destination $output -Force

if (-not $SkipToolchain) {
    Write-Host "[5/6] Copying portable g++/gdb toolchain (this is the largest step)"
    $toolchainDest = Join-Path $output "mingw\ucrt64"
    New-Item -ItemType Directory -Path $toolchainDest -Force | Out-Null
    & robocopy.exe $ToolchainRoot $toolchainDest /E /R:2 /W:1 /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -ge 8) { throw "Toolchain copy failed with robocopy exit code $LASTEXITCODE" }
} else {
    Write-Warning "Toolchain omitted: C++ judging and Trace will not work on a clean computer"
}

Write-Host "[6/6] Creating ZIP and checksums"
$zip = Join-Path $releaseRoot "AlgoPilot-Portable-Windows-x64.zip"
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
if (Get-Command tar.exe -ErrorAction SilentlyContinue) {
    # Compress-Archive keeps the complete 1 GB MSYS2 tree in excessive memory
    # on Windows PowerShell 5.1. bsdtar streams it and still creates a standard ZIP.
    & tar.exe -a -cf $zip -C $output .
    if ($LASTEXITCODE -ne 0) { throw "ZIP creation failed with tar exit code $LASTEXITCODE" }
} else {
    Compress-Archive -Path (Join-Path $output "*") -DestinationPath $zip -CompressionLevel Optimal
}
$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $zip
"$($hash.Hash)  $([IO.Path]::GetFileName($zip))" | Set-Content -LiteralPath (Join-Path $releaseRoot "SHA256SUMS.txt") -Encoding ascii

Write-Host "Portable package: $output"
Write-Host "ZIP: $zip"
