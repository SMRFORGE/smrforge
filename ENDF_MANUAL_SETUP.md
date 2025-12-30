# ENDF Data Manual Setup Guide

SMRForge requires ENDF (Evaluated Nuclear Data File) nuclear data files for cross-section calculations. **ENDF files must be downloaded and set up manually** - SMRForge does not automatically download them.

This guide walks you through:
1. Downloading ENDF files in bulk
2. Setting up files for local use
3. Mounting files in Docker containers

---

## Table of Contents

- [Quick Start](#quick-start)
- [Step 1: Download ENDF Files](#step-1-download-endf-files)
- [Step 2: Extract Files](#step-2-extract-files)
- [Step 3: Local Setup (Python Scripts)](#step-3-local-setup-python-scripts)
- [Step 4: Docker Setup](#step-4-docker-setup)
- [Step 5: Verify Setup](#step-5-verify-setup)
- [Directory Structure](#directory-structure)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

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

## Step 1: Download ENDF Files

### Option A: NNDC (National Nuclear Data Center) - Recommended

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

### Option B: IAEA Nuclear Data Services

1. **Visit IAEA NDS:**
   - URL: https://www-nds.iaea.org/
   - Alternative source for ENDF data

2. **Download ENDF/B-VIII.1:**
   - Navigate to ENDF/B-VIII.1 section
   - Download the complete library archive

### What You Need

- **Neutron data** (required): Contains cross-section data for neutron interactions
- **Other sub-libraries** (optional): Protons, alphas, decay data, etc.

**Minimum requirement:** The `neutrons-version.VIII.1/` directory with `.endf` files.

---

## Step 2: Extract Files

### Windows

1. **Right-click the downloaded archive** → "Extract All..."
2. **Choose extraction location:**
   - Recommended: `C:\Users\YourName\ENDF-Data`
   - Or: `C:\Users\YourName\Downloads\ENDF-B-VIII.1`
3. **Extract** and wait for completion

### Linux/Mac

```bash
# For .zip files
unzip ENDF-B-VIII.1.zip -d ~/ENDF-Data

# For .tar.gz files
tar -xzf ENDF-B-VIII.1.tar.gz -C ~/ENDF-Data
```

### Verify Extraction

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

---

## Step 3: Local Setup (Python Scripts)

### Method 1: Direct Path (Simple)

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

### Method 2: Standard Directory (Recommended)

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

### Method 3: Environment Variable

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

### Complete Example

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
from smrforge.core.reactor_core import CrossSectionTable

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

import numpy as np
group_structure = np.logspace(7, -1, 70)  # 70-group structure

xs_df = xs_table.generate_multigroup(
    nuclides=nuclides,
    reactions=['total', 'fission', 'capture'],
    group_structure=group_structure,
    temperature=900.0  # Kelvin
)

print(f"Generated {len(xs_df)} cross-section entries")
```

---

## Step 4: Docker Setup

### Prerequisites

- Docker Desktop installed and running
- ENDF files downloaded and extracted (see Steps 1-2)

### Step 4.1: Locate Your ENDF Directory

Note the full path to your extracted ENDF directory:

**Windows:**
- Example: `C:\Users\YourName\ENDF-Data\ENDF-B-VIII.1`
- Or: `C:\Users\YourName\Downloads\ENDF-B-VIII.1`

**Linux/Mac:**
- Example: `~/ENDF-Data/ENDF-B-VIII.1`
- Or: `/home/username/ENDF-Data/ENDF-B-VIII.1`

### Step 4.2: Edit docker-compose.yml

Open `docker-compose.yml` in your project root and find the `volumes:` section under the `smrforge:` service:

```yaml
services:
  smrforge:
    # ... other configuration ...
    volumes:
      - ./data:/app/data:rw
      - ./output:/app/output:rw
      - ./examples:/app/examples:ro
      # Add your ENDF directory mount here:
      # For Windows (use forward slashes or escaped backslashes):
      - C:/Users/YourName/ENDF-Data/ENDF-B-VIII.1:/app/endf-data:ro
      # For Linux/Mac:
      # - ~/ENDF-Data/ENDF-B-VIII.1:/app/endf-data:ro
```

**Important Notes:**
- Use forward slashes (`/`) in Windows paths, or escape backslashes (`\\`)
- The `:ro` flag makes it read-only (recommended for data files)
- Replace `YourName` with your actual username
- The path after `:` (`/app/endf-data`) is the mount point inside the container

### Step 4.3: Restart Docker Container

After editing `docker-compose.yml`:

```bash
# Stop the container
docker compose down

# Start it again (this applies the new volume mount)
docker compose up -d smrforge
```

### Step 4.4: Use in Docker Code

In your Python scripts running inside Docker, use the mounted directory:

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, CrossSectionTable

# The ENDF directory is mounted at /app/endf-data
cache = NuclearDataCache(local_endf_dir=Path("/app/endf-data"))

# Create cross-section table with the cache
xs_table = CrossSectionTable(cache=cache)

# Use as normal...
```

### Step 4.5: Verify Mount (Optional)

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

---

## Step 5: Verify Setup

### Quick Verification Script

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

### Expected Output

```
Testing ENDF directory: C:/Users/YourName/ENDF-Data/ENDF-B-VIII.1
Directory exists: True

Scanning directory...
Total files found: 5135
Valid ENDF files: 557
Directory structure: standard

Testing NuclearDataCache...
✓ U-235: Found at n-092_U_235.endf
✓ U-238: Found at n-092_U_238.endf
✓ O-16: Found at n-008_O_016.endf

✓ Setup verification complete!
```

---

## Directory Structure

SMRForge supports **flexible directory structures** - it will automatically discover ENDF files regardless of how they're organized.

### Standard Structure (Recommended)

```
ENDF-B-VIII.1/
├── neutrons-version.VIII.1/
│   ├── n-001_H_001.endf
│   ├── n-092_U_235.endf
│   ├── n-092_U_238.endf
│   └── ... (500+ files)
├── protons-version.VIII.1/
├── decay-version.VIII.1/
└── ... (other sub-libraries)
```

### Alternative Structures (Also Supported)

**Flat directory:**
```
ENDF-Data/
├── n-001_H_001.endf
├── n-092_U_235.endf
└── ... (all .endf files in root)
```

**Nested directories:**
```
ENDF-Data/
├── library1/
│   ├── neutrons/
│   │   └── n-092_U_235.endf
│   └── ...
└── library2/
    └── ...
```

**Mixed structures:** Any combination of the above.

SMRForge will recursively scan and find all `.endf` files.

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

