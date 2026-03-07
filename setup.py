"""
SMRForge setup configuration.

All package metadata, dependencies, extras, and entry points are defined in
pyproject.toml. This file is retained for setuptools compatibility and any
dynamic configuration (e.g., README_PYPI.md fallback).
"""

from pathlib import Path

from setuptools import setup


def _read_long_description() -> str:
    """Prefer a PyPI-safe README if present."""
    root = Path(__file__).parent
    for filename in ("README_PYPI.md", "README.md"):
        path = root / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


setup(
    long_description=_read_long_description(),
    long_description_content_type="text/markdown",
    include_package_data=True,
)
