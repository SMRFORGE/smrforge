#!/usr/bin/env bash
# Bootstrap air-gap scripts, docs, and workflow into smrforge-pro.
# Run from smrforge (Community) repo root.
#
# Usage: ./scripts/setup_pro_airgap.sh /path/to/smrforge-pro

set -e
COMMUNITY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRO_ROOT="${1:?Usage: $0 /path/to/smrforge-pro}"

if [ ! -d "$PRO_ROOT" ]; then
  echo "Error: Pro repo path does not exist: $PRO_ROOT"
  exit 1
fi

echo "==> Bootstrapping air-gap files into $PRO_ROOT"
mkdir -p "$PRO_ROOT/scripts/airgap"
mkdir -p "$PRO_ROOT/docs/deployment"
mkdir -p "$PRO_ROOT/.github/workflows"

# bundle_wheels.sh
cat > "$PRO_ROOT/scripts/airgap/bundle_wheels.sh" << 'BUNDLE_WHEELS'
#!/usr/bin/env bash
# Bundle all wheels for air-gapped installation.
# Run from smrforge-pro repo root.
#
# Usage: ./scripts/airgap/bundle_wheels.sh [OUTPUT_DIR]

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
OUTPUT_DIR="${1:-./offline-wheels}"
mkdir -p "$OUTPUT_DIR"

REQ_FILE="requirements-lock.txt"
[ -f "$REQ_FILE" ] || REQ_FILE="requirements.txt"

echo "==> Bundling wheels to $OUTPUT_DIR"
echo "==> Using $REQ_FILE"
pip download -r "$REQ_FILE" -d "$OUTPUT_DIR" --no-deps 2>/dev/null || true
pip download -r "$REQ_FILE" -d "$OUTPUT_DIR"
pip download . -d "$OUTPUT_DIR"
echo "==> Pro repo: including smrforge (Community) from PyPI"
pip download smrforge -d "$OUTPUT_DIR" || true

cat > "$OUTPUT_DIR/INSTALL.md" << 'INSTALLMD'
# Air-Gap Installation (Pro)

Same features as Pro-tier; no capabilities disabled offline.

Transfer this directory to the air-gapped machine, then:

  pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt
  pip install --no-index --find-links ./offline-wheels smrforge
  pip install --no-index --find-links ./offline-wheels .

Pre-stage ENDF data; set SMRFORGE_ENDF_DIR. See docs/deployment/air-gapped-pro.md.
INSTALLMD

echo "==> Done. Transfer $OUTPUT_DIR to air-gapped machine, then:"
echo "    pip install --no-index --find-links $OUTPUT_DIR -r $REQ_FILE"
echo "    pip install --no-index --find-links $OUTPUT_DIR smrforge"
echo "    pip install --no-index --find-links $OUTPUT_DIR ."
BUNDLE_WHEELS

# bundle_docker.sh
cat > "$PRO_ROOT/scripts/airgap/bundle_docker.sh" << 'BUNDLE_DOCKER'
#!/usr/bin/env bash
# Build and save Docker image for air-gapped deployment.
# Run from smrforge-pro repo root.
#
# Usage: ./scripts/airgap/bundle_docker.sh [OUTPUT_FILE]

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

DF="Dockerfile.pro"
[ -f "$DF" ] || DF="Dockerfile"
if [ -d "smrforge_pro" ] && [ -f "Dockerfile.pro" ]; then
  if ! grep -q "exit 1" Dockerfile.pro 2>/dev/null; then
    DF="Dockerfile.pro"
  fi
fi

IMAGE_NAME="smrforge-pro:latest"
OUTPUT_FILE="${1:-./smrforge-pro-docker.tar}"
echo "==> Building with $DF"
docker build --build-arg USE_LOCKED=1 -f "$DF" -t "$IMAGE_NAME" .
echo "==> Saving to $OUTPUT_FILE"
docker save "$IMAGE_NAME" -o "$OUTPUT_FILE"
echo "==> Done. Transfer $OUTPUT_FILE to air-gapped machine, then:"
echo "    docker load -i $OUTPUT_FILE"
BUNDLE_DOCKER

# bundle_wheels.ps1
cat > "$PRO_ROOT/scripts/airgap/bundle_wheels.ps1" << 'BUNDLE_PS1'
# Bundle all wheels for air-gapped installation.
 param([string]$OutputDir = ".\offline-wheels")
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

$ReqFile = "requirements-lock.txt"
if (-not (Test-Path $ReqFile)) { $ReqFile = "requirements.txt" }
Write-Host "==> Bundling wheels to $OutputDir"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
pip download -r $ReqFile -d $OutputDir
pip download . -d $OutputDir
Write-Host "==> Pro repo: including smrforge (Community) from PyPI"
pip download smrforge -d $OutputDir 2>$null
Write-Host "==> Done. Transfer $OutputDir to air-gapped machine."
BUNDLE_PS1

# README.md
cat > "$PRO_ROOT/scripts/airgap/README.md" << 'README'
# Air-Gap Bundle Scripts

Pre-stage wheels and Docker images for air-gapped SMRForge Pro deployment.

## Usage

From smrforge-pro repo root:

```bash
./scripts/airgap/bundle_wheels.sh [OUTPUT_DIR]
./scripts/airgap/bundle_docker.sh [OUTPUT_FILE]
```

See [Air-Gapped Pro](../../docs/deployment/air-gapped-pro.md) for full details.
README

# air-gapped-pro.md
cat > "$PRO_ROOT/docs/deployment/air-gapped-pro.md" << 'AIRGAP_PRO'
# Air-Gapped Deployment — SMRForge Pro

**Audience:** Pro customers deploying in regulated, air-gapped environments.
**Repo:** [https://github.com/SMRFORGE/smrforge-pro](https://github.com/SMRFORGE/smrforge-pro)

---

## Feature Parity

**Air-gapped Pro has the same features as Pro-tier** when running in an air-gapped environment. No capabilities are disabled. All Pro features work offline:

- Serpent/MCNP full export and import
- CAD/DAGMC import
- Advanced variance reduction (CADIS from diffusion adjoint)
- Tally visualization, AI/surrogate, regulatory package
- Benchmark reproduction, code-to-code verification
- Natural-language design, multi-objective optimization

Licensing validation runs offline (RSA-signed keys; no phone-home). Pre-stage nuclear data (ENDF) and optional preprocessed libraries per the Nuclear Data section in the Community [Air-Gapped Deployment Guide](https://smrforge.readthedocs.io/en/latest/guides/air-gapped-deployment.html).

---

## Overview

Pro supports full air-gapped deployment.

**Distribution:** Wheel bundles on GitHub Releases, Docker images on `ghcr.io/smrforge/smrforge-pro`. Access requires Pro license and authenticated GitHub access.

---

## Option 1: Wheel Bundle

**On connected machine:**

```bash
cd /path/to/smrforge-pro
./scripts/airgap/bundle_wheels.sh ./offline-wheels
```

**Transfer** `offline-wheels/` to air-gapped system. **On air-gapped machine:**

```bash
pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt
pip install --no-index --find-links ./offline-wheels smrforge
pip install --no-index --find-links ./offline-wheels .
```

---

## Option 2: Docker Image

**On connected machine:** `./scripts/airgap/bundle_docker.sh ./smrforge-pro-1.0.tar`  
**On air-gapped:** `docker load -i smrforge-pro-1.0.tar`

---

## Option 3: GitHub Packages (Releases)

Download `airgap-bundle-*.zip` from [Releases](https://github.com/SMRFORGE/smrforge-pro/releases). Authenticate with GitHub PAT (`read:packages` for Docker, `repo` for Releases).

---

## Licensing / ENDF

Pro uses RSA-signed keys; validation is local. Pre-stage ENDF-B-VIII.1 and set `SMRFORGE_ENDF_DIR`.
AIRGAP_PRO

# release-airgap.yml
cat > "$PRO_ROOT/.github/workflows/release-airgap.yml" << 'WORKFLOW'
name: Release Air-Gap Bundle

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  build-bundle:
    name: Build air-gap bundle
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install --upgrade pip wheel build
      - run: mkdir -p offline-wheels
      - name: Download dependencies
        run: |
          REQ="requirements-lock.txt"
          [ -f "$REQ" ] || REQ="requirements.txt"
          pip download -r "$REQ" -d offline-wheels
          pip download . -d offline-wheels
          pip download smrforge -d offline-wheels || true
      - name: Create INSTALL.md
        run: |
          cat > offline-wheels/INSTALL.md << 'EOF'
          # Air-Gap Installation (Pro)

          Same features as Pro-tier; no capabilities disabled offline.

          Transfer this directory to the air-gapped machine, then:

            pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt
            pip install --no-index --find-links ./offline-wheels smrforge
            pip install --no-index --find-links ./offline-wheels .

          Pre-stage ENDF data; set SMRFORGE_ENDF_DIR. See docs/deployment/air-gapped-pro.md.
          EOF
      - name: Create bundle zip
        run: |
          VERSION="${GITHUB_REF#refs/tags/}" || VERSION="snapshot"
          zip -r airgap-bundle-$VERSION.zip offline-wheels/
          echo "BUNDLE_ZIP=airgap-bundle-$VERSION.zip" >> $GITHUB_ENV
      - uses: actions/upload-artifact@v4
        with:
          name: airgap-bundle
          path: airgap-bundle-*.zip

  attach-release:
    name: Attach to release
    runs-on: ubuntu-latest
    needs: build-bundle
    if: github.event_name == 'release'
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: airgap-bundle
      - run: |
          TAG="${{ github.event.release.tag_name }}"
          gh release upload "$TAG" airgap-bundle-*.zip --clobber
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
WORKFLOW

chmod +x "$PRO_ROOT/scripts/airgap/bundle_wheels.sh" "$PRO_ROOT/scripts/airgap/bundle_docker.sh"
echo "==> Done. Air-gap files are now in $PRO_ROOT"
