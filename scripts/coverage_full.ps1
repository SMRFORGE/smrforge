# Full coverage report with detailed missing lines
# Usage: .\scripts\coverage_full.ps1 [test_path]

param(
    [string]$TestPath = "tests"
)

Write-Host "Running full coverage report on: $TestPath" -ForegroundColor Cyan
Write-Host "This may take longer but provides detailed missing line information..." -ForegroundColor Yellow

# Run tests with parallel execution and detailed coverage reporting
pytest $TestPath `
    -n auto `
    --cov=smrforge `
    --cov-report=term-missing `
    --cov-report=html:htmlcov `
    --cov-report=json:coverage.json `
    --tb=short

Write-Host ""
Write-Host "Full coverage report complete!" -ForegroundColor Green
Write-Host "HTML report available at: htmlcov/index.html" -ForegroundColor Cyan
