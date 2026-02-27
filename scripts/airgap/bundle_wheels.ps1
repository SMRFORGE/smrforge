# Bundle all wheels for air-gapped installation.
# Run from repo root (smrforge or smrforge-pro).
#
# Usage: .\scripts\airgap\bundle_wheels.ps1 [OUTPUT_DIR]

param([string]$OutputDir = ".\offline-wheels")
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

$ReqFile = "requirements-lock.txt"
if (-not (Test-Path $ReqFile)) { $ReqFile = "requirements.txt" }

Write-Host "==> Bundling wheels to $OutputDir"
Write-Host "==> Using $ReqFile"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

pip download -r $ReqFile -d $OutputDir
pip download . -d $OutputDir

if (Test-Path "smrforge_pro") {
    Write-Host "==> Pro repo: including smrforge (Community) from PyPI"
    pip download smrforge -d $OutputDir 2>$null
}

Write-Host "==> Done. Transfer $OutputDir to air-gapped machine, then:"
Write-Host "    pip install --no-index --find-links $OutputDir -r $ReqFile"
Write-Host "    pip install --no-index --find-links $OutputDir ."
