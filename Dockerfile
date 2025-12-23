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
# Scientific Python packages require various system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    pkg-config \
    libhdf5-dev \
    libblas-dev \
    liblapack-dev \
    libxml2-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better layer caching)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
# Upgrade pip and install wheel first (helps with some packages)
RUN pip install --upgrade pip wheel setuptools

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy package files
COPY setup.py pyproject.toml README.md /app/
COPY smrforge/ /app/smrforge/

# Install SMRForge in development mode
# Use --no-deps since we've already installed all dependencies above
RUN pip install --no-deps -e .

# Copy examples (optional - can be mounted as volume instead)
COPY examples/ /app/examples/

# Create a directory for data/output
RUN mkdir -p /app/data /app/output

# Default command (can be overridden)
CMD ["python", "-c", "import smrforge as smr; print(f'SMRForge {smr.__version__} is ready!')"]

