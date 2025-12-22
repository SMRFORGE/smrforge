# SMRForge Dockerfile
# Supports both runtime and development use cases

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# OpenMC and scientific Python packages require various system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gfortran \
    cmake \
    pkg-config \
    libhdf5-dev \
    libblas-dev \
    liblapack-dev \
    libxml2-dev \
    libpng-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better layer caching)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
# Upgrade pip and install wheel first (helps with some packages)
RUN pip install --upgrade pip wheel setuptools

# Create a requirements file without OpenMC for core dependencies
# OpenMC is complex to build and may fail, so we install it separately
RUN grep -v "^openmc" requirements.txt > requirements-core.txt || true

# Install core dependencies first (without OpenMC)
RUN pip install --no-cache-dir -r requirements-core.txt

# Try to install OpenMC, but don't fail if it doesn't work
# This allows the container to build successfully even if OpenMC has issues
RUN pip install --no-cache-dir openmc>=0.13.0 || \
    echo "WARNING: OpenMC installation failed. Container will work but OpenMC features won't be available."

# Copy package files
COPY setup.py pyproject.toml /app/
COPY smrforge/ /app/smrforge/

# Install SMRForge in development mode
RUN pip install -e .

# Copy examples (optional - can be mounted as volume instead)
COPY examples/ /app/examples/

# Create a directory for data/output
RUN mkdir -p /app/data /app/output

# Default command (can be overridden)
CMD ["python", "-c", "import smrforge as smr; print(f'SMRForge {smr.__version__} is ready!')"]

