# GitHub Pages Documentation Setup Guide

**Status:** ✅ Workflow created - Manual setup required

---

## What Was Done

✅ **GitHub Actions workflow created** (`.github/workflows/docs.yml`)
- Automatically builds Sphinx documentation on push to `main` branch
- Deploys to GitHub Pages using GitHub Actions
- Only triggers on changes to `docs/`, `smrforge/`, or configuration files

✅ **Documentation links updated** in `README.md`
- Added GitHub Pages link: https://SMRFORGE.github.io/smrforge/
- Kept Read the Docs as alternative: https://smrforge.readthedocs.io

✅ **Sphinx configuration updated** (`docs/conf.py`)
- Added `html_baseurl` for GitHub Pages compatibility

---

## Manual Setup Required

To enable GitHub Pages, you need to configure it in the repository settings:

### Step 1: Enable GitHub Pages

1. Go to your repository on GitHub: https://github.com/SMRFORGE/smrforge
2. Click **Settings** (top menu)
3. Scroll down to **Pages** (left sidebar)
4. Under **Source**, select **GitHub Actions** (NOT "Deploy from a branch")
5. Click **Save**

### Step 2: Verify Deployment

After enabling GitHub Pages:

1. The workflow will run automatically on the next push to `main`
2. You can also trigger it manually:
   - Go to **Actions** tab
   - Select **Build and Deploy Documentation** workflow
   - Click **Run workflow**

3. Check deployment status:
   - Go to **Actions** tab
   - Look for **Build and Deploy Documentation** workflow
   - Wait for it to complete (usually 2-5 minutes)

4. Access your documentation:
   - URL: https://SMRFORGE.github.io/smrforge/
   - May take a few minutes after deployment completes

---

## How It Works

### Workflow Triggers

The documentation workflow runs automatically when:
- Code is pushed to `main` branch
- Files in `docs/` directory change
- Files in `smrforge/` directory change (affects API docs)
- Configuration files change (`README.md`, `pyproject.toml`, `setup.py`)
- Workflow is manually triggered via GitHub Actions UI

### Build Process

1. **Checkout code** - Gets latest code from repository
2. **Set up Python** - Installs Python 3.10
3. **Install dependencies** - Installs Sphinx and theme
4. **Install package** - Installs SMRForge in editable mode (for autodoc)
5. **Build documentation** - Runs `sphinx-build -b html . _build/html`
6. **Deploy to GitHub Pages** - Uploads built HTML to GitHub Pages

### Deployment

- Uses GitHub Actions Pages deployment (modern method)
- No need to commit to `gh-pages` branch
- Automatic versioning (always shows latest from `main`)

---

## Troubleshooting

### Documentation Not Appearing

1. **Check GitHub Pages is enabled:**
   - Settings > Pages > Source should be "GitHub Actions"

2. **Check workflow ran:**
   - Actions tab > Look for "Build and Deploy Documentation"
   - Should show green checkmark if successful

3. **Check for errors:**
   - Click on workflow run to see detailed logs
   - Common issues:
     - Import errors (missing dependencies)
     - Sphinx build errors (check `docs/conf.py`)
     - Permission errors (should be automatic with workflow)

### Build Failures

If the workflow fails:

1. **Check build logs:**
   - Actions tab > Failed workflow > Click on "Build Documentation" job
   - Look for error messages

2. **Common fixes:**
   - Missing dependencies: Add to `requirements.txt` or workflow
   - Import errors: Check `docs/conf.py` paths
   - Sphinx errors: Check RST file syntax

3. **Test locally:**
   ```bash
   cd docs
   pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
   sphinx-build -b html . _build/html
   ```

### URL Not Working

- GitHub Pages URLs are: `https://<username>.github.io/<repository>/`
- For this repo: `https://SMRFORGE.github.io/smrforge/`
- May take 5-10 minutes after first deployment
- Check repository Settings > Pages for the exact URL

---

## Manual Build (For Testing)

To test documentation build locally:

```bash
# Install dependencies
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Install package (for autodoc)
pip install -e .

# Build documentation
cd docs
sphinx-build -b html . _build/html

# View locally
# Open docs/_build/html/index.html in browser
```

---

## Updating Documentation

### Automatic Updates

Documentation automatically updates when:
- You push changes to `main` branch
- Changes affect `docs/` or `smrforge/` directories

### Manual Updates

To force a rebuild:
1. Go to **Actions** tab
2. Select **Build and Deploy Documentation**
3. Click **Run workflow** > **Run workflow**

---

## Documentation Structure

The documentation includes:
- **Installation Guide** - Setup instructions
- **Quick Start** - Getting started guide
- **API Reference** - Auto-generated from docstrings
- **Examples** - Code examples and tutorials
- **Contributing** - Development guidelines

All content is in the `docs/` directory:
- `index.rst` - Main documentation index
- `api/` - API reference (auto-generated)
- `examples/` - Example documentation
- `conf.py` - Sphinx configuration

---

## Next Steps

1. ✅ **Enable GitHub Pages** in repository settings (manual step)
2. ✅ **Wait for first deployment** (automatic after enabling)
3. ✅ **Verify documentation** is accessible at https://SMRFORGE.github.io/smrforge/
4. ✅ **Update links** if needed (already done in README.md)

---

## Notes

- **GitHub Pages is free** for public repositories
- **Build time**: Usually 2-5 minutes
- **Deployment**: Automatic after each push to main
- **Versioning**: Always shows latest from main branch
- **Alternative**: Read the Docs is still available as backup

---

*This setup provides automatic documentation deployment with zero maintenance after initial configuration.*

