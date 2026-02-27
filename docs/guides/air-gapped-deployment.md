# Air-Gapped Deployment Guide

**Last Updated:** February 2026  
**Purpose:** Enable SMRForge installation and use in environments without internet access.  
**Audience:** Site administrators, V&V teams, regulated (NQA-1) deployments.

---

## Overview

SMRForge supports deployment in air-gapped (offline) environments. Dependencies and nuclear data can be pre-staged on a machine with network access, then transferred to the target environment via removable media, internal network share, or approved transfer process.

---

## Strategy: Requirements and Dependencies

Use one of the following approaches so dependencies are available regardless of connectivity:

### Option 1: Wheel Bundle (Recommended)

Pre-download all wheels and the SMRForge package, then install offline.

**On connected machine:**

```bash
# From SMRForge repo root
cd /path/to/smrforge

# Create wheels directory
mkdir -p offline-wheels

# Download all dependencies
pip download -r requirements-lock.txt -d ./offline-wheels
pip download . -d ./offline-wheels  # SMRForge and any extras

# Copy entire repo (including offline-wheels/) to removable media
```

**On air-gapped machine:**

```bash
# After copying smrforge directory to target
cd /path/to/smrforge

pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt
pip install --no-index --find-links ./offline-wheels .
```

### Option 2: Requirements-Lock Only

Use version-locked requirements for reproducible installs.

```bash
# Connected: download all packages to a directory
pip download -r requirements-lock.txt -d ./offline-packages
pip download . -d ./offline-packages  # Include SMRForge
# Copy offline-packages/ and smrforge source to removable media

# Air-gapped: install
pip install --no-index --find-links ./offline-packages -r requirements-lock.txt
pip install --no-index --find-links ./offline-packages .
```

### Option 3: Full Environment Archive

Create a complete environment tarball for maximum portability.

```bash
# On connected machine
python -m venv smrforge-venv
source smrforge-venv/bin/activate  # Windows: smrforge-venv\Scripts\activate
pip install -r requirements-lock.txt
pip install -e .
# Optional: pip freeze > frozen.txt for audit

# Archive the entire venv (platform-specific; copy to target with same OS/arch)
tar -czf smrforge-venv.tar.gz smrforge-venv/
# Transfer smrforge-venv.tar.gz to air-gapped machine
```

**On air-gapped machine:** Extract and activate the venv. Ensure Python version matches.

### Option 4: Docker Image Transfer

For containerized deployments, build the image on a connected machine, save it, and load it on the air-gapped host.

```bash
# Connected: build with pinned dependencies (reproducible production)
docker build --build-arg USE_LOCKED=1 -t smrforge:1.0 .
docker save smrforge:1.0 -o smrforge-1.0.tar
# Transfer smrforge-1.0.tar

# Air-gapped: load and run
docker load -i smrforge-1.0.tar
docker run -it smrforge:1.0 smrforge --help
```

Use `--build-arg USE_LOCKED=1` to install from `requirements-lock.txt` (pinned versions) for reproducible builds.

Mount local ENDF directory when running:

```bash
docker run -v /path/to/ENDF-B-VIII.1:/data/endf -e SMRFORGE_ENDF_DIR=/data/endf smrforge:1.0
```

---

## SMRForge Pro (Licensed)

Pro and the air-gapped Pro version live in the Pro-tier repo [https://github.com/SMRFORGE/smrforge-pro](https://github.com/SMRFORGE/smrforge-pro). For air-gapped Pro deployment:

1. **Use bundle scripts** (in smrforge-pro repo): `./scripts/airgap/bundle_wheels.sh`, `./scripts/airgap/bundle_docker.sh`
2. **Or from Releases**: Download `airgap-bundle-*.zip` from [Pro Releases](https://github.com/SMRFORGE/smrforge-pro/releases)
3. Transfer to air-gapped system.
4. Install: `pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt` then `pip install --no-index --find-links ./offline-wheels .`

See the **air-gapped Pro** guide in smrforge-pro (`docs/deployment/air-gapped-pro.md`). To bootstrap air-gap files into a new Pro repo, run `./scripts/setup_pro_airgap.sh /path/to/smrforge-pro` from the Community repo.

---

## Nuclear Data (ENDF)

SMRForge does **not** require network access for nuclear data at runtime when using local files:

1. **Pre-stage ENDF-B-VIII.1** (or compatible) on the connected machine.
2. Copy the directory to the air-gapped system (e.g., `C:\ENDF\ENDF-B-VIII.1` or `/opt/endf/ENDF-B-VIII.1`).
3. Set `SMRFORGE_ENDF_DIR` to that path (environment variable or `NuclearDataCache(local_endf_dir=...)`).

**Directory structure:**

```
ENDF-B-VIII.1/
├── neutrons-version.VIII.1/   # n-092_U_235.endf, etc.
├── thermal_scatt-version.VIII.1/  # tsl-HinH2O.endf, etc.
├── nfy-version.VIII.1/        # Fission yields
├── decay-version.VIII.1/      # Decay data
└── ...
```

See [ENDF Test Setup](../development/ENDF-TEST-SETUP.md) for layout details.

---

## Verification

After offline installation, verify:

```bash
python -c "
import smrforge as smr
print('SMRForge version:', smr.__version__)
k = smr.quick_keff()
print('quick_keff():', round(k, 6))
"
```

With ENDF data:

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache

cache = NuclearDataCache(local_endf_dir=Path("/path/to/ENDF-B-VIII.1"))
materials = cache.list_available_tsl_materials()
print("TSL materials found:", len(materials))
```

---

## Checklist for Air-Gapped Deployment

| Step | Action |
|------|--------|
| 1 | Obtain `requirements-lock.txt` (or `requirements.txt`) and SMRForge source/wheel |
| 2 | On connected machine: `pip download` all dependencies to a local directory |
| 3 | Transfer dependency bundle + SMRForge to air-gapped system via approved process |
| 4 | On air-gapped machine: `pip install --no-index --find-links <dir> -r requirements-lock.txt` |
| 5 | Install SMRForge: `pip install --no-index --find-links <dir> .` |
| 6 | (Optional) Pre-stage ENDF data; set `SMRFORGE_ENDF_DIR` |
| 7 | Run verification script above |

---

## Code Style Compliance

All SMRForge code follows the [Code Style Guide](../development/code-style.md):

- **Formatting:** Black (88-char line length)
- **Imports:** isort
- **Type hints:** Required for new/modified code
- **Docstrings:** Google-style for public APIs

When extending or modifying SMRForge in air-gapped environments, ensure any changes comply with these guidelines before committing.

---

## References

- [VERSION_LOCK_REQUIREMENTS.md](../VERSION_LOCK_REQUIREMENTS.md) — Reproducibility and pinning
- [API_STABILITY.md](../API_STABILITY.md) — Public API tiers and air-gapped summary
- [Installation Guide](installation.md) — Standard (online) installation
