#!/bin/bash
# Bash script to push SMRForge to GitHub
# Run this after creating a GitHub repository

echo "SMRForge GitHub Push Script"
echo "============================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Error: Git repository not initialized. Run 'git init' first."
    exit 1
fi

# Get GitHub username
read -p "Enter your GitHub username: " github_username
read -p "Enter repository name (default: smrforge): " repo_name
repo_name=${repo_name:-smrforge}

# Show current status
echo ""
echo "Current git status:"
git status --short

# Ask for confirmation
echo ""
echo "This will:"
echo "1. Create an initial commit with all files"
echo "2. Add GitHub remote: https://github.com/$github_username/$repo_name.git"
echo "3. Push to 'main' branch"
echo ""
read -p "Continue? (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

# Stage all files
echo ""
echo "Staging files..."
git add .

# Create initial commit
echo "Creating initial commit..."
git commit -m "Initial commit: SMRForge v0.1.0 - SMR Design and Analysis Toolkit"

# Set branch to main (if not already)
echo "Setting default branch to 'main'..."
git branch -M main 2>/dev/null

# Add remote
echo "Adding GitHub remote..."
git remote remove origin 2>/dev/null
git remote add origin "https://github.com/$github_username/$repo_name.git"

# Verify remote
echo ""
echo "Remote configuration:"
git remote -v

# Push
echo ""
echo "Pushing to GitHub..."
echo "Note: You may be prompted for GitHub credentials."
echo "Use a Personal Access Token (not password) if using HTTPS."
echo ""
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "Success! Repository pushed to GitHub."
    echo "View it at: https://github.com/$github_username/$repo_name"
else
    echo ""
    echo "Push failed. Common issues:"
    echo "1. Repository doesn't exist on GitHub - create it first"
    echo "2. Authentication failed - use Personal Access Token"
    echo "3. Branch name mismatch - try: git push -u origin master"
    echo ""
    echo "See GITHUB_SETUP.md for detailed troubleshooting."
fi

