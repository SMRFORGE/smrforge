# Community Tier — Nuclear Data Setup

How to obtain and configure ENDF nuclear data for Community edition.

---

## Overview

SMRForge Community can run **without ENDF files** using synthetic cross-sections for quick k-eff and preset analyses. For realistic cross-sections (ENDF-based), you need local ENDF files and one of these backends:

| Backend | Install | Notes |
|---------|---------|-------|
| endf-parserpy | `pip install endf-parserpy` | Recommended (IAEA) |
| SANDY | `pip install sandy` | Good for UQ |
| Built-in parser | — | Fallback (limited) |

---

## Workflow: Obtain ENDF Data

### Option 1: Data Downloader (Community)

```python
from smrforge.data_downloader import download_endf_data

stats = download_endf_data(
    library="ENDF/B-VIII.1",
    nuclide_set="common_smr",  # or isotopes=["U235", "U238", ...]
    output_dir="~/ENDF-Data",
    show_progress=True,
)
```

**Required:** `requests`, `tqdm` (included with smrforge).

**Output:** Files in `output_dir` organized by nuclide.

### Option 2: Manual Download

1. Go to [NNDC](https://www.nndc.bnl.gov/endf/) or [IAEA](https://www-nds.iaea.org/exfor/endf.htm).
2. Download desired library (e.g., ENDF/B-VIII.1).
3. Extract to a directory (e.g., `~/ENDF-Data/ENDF-B-VIII.1`).

---

## Configuration

### Environment Variable

```bash
export SMRFORGE_ENDF_DIR=~/ENDF-Data/ENDF-B-VIII.1
```

### In Code

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache

cache = NuclearDataCache(local_endf_dir=Path("~/ENDF-Data/ENDF-B-VIII.1").expanduser())
energy, xs = cache.get_cross_section(nuclide, "fission", temperature=293.6)
```

---

## Libraries Supported

- ENDF/B-VIII.0, ENDF/B-VIII.1  
- JEFF-3.3  
- JENDL-5.0  

---

## Workflow Without ENDF

If you have no ENDF data:

1. Use `quick_keff()`, `create_reactor()` with presets.
2. Use `CrossSectionData` with synthetic arrays for custom neutronics.
3. Burnup uses solver cross-sections (simplified) unless you pass a cache.
