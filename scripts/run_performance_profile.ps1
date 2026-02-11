# Run performance + memory profiling (keff and optionally mesh).
# Use when changing solver, mesh, or data handling. See docs/development/performance-and-benchmarking-assessment.md.
#
# Usage: .\scripts\run_performance_profile.ps1 [--Mesh] [--Output <path>]

param(
    [switch]$Mesh,
    [string]$Output = "output/profiling/report"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Ensure output directory exists
$outDir = Split-Path -Parent $Output
if ($outDir) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

Write-Host "Performance + memory profile (keff" -NoNewline -ForegroundColor Cyan
if ($Mesh) { Write-Host ", mesh" -NoNewline }
Write-Host ") - mode both" -ForegroundColor Cyan
Write-Host ""

$outKeff = @("--output", $Output)
python scripts/profile_performance.py --function keff --mode both @outKeff
if ($Mesh) {
    $outMesh = @("--output", "${Output}_mesh")
    python scripts/profile_performance.py --function mesh --mode both @outMesh
}

Write-Host ""
Write-Host "Done. Check CPU and memory reports above (or --output files)." -ForegroundColor Green
