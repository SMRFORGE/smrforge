# Run performance + memory profiling (keff and optionally mesh).
# Use when changing solver, mesh, or data handling. See docs/development/performance-and-benchmarking-assessment.md.
#
# Usage: .\scripts\run_performance_profile.ps1 [--Mesh] [--Output <path>]

param(
    [switch]$Mesh,
    [string]$Output = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Performance + memory profile (keff" -NoNewline -ForegroundColor Cyan
if ($Mesh) { Write-Host ", mesh" -NoNewline }
Write-Host ") - mode both" -ForegroundColor Cyan
Write-Host ""

$outKeff = @(); if ($Output) { $outKeff = @("--output", $Output) }
python scripts/profile_performance.py --function keff --mode both @outKeff
if ($Mesh) {
    $outMesh = @(); if ($Output) { $outMesh = @("--output", "${Output}_mesh") }
    python scripts/profile_performance.py --function mesh --mode both @outMesh
}

Write-Host ""
Write-Host "Done. Check CPU and memory reports above (or --output files)." -ForegroundColor Green
