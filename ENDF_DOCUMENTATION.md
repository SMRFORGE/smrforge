# ENDF Nuclear Data Documentation

Complete guide for using ENDF (Evaluated Nuclear Data File) nuclear data files with SMRForge.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Setup Guide](#setup-guide)
4. [Integration Details](#integration-details)
5. [Bulk Storage and Organization](#bulk-storage-and-organization)
6. [Codebase Improvements](#codebase-improvements)
7. [Parser Information](#parser-information)
8. [Docker Integration](#docker-integration)
9. [Troubleshooting](#troubleshooting)
10. [Additional Resources](#additional-resources)

---

## Overview

SMRForge requires ENDF nuclear data files for cross-section calculations. **ENDF files must be downloaded and set up manually** - SMRForge does not automatically download them.

### What is ENDF?

ENDF (Evaluated Nuclear Data File) is the standard format for nuclear cross-section data used in reactor physics calculations. SMRForge supports:

- **ENDF/B-VIII.1** (recommended, latest as of 2024)
- **ENDF/B-VIII.0** (also supported)

### Key Features

- ✅ **Local file support** - Use locally stored ENDF files for fast, offline access
- ✅ **Automatic file discovery** - Finds files regardless of directory structure
- ✅ **Bulk download organization** - Organize bulk-downloaded files automatically
- ✅ **Interactive setup wizard** - Step-by-step guidance for setup
- ✅ **Version fallback** - Automatically tries VIII.1 → VIII.0 if needed
- ✅ **Flexible structure** - Supports standard, flat, or nested directory layouts

### Minimum Requirements

- **Neutron data** (required): Contains cross-section data for neutron interactions
- **Directory structure**: `neutrons-version.VIII.1/` with `.endf` files (typically 500+ files)

---

## Quick Start

### Option 1: Interactive Setup Wizard (Recommended)

Run the setup wizard for step-by-step guidance:

```bash
python -m smrforge.core.endf_setup
```

Or use the command-line tool (if installed):

```bash
smrforge-setup-endf
```

The wizard will:
1. Guide you through locating existing ENDF files OR
2. Provide instructions for downloading ENDF files
3. Scan and validate all files
4. Organize files into standard structure (optional)
5. Test the setup

### Option 2: Manual Setup

**For local Python scripts:**
```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache

# Point to your extracted ENDF directory
cache = NuclearDataCache(local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1"))
```

**For Docker:**
1. Download and extract ENDF files to a directory (e.g., `C:/Users/YourName/ENDF-Data`)
2. Edit `docker-compose.yml` and add volume mount:
   ```yaml
   volumes:
     - C:/Users/YourName/ENDF-Data:/app/endf-data:ro
   ```
3. Restart container: `docker compose down && docker compose up -d smrforge`

---

## Setup Guide

### Step 1: Download ENDF Files

#### Option A: NNDC (National Nuclear Data Center) - Recommended

1. **Visit the NNDC ENDF website:**
   - URL: https://www.nndc.bnl.gov/endf/
   - This is the official source for ENDF/B data

2. **Navigate to the library version:**
   - **ENDF/B-VIII.1** (recommended, latest as of 2024)
   - **ENDF/B-VIII.0** (also supported)
   - Look for "Download" or "Bulk Download" links

3. **Download the complete library:**
   - Download the entire `ENDF-B-VIII.1` archive
   - File size: ~500 MB - 2 GB (compressed)
   - Format: Usually `.zip` or `.tar.gz`

#### Option B: IAEA Nuclear Data Services

1. **Visit IAEA NDS:**
   - URL: https://www-nds.iaea.org/
   - Alternative source for ENDF data

2. **Download ENDF/B-VIII.1:**
   - Navigate to ENDF/B-VIII.1 section
   - Download the complete library archive

### Step 2: Extract Files

#### Windows

1. **Right-click the downloaded archive** → "Extract All..."
2. **Choose extraction location:**
   - Recommended: `C:\Users\YourName\ENDF-Data`
   - Or: `C:\Users\YourName\Downloads\ENDF-B-VIII.1`
3. **Extract** and wait for completion

#### Linux/Mac

```bash
# For .zip files
unzip ENDF-B-VIII.1.zip -d ~/ENDF-Data

# For .tar.gz files
tar -xzf ENDF-B-VIII.1.tar.gz -C ~/ENDF-Data
```

#### Verify Extraction

After extraction, you should see a directory structure like:

```
ENDF-B-VIII.1/
├── neutrons-version.VIII.1/
│   ├── n-001_H_001.endf
│   ├── n-092_U_235.endf
│   ├── n-092_U_238.endf
│   └── ... (hundreds of files)
├── protons-version.VIII.1/
├── decay-version.VIII.1/
└── ... (other sub-libraries)
```

**Important:** The `neutrons-version.VIII.1/` directory should contain many `.endf` files (typically 500+ files).

### Step 3: Local Setup (Python Scripts)

#### Method 1: Direct Path (Simple)

Point directly to your extracted ENDF directory:

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

# Windows example
cache = NuclearDataCache(
    local_endf_dir=Path("C:/Users/YourName/Downloads/ENDF-B-VIII.1")
)

# Linux/Mac example
cache = NuclearDataCache(
    local_endf_dir=Path("~/ENDF-Data/ENDF-B-VIII.1")
)
```

#### Method 2: Standard Directory (Recommended)

Use the recommended standard location:

```python
from pathlib import Path
from smrforge.core.reactor_core import (
    NuclearDataCache,
    get_standard_endf_directory,
    organize_bulk_endf_downloads
)

# Get standard directory path
standard_dir = get_standard_endf_directory()
# Windows: C:\Users\YourName\ENDF-Data
# Linux/Mac: ~/ENDF-Data

# If you extracted to a different location, organize into standard directory
organize_bulk_endf_downloads(
    source_dir=Path("C:/Users/YourName/Downloads/ENDF-B-VIII.1"),
    target_dir=standard_dir,
    library_version="VIII.1"
)

# Now use the standard directory
cache = NuclearDataCache(local_endf_dir=standard_dir)
```

#### Method 3: Environment Variable

Set an environment variable and use it:

**Windows (PowerShell):**
```powershell
$env:SMRFORGE_ENDF_DIR = "C:\Users\YourName\ENDF-Data"
```

**Windows (Command Prompt):**
```cmd
set SMRFORGE_ENDF_DIR=C:\Users\YourName\ENDF-Data
```

**Linux/Mac:**
```bash
export SMRFORGE_ENDF_DIR=~/ENDF-Data
```

**In Python:**
```python
import os
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache

endf_dir = Path(os.getenv("SMRFORGE_ENDF_DIR", "~/ENDF-Data"))
cache = NuclearDataCache(local_endf_dir=endf_dir)
```

### Step 4: Verify Setup

Create a test script `test_endf_setup.py`:

```python
"""Test ENDF setup."""
from pathlib import Path
from smrforge.core.reactor_core import (
    NuclearDataCache,
    Nuclide,
    Library,
    scan_endf_directory
)

# Set your ENDF directory path here
ENDF_DIR = Path("C:/Users/YourName/ENDF-Data/ENDF-B-VIII.1")
# Or for Docker: ENDF_DIR = Path("/app/endf-data")

print(f"Testing ENDF directory: {ENDF_DIR}")
print(f"Directory exists: {ENDF_DIR.exists()}")

if not ENDF_DIR.exists():
    print("ERROR: Directory does not exist!")
    exit(1)

# Scan directory
print("\nScanning directory...")
results = scan_endf_directory(ENDF_DIR)
print(f"Total files found: {results['total_files']}")
print(f"Valid ENDF files: {results['valid_files']}")
print(f"Directory structure: {results['directory_structure']}")

if results['valid_files'] == 0:
    print("ERROR: No valid ENDF files found!")
    exit(1)

# Test cache
print("\nTesting NuclearDataCache...")
cache = NuclearDataCache(local_endf_dir=ENDF_DIR)

# Test common nuclides
test_nuclides = [
    (Nuclide(92, 235), "U-235"),
    (Nuclide(92, 238), "U-238"),
    (Nuclide(8, 16), "O-16"),
]

for nuclide, name in test_nuclides:
    try:
        # Try to find file
        file_path = cache._find_local_endf_file(nuclide, Library.ENDF_B_VIII_1)
        if file_path:
            print(f"✓ {name}: Found at {file_path.name}")
        else:
            print(f"✗ {name}: Not found")
    except Exception as e:
        print(f"✗ {name}: Error - {e}")

print("\n✓ Setup verification complete!")
```

**Run locally:**
```bash
python test_endf_setup.py
```

**Run in Docker:**
```bash
docker compose exec smrforge python /app/test_endf_setup.py
```

---

## Integration Details

### File Naming Convention

ENDF files use a standard naming format:
- Format: `n-ZZZ_Element_AAA.endf` (for neutrons)
  - Example: `n-092_U_235.endf` → U-235
  - Example: `n-001_H_001.endf` → H-1
  - Example: `n-013_Al_026m1.endf` → Al-26m1 (metastable)

### Library Support

SMRForge supports multiple ENDF library versions:

```python
from smrforge.core.reactor_core import Library

# Supported libraries
Library.ENDF_B_VIII_0  # "endfb8.0"
Library.ENDF_B_VIII_1  # "endfb8.1" (recommended)
```

### Automatic File Discovery

SMRForge automatically discovers ENDF files regardless of directory structure:

- **Standard structure** (recommended): Files in `neutrons-version.VIII.1/`
- **Flat structure**: All `.endf` files in root directory
- **Nested structure**: Files in any subdirectory

The system supports:
- Standard ENDF naming: `n-092_U_235.endf`
- Alternative naming: `U235.endf`, `u235.endf`, `92235.endf`
- Multiple library versions in the same directory

### Version Fallback

If a file is not found for the requested library version, SMRForge automatically tries:
- VIII.1 → VIII.0 (if VIII.1 not found)

### Usage Example

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, CrossSectionTable
from smrforge.core.reactor_core import Library
import numpy as np

# Initialize cache with local ENDF directory
cache = NuclearDataCache(
    local_endf_dir=Path("C:/Users/YourName/ENDF-Data/ENDF-B-VIII.1")
)

# Create cross-section table (pass the cache!)
xs_table = CrossSectionTable(cache=cache)

# Generate multi-group cross sections
nuclides = [
    Nuclide(92, 235),  # U-235
    Nuclide(92, 238),  # U-238
    Nuclide(8, 16),    # O-16
]

group_structure = np.logspace(7, -1, 70)  # 70-group structure

xs_df = xs_table.generate_multigroup(
    nuclides=nuclides,
    reactions=['total', 'fission', 'capture', 'elastic', 'n,2n', 'n,alpha'],
    group_structure=group_structure,
    temperature=900.0  # Kelvin
)

print(f"Generated {len(xs_df)} cross-section entries")
```

---

## Bulk Storage and Organization

### Standard Directory Structure

SMRForge provides a standard directory location for storing bulk ENDF files:

```python
from smrforge.core.reactor_core import get_standard_endf_directory

# Get standard directory path
endf_dir = get_standard_endf_directory()
# Windows: C:\Users\YourName\ENDF-Data
# Unix/Mac: ~/ENDF-Data

print(f"Store ENDF files in: {endf_dir}")
```

### Recommended Structure

```
ENDF-Data/
├── neutrons-version.VIII.1/
│   ├── n-001_H_001.endf
│   ├── n-092_U_235.endf
│   └── ...
├── neutrons-version.VIII.0/
│   ├── n-001_H_001.endf
│   └── ...
└── protons-version.VIII.1/
    └── ...
```

### Organizing Bulk Downloads

After downloading ENDF files in bulk, organize them:

```python
from pathlib import Path
from smrforge.core.reactor_core import organize_bulk_endf_downloads

# Organize files from bulk download
stats = organize_bulk_endf_downloads(
    source_dir=Path("C:/Users/user/Downloads/ENDF-B-VIII.1"),
    target_dir=Path("C:/Users/user/ENDF-Data"),
    library_version="VIII.1"
)

print(f"Organized {stats['files_organized']} files")
print(f"Valid files: {stats['valid_files']}")
print(f"Invalid files: {stats['invalid_files']}")
```

### Scanning Directories

Check what files are available:

```python
from smrforge.core.reactor_core import scan_endf_directory

results = scan_endf_directory(Path("C:/path/to/ENDF-B-VIII.1"))
print(f"Found {results['valid_files']} valid ENDF files")
print(f"Directory structure: {results['directory_structure']}")
print(f"Library versions: {results['library_versions']}")
```

---

## Codebase Improvements

### Implemented Improvements

All Phase 1 and Phase 2 improvements have been successfully implemented:

#### ✅ 1. Energy-Dependent nu (Neutrons per Fission)

**Implementation:**
- Created `smrforge/core/endf_extractors.py` with `extract_nu_from_endf()` function
- Uses energy-dependent nu values instead of hardcoded constants
- Supports U235, U238, Pu239, Pu241 with nuclide-specific parameters
- Interpolates between thermal and fast values based on neutron energy

**Key Features:**
- Energy-dependent: nu increases with neutron energy (2.43 → 2.58 for U235)
- Nuclide-specific: Different values for U235, U238, Pu239, Pu241
- Logarithmic interpolation for smooth energy dependence

**Usage:**
```python
from smrforge.core.endf_extractors import extract_nu_from_endf

nu_values = extract_nu_from_endf(cache, nuclide, group_structure, temperature)
# Returns: np.ndarray of nu values for each energy group
```

#### ✅ 2. Proper Watt Spectrum chi (Fission Spectrum)

**Implementation:**
- Created `extract_chi_from_endf()` function in `endf_extractors.py`
- Uses proper Watt spectrum with nuclide-specific parameters
- Falls back to hardcoded spectrum if Watt computation fails

**Key Features:**
- Watt spectrum: `chi(E) = C * exp(-E/a) * sinh(sqrt(b*E))`
- Nuclide-specific parameters from `FISSION_SPECTRUM_PARAMS`
- Proper normalization (sum = 1.0)
- Supports U235, U238, Pu239 with appropriate parameters

**Usage:**
```python
from smrforge.core.endf_extractors import extract_chi_from_endf

chi = extract_chi_from_endf(cache, nuclide, group_structure)
# Returns: np.ndarray of chi values (normalized to sum=1)
```

#### ✅ 3. Improved Scattering Matrix Computation

**Implementation:**
- Created `compute_improved_scattering_matrix()` function
- Energy-dependent downscattering model:
  - Fast groups (>100 keV): 70% same, 25% next, 5% skip
  - Thermal groups: 90% same, 10% next

**Key Features:**
- Energy-aware: Different behavior for fast vs thermal groups
- Uses actual elastic cross-section data
- Can accept pre-computed multi-group elastic XS

**Usage:**
```python
from smrforge.core.endf_extractors import compute_improved_scattering_matrix

sigma_s = compute_improved_scattering_matrix(
    cache, nuclide, group_structure, temperature, elastic_mg
)
```

#### ✅ 4. Additional Reactions

**Reactions Now Supported:**
- `total` (MT=1)
- `fission` (MT=18)
- `capture` (MT=102)
- `elastic` (MT=2)
- `n,2n` (MT=16) - **NEW**
- `n,alpha` (MT=107) - **NEW**

#### ✅ 5. Comprehensive Validation

Added validation checks:
- No negative cross-sections
- `sigma_a <= sigma_t` (physical constraint)
- `sigma_f <= sigma_a` (physical constraint)
- `chi` sums to 1.0 for fissioning materials
- Diffusion coefficients are reasonable

#### ✅ 6. Optimized DataFrame Operations

- Replaced multiple filter operations with single-pass dictionary extraction
- Pre-extracts all reactions into dictionaries for O(1) lookup
- **Performance Improvement:** ~5-10x faster for large datasets

### Future Enhancements (Not Yet Implemented)

#### Phase 3: Advanced Features
1. **Parse MF=5 from ENDF** for actual chi data
2. **Parse MF=1, MT=452** for actual nu data
3. **Parse MF=6** for detailed scattering matrices
4. **Add caching** for converted cross-sections
5. **Flux-weighting** for group collapse

---

## Parser Information

### Supported Backends

SMRForge supports multiple backends for parsing ENDF nuclear cross-section data. The system will try them in order until one succeeds.

#### 1. SANDY (Recommended)
- **Pros**: Pure Python, easy to install, no compilation needed, well-maintained
- **Cons**: Potentially slower than compiled alternatives for very large files
- **Installation**: `pip install sandy`
- **Status**: Recommended for most users

#### 2. Custom ENDF Parser (Fallback)
- **Pros**: No external dependencies, built into SMRForge
- **Cons**: Limited to basic reactions (total, elastic, fission, capture), less robust
- **Installation**: None required (built-in)
- **Status**: Fallback for basic use cases

### Custom Parser Features

The `smrforge.core.endf_parser` module implements a custom ENDF parser that:
- ✅ **Pure Python** - No compilation needed, no external dependencies (beyond NumPy)
- ✅ **Clean API** - Simple, intuitive interface for ENDF file parsing
- ✅ **Focused functionality** - Only implements what SMRForge needs
- ✅ **Robust parsing** - Handles standard ENDF-6 format files
- ✅ **Lightweight** - Fast to install and use

### Supported Reactions

- Total (MT=1)
- Elastic scattering (MT=2)
- Non-elastic (MT=3)
- Inelastic (MT=4)
- Fission (MT=18, 19, 20, 21)
- Capture (MT=102)
- And other common reactions

### Usage

```python
from smrforge.core.endf_parser import ENDFCompatibility
from pathlib import Path

# Parse an ENDF file
evaluation = ENDFCompatibility(Path("U235.endf"))

# Check if a reaction exists
if 1 in evaluation:  # MT=1 is total cross section
    rxn_data = evaluation[1]
    
    # Access energy and cross section
    energy = rxn_data.xs['0K'].x  # Energy in eV
    xs = rxn_data.xs['0K'].y      # Cross section in barns
    
    print(f"Energy range: {energy.min():.2e} - {energy.max():.2e} eV")
    print(f"Cross-section range: {xs.min():.2e} - {xs.max():.2e} barns")
```

---

## Docker Integration

### Quick Start

If you're getting download errors when running SMRForge in Docker, you need to mount your local ENDF data directory.

1. **Edit `docker-compose.yml`** and add the ENDF volume mount:

```yaml
services:
  smrforge:
    volumes:
      - ./data:/app/data:rw
      - ./output:/app/output:rw
      - ./examples:/app/examples:ro
      # Add your ENDF directory mount here:
      - C:/Users/YourName/ENDF-Data/ENDF-B-VIII.1:/app/endf-data:ro
```

2. **Update your code** to use the mounted directory:

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache

# Use mounted ENDF directory
cache = NuclearDataCache(local_endf_dir=Path("/app/endf-data"))
```

3. **Restart the container**:

```bash
docker compose down
docker compose up -d smrforge
```

### Complete Docker Example

**docker-compose.yml:**
```yaml
services:
  smrforge:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./data:/app/data:rw
      - ./output:/app/output:rw
      - ./examples:/app/examples:ro
      # Mount ENDF data (Windows example)
      - C:/Users/YourName/ENDF-Data/ENDF-B-VIII.1:/app/endf-data:ro
    environment:
      - PYTHONUNBUFFERED=1
      - SMRFORGE_ENDF_DIR=/app/endf-data
    command: tail -f /dev/null
```

**Python script (inside container):**
```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, CrossSectionTable
import numpy as np

# Initialize with mounted directory
cache = NuclearDataCache(local_endf_dir=Path("/app/endf-data"))

# Create table with cache
xs_table = CrossSectionTable(cache=cache)

# Generate cross sections
nuclides = [Nuclide(92, 235), Nuclide(92, 238)]
group_structure = np.logspace(7, -1, 70)

xs_df = xs_table.generate_multigroup(
    nuclides=nuclides,
    reactions=['total', 'fission', 'capture'],
    group_structure=group_structure,
    temperature=900.0
)

print(f"Success! Generated {len(xs_df)} entries")
```

### Verify Mount (Optional)

Verify the mount is working:

```bash
# Check if files are visible in container
docker compose exec smrforge ls -la /app/endf-data

# Check for neutron files
docker compose exec smrforge ls /app/endf-data/neutrons-version.VIII.1/ | head -10

# Test Python access
docker compose exec smrforge python -c "
from pathlib import Path
from smrforge.core.reactor_core import scan_endf_directory
results = scan_endf_directory(Path('/app/endf-data'))
print(f'Found {results[\"valid_files\"]} valid ENDF files')
"
```

---

## Troubleshooting

### "ENDF file not found" Error

**Symptoms:**
```
FileNotFoundError: ENDF file not found for U235 (endfb8.0).
```

**Solutions:**
1. **Verify directory path:**
   ```python
   from pathlib import Path
   endf_dir = Path("C:/path/to/ENDF-B-VIII.1")
   print(f"Exists: {endf_dir.exists()}")
   print(f"Is directory: {endf_dir.is_dir()}")
   ```

2. **Check file discovery:**
   ```python
   from smrforge.core.reactor_core import scan_endf_directory
   results = scan_endf_directory(endf_dir)
   print(f"Valid files: {results['valid_files']}")
   ```

3. **Verify cache initialization:**
   ```python
   cache = NuclearDataCache(local_endf_dir=endf_dir)
   # Check if index was built
   print(f"Index size: {len(cache._local_file_index) if cache._local_file_index else 0}")
   ```

### "No valid ENDF files found"

**Possible causes:**
- Files are corrupted
- Files are not in ENDF format
- Directory path is incorrect

**Solutions:**
1. Re-download ENDF files from NNDC
2. Verify file format (should start with ENDF header)
3. Check directory path spelling

### Docker: "Directory not found" or "Permission denied"

**Symptoms:**
- Files not visible in container
- Permission errors when accessing files

**Solutions:**
1. **Check path format in docker-compose.yml:**
   - Windows: Use forward slashes: `C:/Users/Name/ENDF-Data`
   - Or escape backslashes: `C:\\Users\\Name\\ENDF-Data`

2. **Verify mount:**
   ```bash
   docker compose exec smrforge ls -la /app/endf-data
   ```

3. **Check file permissions:**
   - Ensure files are readable
   - On Linux/Mac: `chmod -R 755 ~/ENDF-Data`

4. **Restart container:**
   ```bash
   docker compose down
   docker compose up -d smrforge
   ```

### CrossSectionTable Not Using Cache

**Symptoms:**
- Still getting "file not found" errors even after setting up cache

**Solution:**
Make sure to pass the cache to `CrossSectionTable`:

```python
# ❌ Wrong - creates new cache without local_endf_dir
xs_table = CrossSectionTable()

# ✅ Correct - uses your cache
cache = NuclearDataCache(local_endf_dir=Path("C:/path/to/ENDF"))
xs_table = CrossSectionTable(cache=cache)
```

### Files Found But Parsing Fails

**Symptoms:**
```
ImportError: Failed to parse cross-section data for U235/fission.
```

**Solutions:**
1. **Install ENDF parser:**
   ```bash
   pip install endf-parserpy
   # Or
   pip install sandy
   ```

2. **Check file integrity:**
   - Re-download the specific file
   - Verify file is not corrupted

3. **Check reaction availability:**
   - Some nuclides don't have all reactions (e.g., O-16 doesn't have fission)
   - The code should skip missing reactions automatically

---

## Additional Resources

- **NNDC ENDF Website:** https://www.nndc.bnl.gov/endf/
- **IAEA Nuclear Data Services:** https://www-nds.iaea.org/
- **ENDF Format Documentation:** https://www.nndc.bnl.gov/endf/b8.0/manual/
- **SMRForge Documentation:** See `README.md` and other `.md` files in project root

---

## Summary Checklist

- [ ] Downloaded ENDF/B-VIII.1 (or VIII.0) from NNDC or IAEA
- [ ] Extracted files to a directory (e.g., `~/ENDF-Data/ENDF-B-VIII.1`)
- [ ] Verified `neutrons-version.VIII.1/` directory contains `.endf` files
- [ ] For local use: Initialized `NuclearDataCache` with `local_endf_dir` parameter
- [ ] For Docker: Added volume mount in `docker-compose.yml`
- [ ] For Docker: Restarted container (`docker compose down && docker compose up -d`)
- [ ] Ran verification script to confirm setup works
- [ ] Passed cache to `CrossSectionTable(cache=cache)` in code

---

**Need help?** Check the troubleshooting section above or open an issue on the project repository.

