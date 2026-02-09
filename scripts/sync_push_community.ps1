# Sync Community content to public repo and push.
# Run from smrforge-pro (private) repo. Requires sync_to_public.py in scripts/.
# Usage: .\scripts\sync_push_community.ps1 [-DryRun] [-NoPush] [-PublicRepo C:\path\to\smrforge]

param(
    [switch] $DryRun,
    [switch] $NoPush,
    [string] $PublicRepo = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")

$syncScript = Join-Path $scriptDir "sync_to_public.py"
if (-not (Test-Path $syncScript)) {
    Write-Host "sync_to_public.py not found. Run this from smrforge-pro repo." -ForegroundColor Red
    exit 1
}

# 1. Pre-sync check
Push-Location $repoRoot
try {
    python scripts/pre_sync_check.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $syncArgs = @("--skip-leakage-check")  # pre_sync_check.py already ran
    if ($DryRun) { $syncArgs += "--dry-run" }
    if ($PublicRepo) { $syncArgs += "--public-repo", $PublicRepo }
    python scripts/sync_to_public.py @syncArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    if ($DryRun) { exit 0 }

    # Resolve public repo path (sync script prints it; we infer from default)
    $publicPath = if ($PublicRepo) { $PublicRepo } else {
        if ((Split-Path $repoRoot -Leaf) -eq "smrforge-pro") {
            Join-Path (Split-Path $repoRoot -Parent) "smrforge"
        } else {
            Join-Path (Split-Path $repoRoot -Parent) "smrforge-public"
        }
    }
    $publicPath = Resolve-Path $publicPath -ErrorAction SilentlyContinue
    if (-not $publicPath -or -not (Test-Path (Join-Path $publicPath ".git"))) {
        Write-Host "Public repo not found at $publicPath" -ForegroundColor Red
        exit 1
    }

    if (-not $NoPush) {
        Push-Location $publicPath
        try {
            git checkout -B community-sync 2>$null
            git add -A
            $status = git status --porcelain
            if ($status) {
                git commit -m "Community sync from smrforge-pro"
            }
            git push -u origin community-sync
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "Skipping push (--NoPush). Next: cd $publicPath; git add -A; git commit -m 'Community sync'; git push origin community-sync"
    }
} finally {
    Pop-Location
}
