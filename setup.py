"""
SMRForge setup configuration
"""

from pathlib import Path

from setuptools import find_packages, setup


def _read_long_description() -> str:
    """Prefer a PyPI-safe README if present."""
    root = Path(__file__).parent
    for filename in ("README_PYPI.md", "README.md"):
        path = root / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


long_description = _read_long_description()

setup(
    name="smrforge",
    version="0.1.0",
    author="SMRForge Development Team",
    author_email="your.email@example.com",
    description="Small Modular Reactor Design and Analysis Toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SMRFORGE/smrforge",
    packages=find_packages(exclude=["tests", "docs", "examples"]),
    package_data={
        # Include logo in package if needed
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "pyyaml>=6.0",  # YAML config (cli, workflows.templates, parameter_sweep)
        "requests>=2.25.0",  # Nuclear data downloads (data_downloader)
        "pint>=0.20.0",  # Required for unit checking (smrforge.utils.units)
        "pandas>=1.3.0",
        "h5py>=3.0.0",
        "scikit-learn>=1.0.0",
        # Performance and optimization
        "numba>=0.56.0",
        # Data storage
        "zarr>=2.14.0",
        # Fast dataframes
        "polars>=0.19.0",
        # Terminal formatting
        "rich>=13.0.0",
        # Visualization and dashboard (required)
        "plotly>=5.0",
        "pyvista>=0.40.0",
        "dash>=2.0",
        "dash-bootstrap-components>=1.0.0",
        # Uncertainty quantification and sensitivity analysis (required)
        "SALib>=1.4.0",
        # Statistical visualization for UQ (required)
        "seaborn>=0.12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
        "docs": [
            "sphinx>=4.5",
            "sphinx-rtd-theme>=1.0",
            "sphinx-autodoc-typehints>=1.18",
            "myst-parser>=2.0.0",
        ],
        "viz": [
            # Visualization dependencies are now required (moved to install_requires)
            # This extra is kept for backward compatibility but installs nothing additional
        ],
        "nuclear-data": [
            # Optional nuclear data backends
            "sandy",  # Lighter-weight alternative for ENDF parsing
        ],
        "uq": [
            # UQ extras (SALib and seaborn are now required in install_requires)
        ],
        "all": [
            # Install all optional dependencies
            # Note: Visualization (plotly, pyvista, dash), SALib and seaborn are now required
            "sandy",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="nuclear reactor simulation SMR neutronics thermal-hydraulics",
    entry_points={
        "console_scripts": [
            "smrforge-setup-endf=smrforge.core.endf_setup:setup_endf_data_interactive",
            "smrforge=smrforge.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/SMRFORGE/smrforge/issues",
        "Source": "https://github.com/SMRFORGE/smrforge",
        "Documentation": "https://smrforge.readthedocs.io",
    },
)
