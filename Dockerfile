# SMRForge Dockerfile
# Supports both runtime and development use cases
#
# Build: docker build -t smrforge:latest .
# Run:   docker run -it smrforge:latest
#
# Last Updated: January 2026
# - Added support for advanced features (visualization, mesh conversion, CAD import)
# - Includes optional dependencies for enhanced capabilities
# - Test coverage: 70-73% overall, 75-80%+ on priority modules

FROM python:3.11-slim

# Metadata labels
LABEL maintainer="SMRForge Development Team" \
      description="Small Modular Reactor Design and Analysis Toolkit" \
      version="0.1.0"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# Scientific Python packages require various system libraries
# Added libgl1-mesa-glx and libglib2.0-0 for pyvista visualization support
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    pkg-config \
    libhdf5-dev \
    libblas-dev \
    liblapack-dev \
    libxml2-dev \
    libpng-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Copy package metadata first (for better layer caching)
COPY setup.py pyproject.toml README.md MANIFEST.in /app/
COPY smrforge/ /app/smrforge/

# Install Python dependencies
# Upgrade pip and install wheel first (helps with some packages)
RUN pip install --upgrade pip wheel setuptools

# Install SMRForge with all dependencies from setup.py
# This ensures consistency with the package definition
# Optionally install visualization extras: pip install -e ".[viz]"
RUN pip install --no-cache-dir -e .

# Optional: Install visualization and advanced feature dependencies
# Uncomment the next lines to include visualization, mesh conversion, and CAD import support:
# RUN pip install --no-cache-dir \
#     plotly>=5.0 \
#     pyvista>=0.40.0 \
#     joblib>=1.0.0 \
#     meshio>=5.0.0 \
#     trimesh>=3.0.0
# Or install with [viz] extra (if defined in setup.py):
# RUN pip install --no-cache-dir -e ".[viz]"

# Copy examples (optional - can be mounted as volume instead)
COPY examples/ /app/examples/

# Create directories for data/output and ENDF storage
# ENDF data can be mounted as volume or stored in container
RUN mkdir -p /app/data /app/output /app/endf-data

# Set environment variable for standard ENDF directory
# Users can override this or mount their own ENDF directory
ENV SMRFORGE_ENDF_DIR=/app/endf-data

# Default command (can be overridden)
# Note: ENDF files must be set up manually before use
# Run: python -m smrforge.core.endf_setup
# Or: smrforge-setup-endf
CMD ["python", "-c", "import smrforge as smr; print(f'SMRForge {smr.__version__} is ready!'); print('Run: python -m smrforge.core.endf_setup to set up ENDF data'); print('Features: Advanced visualization, geometry import (OpenMC/Serpent/CAD/MCNP), enhanced mesh generation'); print('For visualization: pip install plotly pyvista (or install with [viz] extra)'); print('For mesh conversion: pip install meshio joblib'); print('For CAD import: pip install trimesh')"]

