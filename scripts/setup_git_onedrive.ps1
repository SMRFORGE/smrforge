# One-time Git setup to reduce "Permission denied" / index.lock issues
# when the repo lives in a OneDrive-synced folder on Windows.
#
# Run from repo root: .\scripts\setup_git_onedrive.ps1
# See: docs/development/git-onedrive.md

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
    Write-Error "Not a git repository (or run from repo root). Expected .git in: $repoRoot"
}
Set-Location $repoRoot

Write-Host "Git + OneDrive setup (repo: $repoRoot)" -ForegroundColor Cyan
Write-Host ""

# 1. Remove stale locks first (so git config can run)
$indexLock = Join-Path $repoRoot ".git\index.lock"
$configLock = Join-Path $repoRoot ".git\config.lock"
$removed = $false
if (Test-Path $indexLock) { Remove-Item $indexLock -Force -ErrorAction SilentlyContinue; $removed = $true }
if (Test-Path $configLock) { Remove-Item $configLock -Force -ErrorAction SilentlyContinue; $removed = $true }
if ($removed) {
    Write-Host "1. Removed stale .git\index.lock and/or .git\config.lock." -ForegroundColor Yellow
} else {
    Write-Host "1. No stale Git lock files found." -ForegroundColor Green
}

# 2. Local git config
Write-Host "2. Setting local git config..." -ForegroundColor Yellow
$ea = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$cfgOk = $true
git config core.fscache false 2>$null
if ($LASTEXITCODE -ne 0) { $cfgOk = $false }
git config core.longpaths true 2>$null
if ($LASTEXITCODE -ne 0) { $cfgOk = $false }
$ErrorActionPreference = $ea
if ($cfgOk) {
    Write-Host "   core.fscache = false, core.longpaths = true" -ForegroundColor Green
} else {
    Write-Host "   Config update failed (Permission denied?). Close IDE, pause OneDrive, then re-run." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Cyan
Write-Host ""
Write-Host "If you still see 'Permission denied' (index.lock or config):" -ForegroundColor Yellow
Write-Host "  - Use scripts\git_safe.ps1 for add/commit/push (clears lock, retries)." -ForegroundColor White
Write-Host "  - Prefer 'Always keep on this device' for this folder in OneDrive." -ForegroundColor White
Write-Host "  - Or move the repo outside OneDrive (e.g. C:\dev\smrforge)." -ForegroundColor White
Write-Host "  - See docs/development/git-onedrive.md for more." -ForegroundColor White
Write-Host ""
