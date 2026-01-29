# Git wrapper that clears stale .git/index.lock and retries once on failure.
# Use when working in OneDrive-synced folders: .\scripts\git_safe.ps1 add -A; .\scripts\git_safe.ps1 commit -m "msg"; .\scripts\git_safe.ps1 push
# See: docs/development/git-onedrive.md

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $GitArgs
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$lockPath = Join-Path $repoRoot ".git\index.lock"

function Remove-StaleLock {
    if (Test-Path $lockPath) {
        try {
            Remove-Item $lockPath -Force -ErrorAction Stop
        } catch { }
    }
}

function Invoke-Git {
    $origDir = Get-Location
    try {
        Set-Location $repoRoot
        & git @GitArgs
        return $LASTEXITCODE
    } finally {
        Set-Location $origDir
    }
}

Remove-StaleLock
$exit = Invoke-Git
if ($exit -ne 0) {
    Start-Sleep -Milliseconds 500
    Remove-StaleLock
    $exit = Invoke-Git
}
exit $exit
