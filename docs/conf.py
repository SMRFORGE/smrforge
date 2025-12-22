"""
Sphinx configuration for SMRForge documentation.

To build documentation:
    pip install sphinx sphinx-rtd-theme
    cd docs
    sphinx-build -b html . _build/html
"""

import os
import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Project information
project = "SMRForge"
copyright = "2024, SMRForge Development Team"
author = "SMRForge Development Team"

# Get version from package
try:
    from smrforge import __version__
    version = __version__
    release = __version__
except ImportError:
    version = "0.1.0"
    release = "0.1.0"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

# Templates
templates_path = ["_templates"]

# Exclude patterns
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# HTML theme
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": True,
    "display_version": True,
    "collapse_navigation": False,
    "navigation_depth": 3,
}

# Logo for HTML output
html_logo = "logo/nukepy-logo.png"
html_favicon = "logo/nukepy-logo.png"

# Static files
html_static_path = ["_static"]

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
}

