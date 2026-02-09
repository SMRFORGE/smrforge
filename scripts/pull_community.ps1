# Pull Community changes into Pro repo (merge public/main into current branch).
# Run from smrforge-pro. Requires 'public' remote: git remote add public https://github.com/SMRFORGE/smrforge.git
# Usage: .\scripts\pull_community.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")

$remotes = git remote
if ($remotes -notcontains "public") {
    Write-Host "Add public remote first: git remote add public https://github.com/SMRFORGE/smrforge.git" -ForegroundColor Red
    exit 1
}

Push-Location $repoRoot
try {
    git fetch public
    git merge public/main -m "Merge community changes from public/main"
} finally {
    Pop-Location
}
