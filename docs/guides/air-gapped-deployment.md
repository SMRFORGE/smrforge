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

# Automated: run bundle script (creates offline-wheels/)
./scripts/bundle_offline_wheels.sh
# Windows: .\scripts\bundle_offline_wheels.ps1

# Or manually:
mkdir -p offline-wheels
pip download -r requirements-lock.txt -d ./offline-wheels
pip download . -d ./offline-wheels

# Copy offline-wheels/ to removable media
```

**On air-gapped machine:**

```bash
cd /path/to/transferred/smrforge
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

Pro and the air-gapped Pro version live in the Pro-tier repo [https://github.com/SMRFORGE/smrforge-pro](https://github.com/SMRFORGE/smrforge-pro).

**Feature parity:** Air-gapped Pro has the same features as Pro-tier when running in an air-gapped environment. No capabilities are disabled—Serpent/MCNP full export and import, CAD/DAGMC import, advanced variance reduction (CADIS), tally visualization, AI/surrogate, regulatory package, benchmark reproduction, code-to-code verification, and all other Pro features work offline. License validation is local (RSA-signed keys; no phone-home). Pre-stage nuclear data (ENDF) per options below.

For air-gapped Pro deployment:

1. **Use bundle scripts** (in smrforge-pro repo): `./scripts/airgap/bundle_wheels.sh`, `./scripts/airgap/bundle_docker.sh`
2. **Or from Releases**: Download `airgap-bundle-*.zip` from [Pro Releases](https://github.com/SMRFORGE/smrforge-pro/releases)
3. Transfer to air-gapped system.
4. Install: `pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt` then `pip install --no-index --find-links ./offline-wheels .`

See the **air-gapped Pro** guide in smrforge-pro (`docs/deployment/air-gapped-pro.md`). To bootstrap air-gap files into a new Pro repo, run `./scripts/setup_pro_airgap.sh /path/to/smrforge-pro` from the Community repo.

**Pro feature parity checklist:** With Pro air-gap install + pre-staged ENDF, all Pro features work offline: Serpent/MCNP full export/import, CAD/DAGMC import, advanced variance reduction (CADIS), tally viz, AI/surrogate, regulatory package, benchmark reproduction, code-to-code verification. License validation is local; no phone-home.

---

## Nuclear Data (ENDF)

SMRForge does **not** require network access for nuclear data at runtime when using local files.

**Option A: Bundle script (recommended)**

```bash
# On connected: download ENDF first, then bundle
smrforge data download  # or python -m smrforge.core.endf_setup
./scripts/bundle_nuclear_data.sh [ENDF_DIR] [output.tar.gz]
# Transfer nuclear-data-bundle.tar.gz

# On air-gapped:
tar -xzf nuclear-data-bundle.tar.gz -C /install/path
export SMRFORGE_ENDF_DIR=/install/path/ENDF-B-VIII.1
```

**Option B: Manual copy**

1. Pre-stage ENDF-B-VIII.1 on the connected machine (via `smrforge data download` or manual).
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

### Option C: Pre-Processed Zarr Library (Faster First-Run)

Pre-parse ENDF cross-sections into Zarr format to avoid runtime parsing.

**On connected machine:**

```bash
# Generate preprocessed Zarr bundle from ENDF
python scripts/generate_preprocessed_library.py \
  --endf-dir $SMRFORGE_ENDF_DIR \
  --output preprocessed-common.zarr \
  --zip

# Transfer preprocessed-common.zarr.zip to air-gapped system
```

**On air-gapped machine:**

```bash
# Extract the bundle
unzip preprocessed-common.zarr.zip -d /install/path/

# Use via NuclearDataCache or download_preprocessed_library
python -c "
from smrforge import download_preprocessed_library
stats = download_preprocessed_library(offline_path='/install/path/preprocessed-common.zarr')
print(stats)
"
```

**Hosting on GitHub Releases:** Publish `preprocessed-common.zarr.zip` as a Release asset. Users with network access can download via:

```python
download_preprocessed_library(
    releases_url="https://github.com/SMRFORGE/smrforge/releases/download/v0.1.0/preprocessed-common.zarr.zip",
    output_dir="/path/to/install"
)
```

---

## Validation and Benchmarks (Air-Gapped)

To run validation benchmarks offline:

1. **Pre-stage** on connected machine: ENDF data + `benchmarks/validation_benchmarks.json` (default; includes decay heat, cross-section, and k_eff benchmarks).
2. **Transfer** with wheel bundle and nuclear data.
3. **On air-gapped**: `smrforge validate run --endf-dir $SMRFORGE_ENDF_DIR --output output/validation/report.txt`
   - Uses `benchmarks/validation_benchmarks.json` by default when present.
   - Or: `python scripts/run_validation.py --endf-dir $SMRFORGE_ENDF_DIR --benchmarks benchmarks/validation_benchmarks.json`

See [Validation Accuracy Metrics](../validation/accuracy-metrics.md) and [Validation Execution Guide](../validation/validation-execution-guide.md).

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

**Community tier features** (parametric builders, 2D flux maps, basic variance reduction — work offline):

```python
# Parametric geometry builders
from smrforge.geometry import create_fuel_pin, create_moderator_block, create_simple_prismatic_core
pin = create_fuel_pin(radius=0.41, height=200.0)
block = create_moderator_block(flat_to_flat=36.0)
core = create_simple_prismatic_core(n_rings=2)
print("Parametric builders OK:", len(core.blocks), "blocks")

# 2D Plotly flux map (Community tally viz)
import numpy as np
from smrforge.visualization import plot_flux_map_2d
flux = np.random.rand(10, 15)
fig = plot_flux_map_2d(flux, backend="plotly")
print("plot_flux_map_2d OK:", fig is not None)

# Advanced variance reduction (Pro tier only—Community has basic ImportanceMap/WeightWindow)
# Pro: generate_cadis_weight_windows_from_diffusion, get_smr_preset_importance
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
| 7 | Run verification script above (includes parametric builders, plot_flux_map_2d) |

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
