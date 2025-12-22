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
# OpenMC may need some build tools, but we'll try without first
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better layer caching)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

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

