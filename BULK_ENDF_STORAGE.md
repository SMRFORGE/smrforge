# Bulk ENDF File Storage Guide

This guide explains how to store and organize bulk-downloaded ENDF files for use with SMRForge.

## Standard Directory Structure

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

## Automatic File Discovery

SMRForge automatically discovers ENDF files regardless of directory structure. You can:

1. **Use standard structure** (recommended): Organize files into `neutrons-version.VIII.1/`
2. **Use flat structure**: Place all `.endf` files in the root directory
3. **Use nested structure**: Files can be in any subdirectory - SMRForge will find them

The system supports:
- Standard ENDF naming: `n-092_U_235.endf`
- Alternative naming: `U235.endf`, `u235.endf`, `92235.endf`
- Multiple library versions in the same directory

## Organizing Bulk Downloads

After downloading ENDF files in bulk from NNDC or IAEA, use the organization function:

```python
from pathlib import Path
from smrforge.core.reactor_core import organize_bulk_endf_downloads

# Organize files downloaded to your Downloads folder
stats = organize_bulk_endf_downloads(
    source_dir=Path("C:/Users/YourName/Downloads/ENDF-B-VIII.1"),
    library_version="VIII.1"
)

print(f"Organized {stats['files_organized']} files")
print(f"Found {stats['files_found']} total files")
print(f"Indexed {stats['nuclides_indexed']} unique nuclides")
```

### What It Does

1. **Scans recursively**: Finds all `.endf` files in source directory and subdirectories
2. **Validates files**: Checks that files are valid ENDF format
3. **Parses nuclides**: Extracts nuclide information from filenames
4. **Organizes**: Copies files to standard structure with standard naming
5. **Deduplicates**: Skips duplicate nuclides (keeps first file found)

### Dry Run (Preview)

To see what would be organized without actually copying files:

```python
stats = organize_bulk_endf_downloads(
    source_dir=Path("C:/Users/YourName/Downloads/ENDF-B-VIII.1"),
    library_version="VIII.1",
    create_structure=False  # Preview only
)
```

## Scanning Existing Directories

Check what files are available in a directory:

```python
from smrforge.core.reactor_core import scan_endf_directory

results = scan_endf_directory(Path("C:/Users/YourName/Downloads/ENDF-B-VIII.1"))

print(f"Total files: {results['total_files']}")
print(f"Valid files: {results['valid_files']}")
print(f"Directory structure: {results['directory_structure']}")
print(f"Library versions: {results['library_versions']}")
print(f"Sample nuclides: {results['nuclides'][:10]}")
```

## Using with NuclearDataCache

Once files are organized (or even if they're not), use them with `NuclearDataCache`:

```python
from smrforge.core.reactor_core import (
    NuclearDataCache,
    Nuclide,
    Library,
    get_standard_endf_directory
)

# Use standard directory
endf_dir = get_standard_endf_directory()
cache = NuclearDataCache(local_endf_dir=endf_dir)

# Or use any directory with ENDF files
cache = NuclearDataCache(
    local_endf_dir=Path("C:/Users/YourName/Downloads/ENDF-B-VIII.1")
)

# Use as normal - files are automatically discovered
u235 = Nuclide(Z=92, A=235, m=0)
energy, xs = cache.get_cross_section(u235, "fission", library=Library.ENDF_B_VIII_1)
```

## Downloading from NNDC and IAEA

### NNDC (National Nuclear Data Center)

1. Visit: https://www.nndc.bnl.gov/endf/
2. Download ENDF/B-VIII.1 or ENDF/B-VIII.0
3. Extract to a directory
4. Use `organize_bulk_endf_downloads()` to organize

### IAEA Nuclear Data Services

1. Visit: https://www-nds.iaea.org/
2. Navigate to ENDF data downloads
3. Download bulk files
4. Use `organize_bulk_endf_downloads()` to organize

## File Discovery Priority

When `NuclearDataCache` needs an ENDF file, it checks in this order:

1. **Cache directory**: `~/.smrforge/nucdata/endf/{library}/{nuclide}.endf`
2. **Local ENDF directory**: Recursively scans `local_endf_dir` for files
3. **Automatic download**: Downloads from NNDC/IAEA if not found locally

## Performance

- **Index building**: ~0.09s for 557 files (one-time, on initialization)
- **File lookup**: <0.0001s (instant, cached dictionary)
- **Recursive scanning**: Handles thousands of files efficiently

## Tips

1. **Organize once**: Use `organize_bulk_endf_downloads()` to organize files into standard structure
2. **Use standard directory**: Store files in `get_standard_endf_directory()` for consistency
3. **Multiple versions**: You can store multiple library versions in the same directory
4. **Flexible naming**: System handles various filename formats automatically
5. **Validation**: Invalid files are automatically skipped during organization

## Example Workflow

```python
from pathlib import Path
from smrforge.core.reactor_core import (
    get_standard_endf_directory,
    organize_bulk_endf_downloads,
    NuclearDataCache,
    Nuclide,
    Library
)

# Step 1: Get standard directory
endf_dir = get_standard_endf_directory()
print(f"Standard directory: {endf_dir}")

# Step 2: Organize bulk download
stats = organize_bulk_endf_downloads(
    source_dir=Path("C:/Users/YourName/Downloads/ENDF-B-VIII.1"),
    target_dir=endf_dir,
    library_version="VIII.1"
)
print(f"Organized {stats['files_organized']} files")

# Step 3: Use with NuclearDataCache
cache = NuclearDataCache(local_endf_dir=endf_dir)

# Step 4: Access nuclear data (files automatically discovered)
u235 = Nuclide(Z=92, A=235, m=0)
energy, xs = cache.get_cross_section(u235, "fission", library=Library.ENDF_B_VIII_1)
print(f"U-235 fission cross-section: {len(energy)} energy points")
```

## Troubleshooting

### Files Not Found

- Check that `local_endf_dir` path is correct
- Verify files have `.endf` extension
- Use `scan_endf_directory()` to see what files are detected

### Invalid Files

- Files that fail validation are skipped
- Check file headers are valid ENDF format
- Re-download corrupted files

### Duplicate Nuclides

- System keeps first file found for each nuclide
- Use `organize_bulk_endf_downloads()` to standardize naming
- Check for duplicate files in source directory

