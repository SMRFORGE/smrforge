"""
SMRForge setup configuration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="smrforge",
    version="0.1.0",
    author="SMRForge Development Team",
    author_email="your.email@example.com",
    description="Small Modular Reactor Design and Analysis Toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smrforge",
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
        "pandas>=1.3.0",
        "h5py>=3.0.0",
        "scikit-learn>=1.0.0",
        # Performance and optimization
        "numba>=0.56.0",
        # Data storage
        "zarr>=2.14.0",
        # Fast dataframes
        "polars>=0.19.0",
        # Nuclear data handling
        "openmc>=0.13.0",
        # Terminal formatting
        "rich>=13.0.0",
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
        ],
        "viz": [
            "plotly>=5.0",
            "dash>=2.0",
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
    project_urls={
        "Bug Reports": "https://github.com/yourusername/smrforge/issues",
        "Source": "https://github.com/yourusername/smrforge",
        "Documentation": "https://smrforge.readthedocs.io",
    },
)
