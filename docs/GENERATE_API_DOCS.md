# Generating API Documentation

This guide explains how to generate the Sphinx API documentation for SMRForge.

## Prerequisites

Install Sphinx and required extensions:

```bash
pip install sphinx sphinx-rtd-theme
```

Or with documentation dependencies:

```bash
pip install -e ".[docs]"
```

## Generate API Documentation

### Option 1: Using Scripts

**On Linux/macOS:**
```bash
chmod +x docs/generate_api_docs.sh
./docs/generate_api_docs.sh
```

**On Windows:**
```cmd
docs\generate_api_docs.bat
```

### Option 2: Manual Steps

1. **Generate API documentation files:**

   ```bash
   cd docs
   sphinx-apidoc -o api ../smrforge --separate --module-first
   ```

   This creates `docs/api/` directory with `.rst` files for each module.

2. **Build HTML documentation:**

   ```bash
   sphinx-build -b html . _build/html
   ```

3. **View documentation:**

   Open `docs/_build/html/index.html` in your web browser.

### Option 3: Using Make (if available)

```bash
cd docs
make html
```

## Update API Reference Index

After generating API docs, update `docs/api_reference.rst` to include new modules:

```rst
.. toctree::
   :maxdepth: 2

   api/smrforge.core
   api/smrforge.neutronics
   api/smrforge.thermal
   ...
```

## Automated Generation

### CI/CD Integration

To auto-generate docs in CI/CD, add to `.github/workflows/ci.yml`:

```yaml
- name: Generate API docs
  run: |
    pip install sphinx sphinx-rtd-theme
    cd docs
    sphinx-apidoc -o api ../smrforge --separate
    sphinx-build -b html . _build/html
```

### GitHub Pages Deployment

To deploy docs to GitHub Pages:

1. Generate docs (as above)
2. Copy `_build/html` contents to `docs/` directory
3. Enable GitHub Pages in repository settings
4. Select `docs/` folder as source

Or use GitHub Actions to auto-deploy on release.

## Troubleshooting

### Missing Modules

If some modules are missing from generated docs:
- Ensure module has proper `__init__.py`
- Check that module is importable: `python -c "import smrforge.module"`

### Import Errors

If you get import errors during generation:
- Ensure all dependencies are installed
- Check that package is installed: `pip install -e .`

### Build Errors

Common issues:
- **Missing extensions**: Install required Sphinx extensions
- **Theme issues**: Ensure `sphinx-rtd-theme` is installed
- **Logo missing**: Ensure `docs/logo/smrforge-logo.png` exists

## Next Steps

After generating docs:
1. Review generated `.rst` files in `docs/api/`
2. Add custom documentation where needed
3. Update `docs/index.rst` if needed
4. Deploy to GitHub Pages or Read the Docs

