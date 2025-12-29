# ReadTheDocs Setup Guide for SMRForge

This guide explains how to set up SMRForge documentation on ReadTheDocs.io.

## Quick Setup

### 1. Create ReadTheDocs Account

1. Go to [ReadTheDocs.org](https://readthedocs.org/)
2. Sign up / Log in with your GitHub account
3. Click "Import a Project" and select your GitHub repository

### 2. Configure the Project

The repository already includes `.readthedocs.yml` which configures:
- Python version (3.10)
- Build system (Sphinx)
- Configuration file location (`docs/conf.py`)
- Dependencies (installs package with `[docs]` extra)

**No additional configuration needed in the ReadTheDocs web interface!**

### 3. Build Settings (Automatic)

ReadTheDocs will automatically:
- Detect the `.readthedocs.yml` file
- Install dependencies via `pip install -e ".[docs]"`
- Build documentation using Sphinx
- Generate API documentation from docstrings

### 4. Access Documentation

After the first build completes, your documentation will be available at:
- **Default URL**: `https://smrforge.readthedocs.io/`
- **Latest version**: `https://smrforge.readthedocs.io/en/latest/`

## Configuration Files

### `.readthedocs.yml`

Located in the repository root, this file configures:
- Build environment (Ubuntu 22.04, Python 3.10)
- Sphinx configuration file (`docs/conf.py`)
- Installation method (pip with `[docs]` extra)

### `docs/conf.py`

Sphinx configuration that:
- Sets project metadata
- Configures extensions (autodoc, napoleon, etc.)
- Sets up theme (ReadTheDocs theme)
- Configures logo and static files
- Sets up intersphinx mappings

## Manual Configuration (If Needed)

If you prefer to configure via the web interface:

1. **Admin Settings** → **Advanced Settings**:
   - **Python configuration file**: Leave empty (uses `.readthedocs.yml`)
   - **Requirements file**: Leave empty (uses setup.py extras)
   - **Use system packages**: Unchecked
   - **Install Project**: Checked (reads from `.readthedocs.yml`)

2. **Versions**:
   - Default branch: `main` (or `master`)
   - Enable versions for branches/tags as needed

## Building API Documentation

The documentation includes API reference automatically generated from docstrings.

To regenerate API documentation files manually:

```bash
cd docs
sphinx-apidoc -o api ../smrforge --separate --module-first
```

This is typically done automatically during the build, but you can commit these files to the repository if you want to track them in version control.

## Updating Documentation

Documentation updates automatically when you:

1. Push changes to your repository
2. ReadTheDocs triggers a new build
3. Build completes (usually 1-5 minutes)

To manually trigger a build:
- Go to project page on ReadTheDocs
- Click "Build version" → Select branch/tag

## Troubleshooting

### Build Failures

**Common issues:**

1. **Import errors**:
   - Check that all dependencies are in `setup.py` `install_requires` or `extras_require["docs"]`
   - Verify package can be imported: `python -c "import smrforge"`

2. **Missing modules**:
   - Some optional dependencies may need to be in `autodoc_mock_imports` in `conf.py`
   - Or add to `extras_require["docs"]` if they're needed for building

3. **Sphinx errors**:
   - Check build logs in ReadTheDocs dashboard
   - Test build locally: `cd docs && sphinx-build -b html . _build/html`

### Testing Locally

Test that documentation builds correctly:

```bash
# Install dependencies
pip install -e ".[docs]"

# Build documentation
cd docs
sphinx-build -b html . _build/html

# View in browser
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
start _build/html/index.html  # Windows
```

### Version Control

**Recommended:** Don't commit `docs/_build/` or `docs/api/` directories (unless you want to track generated files).

Add to `.gitignore`:
```
docs/_build/
docs/api/*.rst  # If auto-generated
```

ReadTheDocs will generate these during the build.

## Customization

### Change Theme

Edit `docs/conf.py`:

```python
html_theme = "sphinx_rtd_theme"  # Current theme
# Or use another theme like:
# html_theme = "alabaster"
# html_theme = "sphinx_book_theme"
```

### Add Custom CSS

1. Create `docs/_static/custom.css`
2. Add custom styles
3. Reference in `conf.py`:

```python
html_static_path = ["_static"]
html_css_files = ["custom.css"]
```

### Enable PDF/EPUB Output

ReadTheDocs supports multiple output formats:
- HTML (default)
- PDF
- EPUB

Configure in ReadTheDocs project settings → **Formats**.

## Status Badge

Add a status badge to your README:

```markdown
[![Documentation Status](https://readthedocs.org/projects/smrforge/badge/?version=latest)](https://smrforge.readthedocs.io/en/latest/?badge=latest)
```

## Subdomains

ReadTheDocs provides:
- Default: `https://smrforge.readthedocs.io/`
- Custom domain: Configure in project settings (requires DNS setup)

## Next Steps

After setup:
1. Verify documentation builds successfully
2. Review generated API documentation
3. Add a status badge to README.md
4. Link to documentation in project description
5. Set up automatic builds on commits

## Additional Resources

- [ReadTheDocs Documentation](https://docs.readthedocs.io/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Sphinx RTD Theme](https://sphinx-rtd-theme.readthedocs.io/)

## Support

If you encounter issues:
1. Check build logs in ReadTheDocs dashboard
2. Test build locally
3. Review [ReadTheDocs troubleshooting guide](https://docs.readthedocs.io/en/stable/troubleshooting.html)
4. Check SMRForge GitHub issues

