# Quick Start: Using ENDF Data in Docker

If you're getting download errors when running SMRForge in Docker, you need to mount your local ENDF data directory.

## Quick Fix

1. **Edit `docker-compose.yml`** and uncomment the ENDF volume mount:

```yaml
volumes:
  # ... other volumes ...
  # Uncomment this line and set path to your ENDF directory:
  - ~/ENDF-Data:/app/endf-data:ro
  # Or use a specific path:
  # - C:/Users/YourName/Downloads/ENDF-B-VIII.1:/app/endf-data:ro
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

## Getting ENDF Data

### Option 1: Download Bulk ENDF Files

1. Download ENDF/B-VIII.1 from NNDC: https://www.nndc.bnl.gov/endf/
2. Extract to a directory (e.g., `~/ENDF-Data`)
3. Mount in `docker-compose.yml` as shown above

### Option 2: Organize Existing Downloads

If you already have ENDF files downloaded:

```bash
# Access container
docker compose exec smrforge-dev bash

# Inside container, organize files
python -c "
from pathlib import Path
from smrforge.core.reactor_core import organize_bulk_endf_downloads

stats = organize_bulk_endf_downloads(
    source_dir=Path('/app/endf-data/raw'),
    target_dir=Path('/app/endf-data'),
    library_version='VIII.1'
)
print(f'Organized {stats[\"files_organized\"]} files')
"
```

### Option 3: Use Standard Directory

```python
from pathlib import Path
from smrforge.core.reactor_core import get_standard_endf_directory, NuclearDataCache

# Get standard directory path
endf_dir = get_standard_endf_directory()
# This returns ~/ENDF-Data (or %USERPROFILE%\ENDF-Data on Windows)

# Mount this directory in docker-compose.yml
# Then use it:
cache = NuclearDataCache(local_endf_dir=Path("/app/endf-data"))
```

## Example: Complete Integration with ENDF Data

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

# Initialize cache with local ENDF directory
cache = NuclearDataCache(
    local_endf_dir=Path("/app/endf-data")  # Mounted volume
)

# Use as normal - files are automatically discovered
u235 = Nuclide(Z=92, A=235, m=0)
energy, xs = cache.get_cross_section(
    u235, 
    "fission", 
    library=Library.ENDF_B_VIII_1
)
```

## Troubleshooting

### Error: "Failed to download ENDF file"

This means automatic downloads failed. Solutions:

1. **Mount local ENDF directory** (recommended)
2. **Check network connectivity** in container
3. **Use SANDY** for downloads (if available)

### Error: "Local ENDF directory checked: /app/endf-data"

The directory is mounted but no files found. Check:

1. **Directory exists** on host: `ls ~/ENDF-Data`
2. **Volume mount** is correct in `docker-compose.yml`
3. **Files are organized** using `organize_bulk_endf_downloads()`

### Files Not Found

Use the scanning utility to see what's available:

```python
from pathlib import Path
from smrforge.core.reactor_core import scan_endf_directory

results = scan_endf_directory(Path("/app/endf-data"))
print(f"Found {results['valid_files']} valid ENDF files")
print(f"Nuclides: {results['nuclides'][:10]}")
```

## See Also

- `BULK_ENDF_STORAGE.md` - Complete guide for bulk storage
- `DOCKER.md` - Full Docker documentation
- `NUCLEAR_DATA_BACKENDS.md` - Nuclear data backend information

