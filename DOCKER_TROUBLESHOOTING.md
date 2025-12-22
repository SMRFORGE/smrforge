# Docker Troubleshooting Guide

## Common Build Issues

### Issue: `pip install` fails with exit code 1

This usually happens when a package fails to build. Common causes:

1. **Missing system dependencies** - Fixed in updated Dockerfile
2. **OpenMC installation failures** - OpenMC can be tricky to install

### Solution 1: Use the Updated Dockerfile

The main `Dockerfile` has been updated with all necessary system dependencies:
- HDF5 libraries (for h5py and OpenMC)
- CMake (for OpenMC)
- BLAS/LAPACK (for numpy/scipy)
- Build tools

Try building again:
```bash
docker-compose build --no-cache smrforge
docker-compose up -d smrforge
```

### Solution 2: Make OpenMC Optional

If OpenMC continues to cause issues, use the alternative Dockerfile that makes OpenMC optional:

```bash
# Update docker-compose.yml to use alternative Dockerfile
# Change line 7 from: dockerfile: Dockerfile
# To: dockerfile: Dockerfile.optional-openmc

docker-compose build --no-cache smrforge
docker-compose up -d smrforge
```

Or manually:
```bash
docker build -f Dockerfile.optional-openmc -t smrforge:latest .
```

### Solution 3: Remove OpenMC from Requirements

If you don't need OpenMC immediately, you can temporarily remove it:

1. Edit `requirements.txt` and comment out the OpenMC line:
   ```txt
   # openmc>=0.13.0
   ```

2. Rebuild:
   ```bash
   docker-compose build --no-cache smrforge
   ```

3. Install OpenMC later if needed (it's optional for basic functionality)

### Solution 4: Check the Actual Error

To see the exact error, build with verbose output:

```bash
docker-compose build smrforge 2>&1 | tee build.log
```

Or run the build step manually in a container:

```bash
docker run -it --rm python:3.11-slim bash
# Inside container:
apt-get update && apt-get install -y build-essential gfortran cmake pkg-config libhdf5-dev libhdf5-serial-dev libblas-dev liblapack-dev git
pip install --upgrade pip wheel setuptools
# Try installing packages one by one to identify the culprit
```

## Specific Package Issues

### OpenMC Installation Problems

OpenMC requires:
- CMake >= 3.10
- HDF5 development libraries
- C++ compiler with C++11 support
- Git (to clone dependencies)

The updated Dockerfile includes all of these. If it still fails:

1. Check OpenMC's official installation docs
2. Try installing from conda-forge instead (requires conda base image)
3. Use the optional-openmc Dockerfile variant

### h5py Installation Problems

h5py needs HDF5 development libraries. The Dockerfile includes:
- `libhdf5-dev`
- `libhdf5-serial-dev`

If h5py still fails, you may need to set environment variables:
```dockerfile
ENV HDF5_DIR=/usr/lib/x86_64-linux-gnu/hdf5/serial
```

### Numba Compilation Issues

Numba is optional for performance. If it fails:
1. The library still works without it (just slower)
2. Remove it from requirements.txt temporarily
3. Install later: `pip install numba`

## Network Issues

If packages fail to download:

1. Check Docker's network connectivity
2. Try building with `--network=host` (Linux only)
3. Use a proxy if behind corporate firewall

## Disk Space Issues

If build fails due to disk space:

```bash
# Clean up Docker
docker system prune -a

# Check disk space
docker system df
```

## Build Performance

To speed up rebuilds:

1. The Dockerfile uses layer caching (requirements installed before code copy)
2. Use BuildKit: `DOCKER_BUILDKIT=1 docker-compose build`
3. Use multi-stage builds for smaller final image

## Verifying Installation

After successful build, verify packages:

```bash
docker-compose exec smrforge python -c "import smrforge; print('OK')"
docker-compose exec smrforge python -c "import numpy, scipy, matplotlib, pandas; print('Core packages OK')"
docker-compose exec smrforge python -c "import openmc; print('OpenMC OK')" || echo "OpenMC not installed (optional)"
```

## Getting More Help

1. Check the full build log: `docker-compose build 2>&1 | tee build.log`
2. Run interactively to debug: `docker run -it --rm smrforge:latest bash`
3. Check package-specific documentation
4. Open an issue with the full error message

