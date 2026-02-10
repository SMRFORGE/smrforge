# Docker Usage Guide for SMRForge

**Last Updated:** February 10, 2026

This guide explains how to use SMRForge with Docker Desktop, including setup, usage, and troubleshooting.

## Prerequisites

- **Docker Desktop** installed and running
  - Windows: [Download Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
  - macOS: [Download Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
  - Linux: Install Docker Engine and Docker Compose

**Note**: This guide uses `docker compose` (with a space) which is the syntax for Docker Compose v2. If you're using Docker Compose v1, replace `docker compose` with `docker-compose` (with a hyphen) in all commands.

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Build and start the container:**
   ```bash
   docker compose up -d smrforge
   ```

2. **Open the dashboard (default):**
   - The `smrforge` service starts the Dash dashboard by default.
   - Visit `http://localhost:8050`

3. **Run commands interactively:**
   ```bash
   docker compose exec smrforge python -c "import smrforge as smr; print(smr.__version__)"
   ```

4. **Run an example:**
   ```bash
   docker compose exec smrforge python examples/complete_integration_example.py
   ```

5. **Access interactive Python shell:**
   ```bash
   docker compose exec smrforge python
   ```

### Option 2: Using Docker Directly

1. **Build the image:**
   ```bash
   docker build -t smrforge:latest .
   ```

2. **Run the dashboard (default):**
   ```bash
   docker run --rm \
     -p 8050:8050 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/output:/app/output \
     smrforge:latest
   ```

3. **Run a container for CLI / Python:**
   ```bash
   docker run -it --rm \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/output:/app/output \
     smrforge:latest python
   ```

## Development Mode

For development with live code editing:

```bash
# Start development container
docker compose up -d smrforge-dev

# Access bash shell
docker compose exec smrforge-dev bash

# Inside container, you can:
# - Edit code (changes reflect immediately via volume mount)
# - Run tests: pytest tests/
# - Run performance profiling: python scripts/profile_performance.py --function keff --mode both (see docs/development/memory-and-performance-assessment.md)
# - Format code: black .
# - Run type checking: mypy smrforge/
```

## Installing Optional Dependencies

The Docker images already include **core + dashboard/visualization** dependencies (installed from `requirements.txt`), including:

- `plotly`, `dash`, `dash-bootstrap-components`
- `matplotlib`
- `pyvista`
- `pint` (mandatory: unit checking and dimensional analysis)

SMRForge also supports **optional** features via pip extras (installed inside the container).

### Visualization dependencies

Visualization dependencies are **already included** in the images. The `.[viz]` extra is kept for backward compatibility and **does not install anything additional**.

```bash
# Optional: re-install the package (no extra deps are added)
docker compose exec smrforge pip install ".[viz]"
```

### Installing Other Optional Dependencies

```bash
# Uncertainty quantification
docker compose exec smrforge pip install ".[uq]"

# All optional dependencies
docker compose exec smrforge pip install ".[all]"
```

### Making Dependencies Persistent

If you want optional extras (like UQ) included in the image permanently, you can:

1. **Modify the Dockerfile** - add a `RUN pip install ".[uq]"` (or add packages to `requirements.txt`)
2. **Rebuild the image** - `docker compose build smrforge`

Or create a custom Dockerfile that includes the dependencies:

```dockerfile
FROM smrforge:latest
RUN pip install ".[uq]"
```

## Common Use Cases

### Running Analysis Scripts

```bash
# Method 1: Mount your script
docker run --rm \
  -v $(pwd)/my_analysis.py:/app/my_analysis.py \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/output:/app/output \
  smrforge:latest python my_analysis.py

# Method 2: Using docker compose
docker compose run --rm smrforge python /app/examples/complete_integration_example.py
```

### Jupyter Notebooks (Optional)

To use Jupyter notebooks, add to `docker-compose.yml`:

```yaml
  smrforge-jupyter:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/app/notebooks
      - ./data:/app/data
    command: bash -c "pip install jupyter && jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root"
```

Then run:
```bash
docker compose up smrforge-jupyter
# Access at http://localhost:8888
```

### Running Tests

```bash
# Recommended: use the dev container (includes pytest + tooling)
docker compose run --rm smrforge-dev pytest tests/

# With coverage
docker compose run --rm smrforge-dev pytest --cov=smrforge tests/
```

## Directory Structure

The Docker setup mounts the following directories:

- `/app/data` - Input data files (mapped to `./data/` on host)
- `/app/output` - Output files (mapped to `./output/` on host)
- `/app/examples` - Example scripts (read-only)
- `/app/endf-data` - ENDF nuclear data files (optional, see ENDF Data Storage below)

Create these directories on your host if they don't exist:
```bash
mkdir -p data output
```

## ENDF Data Storage

SMRForge supports bulk ENDF file storage for faster, offline access to nuclear data. You can mount your local ENDF data directory into the container.

### Using Local ENDF Data

1. **Mount your ENDF directory** in `docker-compose.yml`:
   ```yaml
   volumes:
     # Mount local ENDF data directory
     - ~/ENDF-Data:/app/endf-data:ro
     # Or mount a specific ENDF directory:
     # - /path/to/ENDF-B-VIII.1:/app/endf-data:ro
   ```

2. **Use in your code**:
   ```python
   from pathlib import Path
   from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
   
   # Use mounted ENDF directory
   cache = NuclearDataCache(
       local_endf_dir=Path("/app/endf-data")
   )
   
   # Files are automatically discovered
   u235 = Nuclide(Z=92, A=235, m=0)
   energy, xs = cache.get_cross_section(u235, "fission", library=Library.ENDF_B_VIII_1)
   ```

### Organizing Bulk Downloads

If you've downloaded ENDF files in bulk, organize them inside the container:

```bash
# Access container
docker compose exec smrforge-dev bash

# Inside container, organize bulk downloads
python -c "
from pathlib import Path
from smrforge.core.reactor_core import organize_bulk_endf_downloads

stats = organize_bulk_endf_downloads(
    source_dir=Path('/app/endf-data/raw'),
    target_dir=Path('/app/endf-data'),
    library_version='VIII.1'
)
print(f'Organized {stats[\"files_organized\"]} files')
"
```

### Setup Wizard (Recommended)

**IMPORTANT**: ENDF files must be set up manually. Use the interactive setup wizard:

```bash
# Run setup wizard inside container
docker compose exec smrforge python -m smrforge.core.endf_setup

# Or use command-line tool (if installed)
docker compose exec smrforge smrforge-setup-endf
```

The wizard will:
- Guide you through locating or downloading ENDF files
- Validate all files
- Organize files into standard structure
- Test the setup

See [`docs/technical/endf-documentation.md`](docs/technical/endf-documentation.md) for complete documentation on ENDF data setup, bulk storage, and Docker integration.

## Environment Variables

You can set environment variables in `docker-compose.yml`:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - SMRFORGE_DATA_PATH=/app/data/nuclear_data
  # Optional: set custom ENDF directory path
  - SMRFORGE_ENDF_DIR=/app/endf-data
  # Optional: override headless visualization defaults
  - MPLBACKEND=Agg
  - PYVISTA_OFF_SCREEN=true
```

## Troubleshooting

### Common Build Issues

#### Issue: `apt-get install` fails with exit code 100

If you see errors like "Package 'libgl1-mesa-glx' has no installation candidate":

1. **Debian Trixie compatibility** - The Dockerfile uses `libgl1` instead of `libgl1-mesa-glx` for Debian Trixie (used by python:3.11-slim). This package provides OpenGL support for pyvista visualization.

2. **Update to latest Dockerfile** - Ensure you're using the latest version of the Dockerfile, which includes:
   - `DEBIAN_FRONTEND=noninteractive` for better error handling
   - `libgl1` package (replaces deprecated `libgl1-mesa-glx`)

3. **Rebuild from scratch**:
   ```bash
   docker compose build --no-cache smrforge
   docker compose up -d smrforge
   ```

#### Issue: `pip install` fails with exit code 1

This usually happens when a package fails to build. Common causes:

1. **Missing system dependencies** - The Dockerfile includes all necessary dependencies, but try rebuilding with no cache:
   ```bash
   docker compose build --no-cache smrforge
   docker compose up -d smrforge
   ```

2. **Package installation failures** - If optional packages fail to install, the container will still build. SMRForge includes a built-in ENDF parser and works without optional dependencies.

#### Issue: Container won't start

Check Docker Desktop is running and has enough resources allocated:
- Docker Desktop → Settings → Resources
- Recommended: 4GB RAM, 2 CPUs minimum

#### Issue: Permission issues (Linux/macOS)

If you get permission errors when mounting volumes:
```bash
# Fix ownership (run on host)
sudo chown -R $USER:$USER data output
```

#### Issue: Import errors

Make sure the container has the latest code:
```bash
docker compose build --no-cache smrforge
docker compose up -d smrforge
```

#### Issue: Slow performance

Docker volume mounts can be slow on Windows/macOS. Consider:
- Using Docker volumes instead of bind mounts for large datasets
- Running on Linux for better I/O performance

### Specific Package Issues

#### h5py Installation Problems

h5py needs HDF5 development libraries. The Dockerfile includes:
- `libhdf5-dev`

If h5py still fails, you may need to set environment variables:
```dockerfile
ENV HDF5_DIR=/usr/lib/x86_64-linux-gnu/hdf5/serial
```

#### OpenGL/Visualization Packages

The Dockerfile includes OpenGL libraries for pyvista visualization support:
- `libgl1` - OpenGL library (replaces deprecated `libgl1-mesa-glx` in Debian Trixie)
- `libglib2.0-0` - GLib library

If visualization features don't work, ensure these packages are installed in the container.

#### Numba Compilation Issues

Numba is optional for performance. If it fails:
1. The library still works without it (just slower)
2. Remove it from requirements.txt temporarily
3. Install later: `pip install numba`

### Network Issues

If packages fail to download:
1. Check Docker's network connectivity
2. Try building with `--network=host` (Linux only)
3. Use a proxy if behind corporate firewall

### Disk Space Issues

If build fails due to disk space:

```bash
# Clean up Docker
docker system prune -a

# Check disk space
docker system df
```

### Build Performance

To speed up rebuilds:

1. The Dockerfile uses layer caching (requirements installed before code copy)
2. Use BuildKit: `DOCKER_BUILDKIT=1 docker compose build`
3. Use multi-stage builds for smaller final image

### Verifying Installation

After successful build, verify packages:

```bash
docker compose exec smrforge python -c "import smrforge; print('OK')"
docker compose exec smrforge python -c "import numpy, scipy, matplotlib, pandas; print('Core packages OK')"
docker compose exec smrforge python -c "import requests, httpx, tqdm, yaml, pint; print('Downloader/config/units deps OK')"
docker compose exec smrforge python -c "import sandy; print('SANDY OK')" || echo "SANDY not installed (optional)"
docker compose exec smrforge python -c "import rich; print('Rich OK')"
```

When running interactively, console logging is colorized via Rich. To disable colors (e.g., in CI), set `NO_COLOR=1`.

### Getting More Help

1. Check the full build log: `docker compose build 2>&1 | tee build.log`
2. Run interactively to debug: `docker run -it --rm smrforge:latest bash`
3. Check package-specific documentation
4. Open an issue with the full error message

## Cleaning Up

```bash
# Stop containers
docker compose down

# Remove containers and volumes
docker compose down -v

# Remove images
docker compose down --rmi all

# Full cleanup (containers, images, volumes)
docker system prune -a
```

## Advanced Usage

### Multi-stage Build (Smaller Image)

For production deployments, you might want a smaller image. Create `Dockerfile.prod`:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY smrforge/ /app/smrforge/
COPY setup.py pyproject.toml README.md README_PYPI.md MANIFEST.in /app/
RUN pip install --no-cache-dir --no-deps .
CMD ["python", "-c", "import smrforge; print('SMRForge ready')"]
```

### GPU Support (for future ML features)

If you need GPU support (e.g., for PyTorch/TensorFlow in future ML modules):

```yaml
# docker-compose.yml
services:
  smrforge-gpu:
    # ... other config ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Examples

See the `examples/` directory for sample scripts that work with Docker:

```bash
# Run complete integration example
docker compose run --rm smrforge python examples/complete_integration_example.py

# Run safety/UQ example
docker compose run --rm smrforge python examples/integrated_safety_uq.py
```

---

**Note**: This Docker setup is optimized for ease of use. For production deployments, consider additional security hardening and optimizations.

