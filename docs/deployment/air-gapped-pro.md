# Air-Gapped Deployment — SMRForge Pro

**Audience:** Pro customers deploying in regulated, air-gapped environments.  
**Repo:** Pro code and bundles live in [smrforge-pro](https://github.com/SMRFORGE/smrforge-pro).

---

## Overview

Pro supports full air-gapped deployment: wheels, Docker images, and nuclear data can be pre-staged on a connected machine and transferred via approved process. Licensing validation runs offline (RSA-signed keys, no phone-home).

**Distribution:** Paid-tier Pro and air-gapped bundles use **GitHub Packages** for storage—wheel bundles on GitHub Releases, Docker images on `ghcr.io/smrforge/smrforge-pro`. Access requires a Pro license and authenticated GitHub access.

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

## Option 3: GitHub Packages (Releases + GHCR)

Pro and air-gapped bundles are stored in **GitHub Packages** for paid-tier customers:

| Asset | Location | Auth |
|-------|----------|------|
| Wheel bundle | [Releases](https://github.com/SMRFORGE/smrforge-pro/releases) — `airgap-bundle-*.zip` | GitHub PAT with `repo` (or org package read) |
| Docker image | `ghcr.io/smrforge/smrforge-pro` | `docker login ghcr.io` with PAT (`read:packages`) |

When Pro releases are tagged, an automated workflow attaches an air-gap bundle to the GitHub Release. Download on a connected machine, then transfer to the air-gapped system.

**Authenticating for paid-tier access:**

```bash
# Docker (pull from GitHub Container Registry)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Releases (browser or gh CLI)
gh release download <tag> --repo SMRFORGE/smrforge-pro
```

Use a GitHub Personal Access Token (PAT) with `read:packages` for Docker and `repo` for Releases. Your sales contact provides access and token scopes.

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
