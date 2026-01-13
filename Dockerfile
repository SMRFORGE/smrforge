# SMRForge Dockerfile
# Supports both runtime and development use cases
#
# Build: docker build -t smrforge:latest .
# Run:   docker run -it smrforge:latest
#
# Last Updated: January 2026
# - Added Dash web dashboard with dark/gray mode support
# - Added CLI command (smrforge serve) for dashboard
# - Added LWR SMR transient analysis (PWR/BWR/Integral SMR transients)
# - Added LWR SMR burnup features (gadolinium depletion, assembly/rod-wise tracking)
# - Added automated data downloader with parallel downloads and progress indicators
# - Added support for advanced features (visualization, mesh conversion, CAD import)
# - Includes optional dependencies for enhanced capabilities
# - Test coverage: 79.2% overall, 75-80%+ on priority modules

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
# Added libgl1 and libglib2.0-0 for pyvista visualization support
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    pkg-config \
    libhdf5-dev \
    libblas-dev \
    liblapack-dev \
    libxml2-dev \
    libpng-dev \
    libgl1 \
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

# Optional: Install visualization and dashboard dependencies
# Uncomment the next lines to include visualization, dashboard, mesh conversion, and CAD import support:
# RUN pip install --no-cache-dir \
#     plotly>=5.0 \
#     pyvista>=0.40.0 \
#     dash>=2.0 \
#     dash-bootstrap-components>=1.0.0 \
#     joblib>=1.0.0 \
#     meshio>=5.0.0 \
#     trimesh>=3.0.0
# Or install with [viz] extra (includes dashboard):
# RUN pip install --no-cache-dir -e ".[viz]"

# Copy examples (optional - can be mounted as volume instead)
COPY examples/ /app/examples/

# Create directories for data/output and ENDF storage
# ENDF data can be mounted as volume or stored in container
RUN mkdir -p /app/data /app/output /app/endf-data

# Set environment variable for standard ENDF directory
# Users can override this or mount their own ENDF directory
# Also supports configuration file: ~/.smrforge/config.yaml
ENV SMRFORGE_ENDF_DIR=/app/endf-data

# Default command (can be overridden)
# Note: ENDF files can be downloaded automatically using the data downloader
# Run: python -c \"from smrforge.data_downloader import download_endf_data; download_endf_data(library='ENDF/B-VIII.1', output_dir='/app/endf-data')\"
# Or set up manually: python -m smrforge.core.endf_setup
# 
# To run the web dashboard:
#   smrforge serve --host 0.0.0.0 --port 8050
#   Or: python -c \"from smrforge.gui import run_server; run_server(host='0.0.0.0', port=8050)\"
#   Then access at http://localhost:8050 (map port 8050 in docker run -p 8050:8050)
CMD ["python", "-c", "import smrforge as smr; print(f'SMRForge {smr.__version__} is ready!'); print('Features:'); print('  - Web Dashboard (smrforge serve) with dark/gray mode'); print('  - LWR SMR transient analysis (PWR/BWR/Integral SMR)'); print('  - LWR SMR burnup features (gadolinium depletion, assembly/rod tracking)'); print('  - Automated ENDF data downloader'); print('  - Advanced visualization, geometry import (OpenMC/Serpent/CAD/MCNP)'); print('  - Enhanced mesh generation'); print(''); print('ENDF Data Setup:'); print('  Option 1 (Recommended): Use data downloader'); print('    from smrforge.data_downloader import download_endf_data'); print('    download_endf_data(library=\"ENDF/B-VIII.1\", output_dir=\"/app/endf-data\")'); print('  Option 2: Manual setup'); print('    python -m smrforge.core.endf_setup'); print(''); print('Web Dashboard:'); print('  smrforge serve --host 0.0.0.0 --port 8050'); print('  Access at http://localhost:8050 (map port with -p 8050:8050)'); print(''); print('Optional dependencies:'); print('  - Dashboard & Visualization: pip install dash dash-bootstrap-components plotly pyvista'); print('  - Or install with [viz] extra: pip install -e \".[viz]\"'); print('  - Mesh conversion: pip install meshio joblib'); print('  - CAD import: pip install trimesh')"]

