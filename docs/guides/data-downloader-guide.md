# SMRForge Data Downloader Guide

**Last Updated:** January 2026

Complete guide for using the automated ENDF data downloader in SMRForge.

---

## Overview

SMRForge provides an automated data downloader that allows you to programmatically download ENDF nuclear data files from NNDC and IAEA, eliminating the need for manual downloads.

### Key Features

- ✅ **Automated downloads** - Download ENDF files programmatically
- ✅ **Selective downloads** - Download by element, isotope, or pre-defined sets
- ✅ **Progress indicators** - Visual progress bars during downloads
- ✅ **Resume capability** - Resume interrupted downloads
- ✅ **Automatic validation** - Validates downloaded files
- ✅ **Automatic organization** - Organizes files into standard structure

---

## Installation

The data downloader requires `requests` and optionally `tqdm` for progress bars:

```bash
pip install requests tqdm
```

These are included in SMRForge's requirements, so they should already be installed.

---

## Quick Start

### Download Specific Isotopes

```python
from smrforge.data_downloader import download_endf_data

# Download specific isotopes
stats = download_endf_data(
    library="ENDF/B-VIII.1",
    isotopes=["U235", "U238", "Pu239"],
    output_dir="~/ENDF-Data",
    show_progress=True,
)

print(f"Downloaded: {stats['downloaded']}")
print(f"Skipped: {stats['skipped']}")
print(f"Failed: {stats['failed']}")
```

### Download by Element

```python
# Download all common isotopes of specific elements
stats = download_endf_data(
    library="ENDF/B-VIII.1",
    elements=["U", "Pu", "Th"],
    output_dir="~/ENDF-Data",
    show_progress=True,
)
```

### Download Common SMR Nuclides

```python
# Download pre-selected common SMR nuclides
stats = download_endf_data(
    library="ENDF/B-VIII.1",
    nuclide_set="common_smr",
    output_dir="~/ENDF-Data",
    show_progress=True,
)
```

---

## API Reference

### `download_endf_data()`

Download ENDF nuclear data files from NNDC/IAEA.

**Parameters:**

- `library` (str or Library): Library version (e.g., "ENDF/B-VIII.1", "ENDF/B-VIII.0", "JEFF-3.3", "JENDL-5.0")
- `output_dir` (str or Path, optional): Output directory. Defaults to standard ENDF directory (`~/ENDF-Data`)
- `elements` (List[str], optional): List of element symbols (e.g., ["U", "Pu"])
- `isotopes` (List[str], optional): List of isotope strings (e.g., ["U235", "Pu239"])
- `nuclides` (List[Nuclide], optional): List of Nuclide instances
- `nuclide_set` (str, optional): Pre-defined set name (currently only "common_smr")
- `resume` (bool, default=True): Resume interrupted downloads
- `show_progress` (bool, default=True): Show progress indicators
- `validate` (bool, default=True): Validate downloaded files
- `organize` (bool, default=True): Organize files into standard structure
- `max_workers` (int, default=5): Maximum concurrent downloads (parallel downloads enabled)

**Returns:**

Dictionary with download statistics:
- `downloaded`: Number of files downloaded
- `skipped`: Number of files skipped (already exist)
- `failed`: Number of failed downloads
- `total`: Total number of files attempted
- `output_dir`: Path to output directory
- `organized`: Number of files organized (if organize=True)

**Example:**

```python
from smrforge.data_downloader import download_endf_data

stats = download_endf_data(
    library="ENDF/B-VIII.1",
    isotopes=["U235", "U238"],
    output_dir="~/ENDF-Data",
    show_progress=True,
    validate=True,
    organize=True,
)

print(f"Download complete: {stats['downloaded']} files")
```

---

## Using Downloaded Data

After downloading, use the data with `NuclearDataCache`:

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Nuclide

# Point to downloaded directory
cache = NuclearDataCache(local_endf_dir=Path.home() / "ENDF-Data")

# Use the data
u235 = Nuclide(Z=92, A=235)
energy, xs = cache.get_cross_section(u235, "total", temperature=293.6)
```

### Environment Variable

You can also set the `SMRFORGE_ENDF_DIR` environment variable:

```bash
export SMRFORGE_ENDF_DIR=~/ENDF-Data
```

Then in Python:

```python
from smrforge.core.reactor_core import NuclearDataCache

# Automatically uses SMRFORGE_ENDF_DIR
cache = NuclearDataCache()
```

### Configuration File

Create `~/.smrforge/config.yaml`:

```yaml
endf:
  default_directory: "~/ENDF-Data"
  default_library: "ENDF/B-VIII.1"
  auto_download: true
```

Then `NuclearDataCache` will automatically use the configured directory.

---

## Common SMR Nuclides

The `common_smr` nuclide set includes:

- **Moderator/Water**: H1, H2, O16, O17, O18
- **Graphite**: C12, C13
- **Uranium**: U235, U238, U236, U237
- **Plutonium**: Pu239, Pu240, Pu241, Pu242, Pu238
- **Thorium**: Th232, Th233
- **Minor Actinides**: Np237, Am241, Am243
- **Structural**: Zr90-96, Fe54-58, Cr50-54, Ni58-64

Access the list:

```python
from smrforge.data_downloader import COMMON_SMR_NUCLIDES
print(COMMON_SMR_NUCLIDES)
```

---

## Advanced Usage

### Resume Interrupted Downloads

```python
# Resume downloads that were interrupted
stats = download_endf_data(
    library="ENDF/B-VIII.1",
    isotopes=["U235", "U238", "Pu239"],
    output_dir="~/ENDF-Data",
    resume=True,  # Skip already-downloaded files
    show_progress=True,
)
```

### Custom Nuclide List

```python
from smrforge.core.reactor_core import Nuclide

# Download specific nuclides
nuclides = [
    Nuclide(Z=92, A=235),
    Nuclide(Z=92, A=238),
    Nuclide(Z=94, A=239),
]

stats = download_endf_data(
    library="ENDF/B-VIII.1",
    nuclides=nuclides,
    output_dir="~/ENDF-Data",
)
```

### Disable Validation

```python
# Download without validation (faster, but less safe)
stats = download_endf_data(
    library="ENDF/B-VIII.1",
    isotopes=["U235"],
    validate=False,  # Skip validation
)
```

---

## Troubleshooting

### Import Error: requests not found

Install requests:

```bash
pip install requests
```

### Import Error: tqdm not found

Install tqdm (optional, for progress bars):

```bash
pip install tqdm
```

### Download Fails

- Check internet connection
- Verify URL is accessible (may be temporary server issue)
- Try again later (servers may be temporarily unavailable)
- Check firewall/proxy settings

### Files Not Found After Download

- Check `output_dir` path
- Verify files were actually downloaded (check `stats['downloaded']`)
- Check file permissions
- Run with `organize=True` to organize files into standard structure

---

## Integration with Setup Wizard

The data downloader integrates with the existing setup wizard:

```python
from smrforge.core.endf_setup import setup_endf_data_interactive

# Run setup wizard
setup_endf_data_interactive()

# Or download programmatically
from smrforge.data_downloader import download_endf_data
download_endf_data(library="ENDF/B-VIII.1", nuclide_set="common_smr")
```

---

## Performance Optimizations

### Parallel Downloads ✅

The downloader automatically uses parallel downloads when `max_workers > 1`:

```python
# Download with 10 parallel workers (faster for many files)
stats = download_endf_data(
    library="ENDF/B-VIII.1",
    isotopes=["U235", "U238", "Pu239", ...],  # Many files
    max_workers=10,  # Parallel downloads
    show_progress=True,
)
```

**Expected Speedup:** 3-10x faster (depending on network and number of files)

### Connection Pooling ✅

The downloader uses connection pooling to reuse HTTP connections, reducing overhead.

### URL Source Caching ✅

The downloader remembers which source (IAEA or NNDC) works best for each library, trying the preferred source first on subsequent downloads.

### Unified Progress Bar ✅

A single progress bar shows overall progress across all files, with current file name and statistics.

---

## Future Features (Phase 2)

- **Pre-processed libraries**: Download optimized Zarr libraries
- **Full library downloads**: Download entire library automatically
- **Library hosting**: Pre-processed libraries on GitHub Releases/Zenodo

---

## See Also

- [ENDF Documentation](technical/endf-documentation.md) - Complete ENDF setup guide
- [Data Import Comparison](status/data-import-comparison-and-improvement-plan.md) - Comparison with OpenMC
- [Examples](../examples/data_downloader_example.py) - Code examples
