# Push current branch to origin (Pro private repo).
# Run from repo root. Use git_safe.ps1 if working in OneDrive-synced folder.
# Usage: .\scripts\push_pro.ps1 [-Message "commit msg"]  # commit first if -Message
#        .\scripts\push_pro.ps1                          # push only

param(
    [string] $Message = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")

Push-Location $repoRoot
try {
    if ($Message) {
        git add -A
        $status = git status --porcelain
        if ($status) {
            git commit -m $Message
        }
    }
    $branch = git rev-parse --abbrev-ref HEAD
    git push -u origin $branch
} finally {
    Pop-Location
}
