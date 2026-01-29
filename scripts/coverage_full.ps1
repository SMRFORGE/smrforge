# Full coverage report with detailed missing lines
# Usage: .\scripts\coverage_full.ps1 [test_path]

param(
    [string]$TestPath = "tests"
)

Write-Host "Running full coverage report on: $TestPath" -ForegroundColor Cyan
Write-Host "This may take longer but provides detailed missing line information..." -ForegroundColor Yellow

# Keep generated artifacts out of repo root
$CoverageOutDir = "coverage/generated"
New-Item -ItemType Directory -Force $CoverageOutDir | Out-Null

# Use temp dir for coverage data to avoid Windows/OneDrive lock issues (see COVERAGE_TRACKING.md)
$env:COVERAGE_FILE = Join-Path $env:TEMP ".coverage_smrforge"

# Run tests with detailed coverage reporting (omit -n auto if pytest-xdist not installed)
pytest $TestPath `
    --cov=smrforge `
    --cov-report=term-missing `
    --cov-report=html:$CoverageOutDir/htmlcov `
    --cov-report=json:$CoverageOutDir/coverage.json `
    --tb=short

Write-Host ""
Write-Host "Full coverage report complete!" -ForegroundColor Green
Write-Host "HTML report available at: $CoverageOutDir/htmlcov/index.html" -ForegroundColor Cyan
