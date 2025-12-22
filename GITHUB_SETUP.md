# GitHub Setup Guide for SMRForge

This guide will help you push your SMRForge repository to GitHub.

## Prerequisites

1. **Git installed** on your system
   - Windows: Download from [git-scm.com](https://git-scm.com/download/win)
   - Check installation: `git --version`

2. **GitHub account** created
   - Sign up at [github.com](https://github.com)

3. **GitHub repository created** (empty or with README)
   - Go to GitHub → New Repository
   - Name it `smrforge` (or your preferred name)
   - Choose public or private
   - **Don't initialize with README** (we already have one)

## Step-by-Step Setup

### Step 1: Initialize Git Repository

```bash
# Navigate to your project directory
cd C:\Users\cmwha\OneDrive\Documents\GitHub\smrforge

# Initialize git repository
git init

# Verify git is initialized
git status
```

### Step 2: Add All Files

```bash
# Add all files to staging
git add .

# Verify what will be committed
git status
```

### Step 3: Create Initial Commit

```bash
# Create your first commit
git commit -m "Initial commit: SMRForge v0.1.0 - SMR Design and Analysis Toolkit"
```

### Step 4: Add GitHub Remote

Replace `YOUR_USERNAME` with your GitHub username:

```bash
# Add GitHub remote (HTTPS)
git remote add origin https://github.com/YOUR_USERNAME/smrforge.git

# Or use SSH (if you have SSH keys set up)
# git remote add origin git@github.com:YOUR_USERNAME/smrforge.git

# Verify remote
git remote -v
```

### Step 5: Push to GitHub

```bash
# Push to GitHub (first time)
git push -u origin main

# If you get an error about 'main' branch, try 'master':
# git branch -M main
# git push -u origin main
```

## Common Issues and Solutions

### Issue: "Branch name is 'master' not 'main'"

```bash
# Rename branch to main
git branch -M main
git push -u origin main
```

### Issue: Authentication Required

GitHub no longer accepts passwords. Use one of these:

**Option 1: Personal Access Token (Recommended for HTTPS)**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use token as password when prompted

**Option 2: SSH Keys (Recommended for long-term)**
1. Generate SSH key: `ssh-keygen -t ed25519 -C "your_email@example.com"`
2. Add to GitHub: Settings → SSH and GPG keys → New SSH key
3. Use SSH URL: `git@github.com:YOUR_USERNAME/smrforge.git`

**Option 3: GitHub CLI**
```bash
# Install GitHub CLI: https://cli.github.com
gh auth login
git remote set-url origin https://github.com/YOUR_USERNAME/smrforge.git
```

### Issue: "Repository not found"

- Check that the repository exists on GitHub
- Verify your username in the remote URL
- Ensure you have push access to the repository

## Quick Reference Commands

```bash
# Check status
git status

# Add files
git add .
git add <specific-file>

# Commit changes
git commit -m "Your commit message"

# Push changes
git push

# Pull changes (if working from multiple locations)
git pull

# View commit history
git log --oneline

# View remote
git remote -v
```

## Future Updates

After initial push, to update GitHub with new changes:

```bash
# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push
git push
```

## Repository Structure

Your repository should have:
- ✅ `README.md` - Project overview
- ✅ `setup.py` - Package configuration
- ✅ `requirements.txt` - Dependencies
- ✅ `smrforge/` - Main package code
- ✅ `tests/` - Test suite
- ✅ `examples/` - Example scripts
- ✅ `Dockerfile` & `docker-compose.yml` - Docker support
- ✅ `.gitignore` - Excluded files
- ✅ Various documentation files (`.md`)

## Optional: GitHub Actions CI/CD

To set up automated testing, create `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11", "3.12"]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    - name: Run tests
      run: |
        pytest tests/ -v
```

## Next Steps

After pushing to GitHub:

1. **Add repository description** on GitHub
2. **Add topics/tags** (e.g., `nuclear`, `reactor`, `smr`, `python`, `neutronics`)
3. **Set up GitHub Pages** for documentation (optional)
4. **Add license** if not already included
5. **Create releases** for version tags
6. **Set up branch protection** (Settings → Branches)
7. **Add collaborators** if working in a team

---

**Need Help?** Check [GitHub Docs](https://docs.github.com/) or open an issue in your repository.

