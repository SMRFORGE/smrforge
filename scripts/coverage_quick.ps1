# Quick coverage check script - faster than full coverage report
# Usage: .\scripts\coverage_quick.ps1 [test_path]

param(
    [string]$TestPath = "tests"
)

Write-Host "Running quick coverage check on: $TestPath" -ForegroundColor Cyan
Write-Host "Using parallel execution for speed..." -ForegroundColor Yellow

# Run tests with parallel execution and minimal coverage reporting
pytest $TestPath `
    -n auto `
    --cov=smrforge `
    --cov-report=term `
    --cov-report=json:coverage_quick.json `
    -q `
    --tb=short

Write-Host ""
Write-Host "Quick coverage check complete!" -ForegroundColor Green
Write-Host "For detailed missing lines, run: pytest --cov=smrforge --cov-report=term-missing" -ForegroundColor Yellow
