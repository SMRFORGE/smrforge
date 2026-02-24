# SMRForge Pro Dockerfile
# Licensed tier with AI/surrogate, full converters, validation reports, ML export.
#
# Build: docker build -f Dockerfile.pro -t smrforge-pro:latest .
# Run:   docker run -it smrforge-pro:latest
#
# Requires: SMRForge Pro license for production use.
# Last Updated: February 2026
# Tier: Pro (SMRFORGE_TIER=pro)
# Includes: Serpent/MCNP converters, OpenMC tally viz, AI/surrogate, validation reports, ML export,
# natural-language design, code-to-code verification, regulatory package, benchmark reproduction,
# multi-objective optimization, physics-informed surrogates.

FROM python:3.11-slim

LABEL maintainer="SMRForge Development Team" \
      description="SMRForge Pro - AI/surrogate, Serpent/MCNP converters, validation reports, ML export" \
      version="0.1.0" \
      org.opencontainers.image.title="SMRForge Pro" \
      org.opencontainers.image.description="SMRForge Pro - licensed tier with full converters and AI workflows"

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLBACKEND=Agg \
    PYVISTA_OFF_SCREEN=true \
    SMRFORGE_TIER=pro

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
    libgomp1 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy manifests and install Community first
COPY requirements.txt requirements-lock.txt /app/
ARG USE_LOCKED=0
RUN pip install --upgrade pip wheel setuptools && \
    if [ "$USE_LOCKED" = "1" ]; then pip install --no-cache-dir -r /app/requirements-lock.txt; \
    else pip install --no-cache-dir -r /app/requirements.txt; fi

# Copy repo (Community + Pro)
COPY setup.py pyproject.toml README.md MANIFEST.in /app/
COPY smrforge/ /app/smrforge/
COPY smrforge_pro/ /app/smrforge_pro/
COPY scripts/ /app/scripts/
COPY examples/ /app/examples/

# Install Community
RUN pip install --no-cache-dir .

# Install Pro with extras (ai, reporting, ml, openmc for tally viz)
RUN pip install --no-cache-dir -e "./smrforge_pro[ai,reporting,ml,openmc]"

RUN mkdir -p /app/data /app/output /app/results /app/endf-data
ENV SMRFORGE_ENDF_DIR=/app/endf-data

EXPOSE 8050

# Pro features: convert (serpent, openmc, mcnp), visualize tally, workflow surrogate, ml-export, report validation
# smrforge convert serpent --reactor valar-10 --output reactor.serp
# smrforge convert mcnp --reactor valar-10 --output reactor.mcnp
# smrforge visualize tally --statepoint statepoint.10.h5 --output tally.html
# smrforge workflow surrogate --sweep-results sweep.json --params enrichment power --output surr.pkl
# smrforge workflow ml-export --results sweep.json --output design.parquet
# smrforge report validation --predictions pred.txt --reference ref.txt --output report.json --pdf
# Pro workflows: nl-design, code-verify, regulatory-package, benchmark, multi-optimize
# smrforge workflow nl-design --text "10 MW HTGR"
# smrforge workflow code-verify --reactor valar-10 --output verification_output
# smrforge workflow regulatory-package --reactor valar-10 --output regulatory_package
# smrforge workflow benchmark --id valar10_preset --output benchmark_output
CMD ["smrforge", "serve", "--host", "0.0.0.0", "--port", "8050"]
