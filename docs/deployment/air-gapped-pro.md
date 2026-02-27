# Air-Gapped Deployment — SMRForge Pro

**Audience:** Pro customers deploying in regulated, air-gapped environments.  
**Repo:** Pro code and bundles live in [smrforge-pro](https://github.com/SMRFORGE/smrforge-pro).

---

## Overview

Pro supports full air-gapped deployment: wheels, Docker images, and nuclear data can be pre-staged on a connected machine and transferred via approved process. Licensing validation runs offline (RSA-signed keys, no phone-home).

---

## Option 1: Wheel Bundle (Recommended)

**On connected machine (with Pro access):**

```bash
# From smrforge-pro repo root
cd /path/to/smrforge-pro
./scripts/airgap/bundle_wheels.sh ./offline-wheels

# Or manually:
mkdir -p offline-wheels
pip download -r requirements-lock.txt -d ./offline-wheels
pip download . -d ./offline-wheels
pip download smrforge -d ./offline-wheels   # Community dependency
```

**Transfer** the `offline-wheels/` directory to the air-gapped system.

**On air-gapped machine:**

```bash
pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt
pip install --no-index --find-links ./offline-wheels smrforge
pip install --no-index --find-links ./offline-wheels .
```

---

## Option 2: Docker Image Transfer

**On connected machine:**

```bash
cd /path/to/smrforge-pro
./scripts/airgap/bundle_docker.sh ./smrforge-pro-1.0.tar

# Or manually:
docker build --build-arg USE_LOCKED=1 -f Dockerfile.pro -t smrforge-pro:1.0 .
docker save smrforge-pro:1.0 -o smrforge-pro-1.0.tar
```

**Transfer** the `.tar` file. **On air-gapped machine:**

```bash
docker load -i smrforge-pro-1.0.tar
docker run -v /path/to/ENDF:/app/endf-data:ro \
  -e SMRFORGE_ENDF_DIR=/app/endf-data \
  smrforge-pro:1.0 smrforge serve --host 0.0.0.0 --port 8050
```

---

## Option 3: GitHub Release Bundle

When Pro releases are tagged, an automated workflow can attach an air-gap bundle to the GitHub Release:

- `smrforge-pro-airgap-v1.0.0.zip` — wheels + install instructions
- Optional: `smrforge-pro-1.0.0-docker.tar` (large)

Download from [Releases](https://github.com/SMRFORGE/smrforge-pro/releases) on a connected machine, then transfer to the air-gapped system.

---

## Licensing (Offline)

Pro uses RSA-signed license keys. Validation is local; no network required. Ensure the license key file is included in the transfer (e.g. `SMRFORGE_LICENSE` env or `~/.smrforge/license.json`).

---

## Nuclear Data (ENDF)

Same as Community: pre-stage ENDF-B-VIII.1 (or compatible) and set `SMRFORGE_ENDF_DIR`. See [Air-Gapped Deployment Guide](../guides/air-gapped-deployment.md#nuclear-data-endf).

---

## Checklist

| Step | Action |
|------|--------|
| 1 | Obtain Pro package (wheels or Docker) from Releases or bundle scripts |
| 2 | On connected machine: run `bundle_wheels.sh` or `bundle_docker.sh` |
| 3 | Transfer bundle + license key via approved process |
| 4 | On air-gapped: `pip install --no-index ...` or `docker load` |
| 5 | (Optional) Pre-stage ENDF; set `SMRFORGE_ENDF_DIR` |
| 6 | Verify: `python -c "import smrforge_pro; print('OK')"` |

---

## References

- [Air-Gapped Deployment (Community)](../guides/air-gapped-deployment.md)
- [Pro Overview](../pro-tier-overview.md)
