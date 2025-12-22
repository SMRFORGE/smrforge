# PowerShell script to push SMRForge to GitHub
# Run this after creating a GitHub repository

Write-Host "SMRForge GitHub Push Script" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Error: Git repository not initialized. Run 'git init' first." -ForegroundColor Red
    exit 1
}

# Get GitHub username
$githubUsername = Read-Host "Enter your GitHub username"
$repoName = Read-Host "Enter repository name (default: smrforge)" 
if ([string]::IsNullOrWhiteSpace($repoName)) {
    $repoName = "smrforge"
}

# Show current status
Write-Host "`nCurrent git status:" -ForegroundColor Yellow
git status --short

# Ask for confirmation
Write-Host "`nThis will:" -ForegroundColor Yellow
Write-Host "1. Create an initial commit with all files"
Write-Host "2. Add GitHub remote: https://github.com/$githubUsername/$repoName.git"
Write-Host "3. Push to 'main' branch"
Write-Host ""
$confirm = Read-Host "Continue? (y/n)"

if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

# Stage all files
Write-Host "`nStaging files..." -ForegroundColor Green
git add .

# Create initial commit
Write-Host "Creating initial commit..." -ForegroundColor Green
git commit -m "Initial commit: SMRForge v0.1.0 - SMR Design and Analysis Toolkit"

# Set branch to main (if not already)
Write-Host "Setting default branch to 'main'..." -ForegroundColor Green
git branch -M main 2>$null

# Add remote
Write-Host "Adding GitHub remote..." -ForegroundColor Green
git remote remove origin 2>$null
git remote add origin "https://github.com/$githubUsername/$repoName.git"

# Verify remote
Write-Host "`nRemote configuration:" -ForegroundColor Cyan
git remote -v

# Push
Write-Host "`nPushing to GitHub..." -ForegroundColor Green
Write-Host "Note: You may be prompted for GitHub credentials." -ForegroundColor Yellow
Write-Host "Use a Personal Access Token (not password) if using HTTPS." -ForegroundColor Yellow
Write-Host ""
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSuccess! Repository pushed to GitHub." -ForegroundColor Green
    Write-Host "View it at: https://github.com/$githubUsername/$repoName" -ForegroundColor Cyan
} else {
    Write-Host "`nPush failed. Common issues:" -ForegroundColor Red
    Write-Host "1. Repository doesn't exist on GitHub - create it first" -ForegroundColor Yellow
    Write-Host "2. Authentication failed - use Personal Access Token" -ForegroundColor Yellow
    Write-Host "3. Branch name mismatch - try: git push -u origin master" -ForegroundColor Yellow
    Write-Host "`nSee GITHUB_SETUP.md for detailed troubleshooting." -ForegroundColor Yellow
}

