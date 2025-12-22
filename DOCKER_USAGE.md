# Docker Usage Guide for SMRForge

This guide explains how to use SMRForge with Docker Desktop.

## Prerequisites

- **Docker Desktop** installed and running
  - Windows: [Download Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
  - macOS: [Download Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
  - Linux: Install Docker Engine and Docker Compose

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Build and start the container:**
   ```bash
   docker-compose up -d smrforge
   ```

2. **Run commands interactively:**
   ```bash
   docker-compose exec smrforge python -c "import smrforge as smr; print(smr.__version__)"
   ```

3. **Run an example:**
   ```bash
   docker-compose exec smrforge python examples/complete_integration_example.py
   ```

4. **Access interactive Python shell:**
   ```bash
   docker-compose exec smrforge python
   ```

### Option 2: Using Docker Directly

1. **Build the image:**
   ```bash
   docker build -t smrforge:latest .
   ```

2. **Run a container:**
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
docker-compose up -d smrforge-dev

# Access bash shell
docker-compose exec smrforge-dev bash

# Inside container, you can:
# - Edit code (changes reflect immediately via volume mount)
# - Run tests: pytest tests/
# - Format code: black .
# - Run type checking: mypy smrforge/
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

# Method 2: Using docker-compose
docker-compose run --rm smrforge python /app/examples/complete_integration_example.py
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
docker-compose up smrforge-jupyter
# Access at http://localhost:8888
```

### Running Tests

```bash
# Install dev dependencies first
docker-compose run --rm smrforge pip install -e ".[dev]"

# Run tests
docker-compose run --rm smrforge pytest tests/

# Run with coverage
docker-compose run --rm smrforge pytest --cov=smrforge tests/
```

## Directory Structure

The Docker setup mounts the following directories:

- `/app/data` - Input data files (mapped to `./data/` on host)
- `/app/output` - Output files (mapped to `./output/` on host)
- `/app/examples` - Example scripts (read-only)

Create these directories on your host if they don't exist:
```bash
mkdir -p data output
```

## Environment Variables

You can set environment variables in `docker-compose.yml`:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - OPENMC_DATA_PATH=/app/data/nuclear_data
```

## Troubleshooting

### Container won't start

Check Docker Desktop is running and has enough resources allocated:
- Docker Desktop → Settings → Resources
- Recommended: 4GB RAM, 2 CPUs minimum

### Permission issues (Linux/macOS)

If you get permission errors when mounting volumes:
```bash
# Fix ownership (run on host)
sudo chown -R $USER:$USER data output
```

### Import errors

Make sure the container has the latest code:
```bash
docker-compose build --no-cache smrforge
docker-compose up -d smrforge
```

### Slow performance

Docker volume mounts can be slow on Windows/macOS. Consider:
- Using Docker volumes instead of bind mounts for large datasets
- Running on Linux for better I/O performance

## Cleaning Up

```bash
# Stop containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

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
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY smrforge/ /app/smrforge/
COPY setup.py /app/
RUN pip install -e . && \
    rm -rf /root/.cache
ENV PATH=/root/.local/bin:$PATH
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
docker-compose run --rm smrforge python examples/complete_integration_example.py

# Run safety/UQ example
docker-compose run --rm smrforge python examples/integrated_safety_uq.py
```

---

**Note**: This Docker setup is optimized for ease of use. For production deployments, consider additional security hardening and optimizations.

