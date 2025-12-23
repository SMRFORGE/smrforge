# SMRForge Documentation

This directory contains the Sphinx documentation for SMRForge.

## Building Documentation

### Prerequisites

Install Sphinx and the required theme:

```bash
pip install sphinx sphinx-rtd-theme
```

### Build HTML Documentation

```bash
cd docs
sphinx-build -b html . _build/html
```

Or use make (if available):

```bash
cd docs
make html
```

### View Documentation

Open `_build/html/index.html` in your web browser.

## Documentation Structure

- `index.rst` - Main documentation page
- `quickstart.rst` - Quick start guide
- `installation.rst` - Installation instructions
- `api_reference.rst` - API reference (to be generated)
- `examples.rst` - Example documentation

## Generating API Documentation

To generate API documentation from source code:

```bash
cd docs
sphinx-apidoc -o api ../smrforge --separate
sphinx-build -b html . _build/html
```

This will create API documentation for all modules in `smrforge/`.

## Deployment

Documentation can be deployed to:

- **Read the Docs**: Connect GitHub repository to Read the Docs
- **GitHub Pages**: Use GitHub Actions to build and deploy
- **Local**: Build locally and serve

See Sphinx documentation for more deployment options.

