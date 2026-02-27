# Air-Gap Bundle Scripts

Pre-stage wheels and Docker images for air-gapped SMRForge deployment.

## Usage

**From repo root (smrforge or smrforge-pro):**

```bash
# Bundle all Python wheels (deps + package)
./scripts/airgap/bundle_wheels.sh [OUTPUT_DIR]
# Default: ./offline-wheels

# Bundle Docker image
./scripts/airgap/bundle_docker.sh [OUTPUT_FILE]
# Default: ./smrforge-docker.tar
```

## On Air-Gapped Machine

**Wheels:**
```bash
pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt
pip install --no-index --find-links ./offline-wheels .
```

**Docker:**
```bash
docker load -i smrforge-docker.tar
docker run -v /path/to/ENDF:/app/endf-data:ro -e SMRFORGE_ENDF_DIR=/app/endf-data smrforge:latest
```

See [Air-Gapped Deployment](../../docs/guides/air-gapped-deployment.md) and [Pro Deployment](../../docs/deployment/air-gapped-pro.md) for full details.
