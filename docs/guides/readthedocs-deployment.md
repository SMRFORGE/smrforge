# Read the Docs Deployment Guide (Community)

This guide walks you through deploying SMRForge Community documentation to [Read the Docs](https://readthedocs.org/).

## Prerequisites

- GitHub account with access to the [SMRFORGE/smrforge](https://github.com/SMRFORGE/smrforge) repository
- Repository must be **public** (Read the Docs free tier) or you need a Read the Docs paid plan for private repos

## Quick Deployment (5 minutes)

### Step 1: Sign in to Read the Docs

1. Go to [readthedocs.org](https://readthedocs.org/)
2. Click **Sign up** or **Log in**
3. Choose **Sign up with GitHub** (recommended) to connect your GitHub account

### Step 2: Import the Project

1. Click **Import a Project**
2. Find **SMRFORGE/smrforge** in the list (or use **Import manually** if it doesn't appear)
3. If importing manually:
   - **Repository URL**: `https://github.com/SMRFORGE/smrforge`
   - **Project name**: `smrforge` (this determines the URL: `smrforge.readthedocs.io`)
4. Click **Next** → **Create Project**

### Step 3: Verify Configuration

The repository includes `.readthedocs.yml`, so Read the Docs will automatically:

- Use Python 3.10
- Install the package with `pip install .[docs]` (Sphinx, theme, myst-parser)
- Build Sphinx docs from `docs/conf.py`
- Output HTML to the default location

**No manual configuration needed** unless you want to change defaults.

### Step 4: Wait for First Build

- First build typically takes **3–8 minutes** (installs dependencies + builds docs)
- Monitor progress on the project dashboard
- Build logs are available if something fails

### Step 5: Access Documentation

Once the build succeeds:

- **Latest (default branch)**: https://smrforge.readthedocs.io/en/latest/
- **Home**: https://smrforge.readthedocs.io/

## Configuration Reference

### `.readthedocs.yml` (repository root)

| Setting | Value | Purpose |
|--------|-------|---------|
| `build.os` | ubuntu-22.04 | Build environment |
| `build.tools.python` | 3.10 | Python version |
| `sphinx.configuration` | docs/conf.py | Sphinx config |
| `python.install` | `.[docs]` | Package + docs extra |

### Default Branch

By default, Read the Docs builds the **default branch** of the repo (usually `main`). To explicitly set it, uncomment in `.readthedocs.yml`:

```yaml
defaults:
  branches:
    latest: main
    stable: main
```

### Building Other Branches

- **Admin** → **Versions** → enable the branches you want (e.g. `fix/ci-numpy-build`)
- Each enabled branch gets a URL: `smrforge.readthedocs.io/en/<branch>/`

## Automatic Updates

Read the Docs automatically rebuilds when you:

- Push to the default branch
- Push to any enabled branch
- Create a new tag (if version builds are enabled)

Webhooks are set up automatically when you import via GitHub.

## Troubleshooting

### Build fails with "ModuleNotFoundError: smrforge"

- Ensure `pyproject.toml` has the `docs` extra with Sphinx dependencies
- Test locally: `pip install .[docs]` then `cd docs && sphinx-build -b html . _build/html`

### Build fails with "No module named 'sphinx_rtd_theme'"

- The `docs` extra in `pyproject.toml` must include `sphinx-rtd-theme>=1.0`
- Verify: `pip install .[docs]` and `python -c "import sphinx_rtd_theme"`

### Build times out (15 min default)

- Reduce optional dependencies in the docs build
- Add heavy packages to `autodoc_mock_imports` in `docs/conf.py` if they're not needed for doc generation

### Logo or static files missing

- Ensure `docs/logo/smrforge-logo.png` exists and is committed
- Check `html_static_path` and `html_logo` in `docs/conf.py`

### Test build locally

```powershell
# From repository root
pip install .[docs]
cd docs
sphinx-build -b html . _build/html
start _build/html/index.html
```

## Status Badge

Add to `README.md` to show build status:

```markdown
[![Documentation Status](https://readthedocs.org/projects/smrforge/badge/?version=latest)](https://smrforge.readthedocs.io/en/latest/?badge=latest)
```

## Links

- **Live docs**: https://smrforge.readthedocs.io/
- **Read the Docs docs**: https://docs.readthedocs.io/
- **Sphinx RTD theme**: https://sphinx-rtd-theme.readthedocs.io/
