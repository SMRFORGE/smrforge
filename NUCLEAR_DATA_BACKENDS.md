# Nuclear Data Backend Alternatives

SMRForge supports multiple backends for parsing ENDF nuclear cross-section data. The system will try them in order until one succeeds.

## Supported Backends (in order of preference)

### 1. SANDY (Recommended)
- **Pros**: Pure Python, easy to install, no compilation needed, well-maintained
- **Cons**: Potentially slower than compiled alternatives for very large files
- **Installation**: `pip install sandy`
- **Status**: Recommended for most users

### 2. Simple ENDF Parser (Fallback)
- **Pros**: No external dependencies, built into SMRForge
- **Cons**: Limited to basic reactions (total, elastic, fission, capture), less robust
- **Installation**: None required (built-in)
- **Status**: Fallback for basic use cases

## Local ENDF Directory Support

SMRForge supports using local ENDF files for faster, offline access with **automatic file discovery** from bulk downloads.

### Benefits
- **Offline Use**: No network connection required
- **Faster Access**: ~800x faster than downloads (0.08s → 0.0001s)
- **Reliable**: No dependency on external servers
- **Latest Data**: Use ENDF/B-VIII.1 (August 2024) or any version you have
- **Flexible Structure**: Automatically discovers files regardless of directory structure
- **Bulk Downloads**: Organize and index bulk-downloaded files from NNDC/IAEA

### Standard Directory

Get the recommended directory for storing bulk ENDF files:

```python
from smrforge.core.reactor_core import get_standard_endf_directory

endf_dir = get_standard_endf_directory()
# Windows: C:\Users\YourName\ENDF-Data
# Unix/Mac: ~/ENDF-Data
```

### Organizing Bulk Downloads

After downloading ENDF files in bulk, organize them:

```python
from pathlib import Path
from smrforge.core.reactor_core import organize_bulk_endf_downloads

# Organize files from bulk download
stats = organize_bulk_endf_downloads(
    source_dir=Path("C:/Users/user/Downloads/ENDF-B-VIII.1"),
    library_version="VIII.1"
)

print(f"Organized {stats['files_organized']} files")
```

### Usage

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Library, get_standard_endf_directory

# Option 1: Use standard directory
endf_dir = get_standard_endf_directory()
cache = NuclearDataCache(local_endf_dir=endf_dir)

# Option 2: Use any directory with ENDF files (flexible structure)
cache = NuclearDataCache(
    local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1")
)

# Use as normal - files automatically discovered
# Falls back to download if local file not found
```

### Scanning Directories

Check what files are available:

```python
from smrforge.core.reactor_core import scan_endf_directory

results = scan_endf_directory(Path("C:/path/to/ENDF-B-VIII.1"))
print(f"Found {results['valid_files']} valid ENDF files")
print(f"Directory structure: {results['directory_structure']}")
```

**See**: [`ENDF_DOCUMENTATION.md`](ENDF_DOCUMENTATION.md) for complete documentation on bulk storage, organization, setup, and usage.

### Expected Directory Structure

```
ENDF-B-VIII.1/
├── neutrons-version.VIII.1/
│   ├── n-001_H_001.endf
│   ├── n-092_U_235.endf
│   └── ...
├── protons-version.VIII.1/
└── ...
```

### File Discovery Priority

1. **Cache directory** - Check if file already exists in cache
2. **Local ENDF directory** - Scan local directory (if provided) with O(1) lookup
3. **Download** - Attempt to download from NNDC/IAEA with multiple URL fallbacks
4. **Version fallback** - Try older library version (e.g., VIII.1 → VIII.0)

### Performance

- **Index building**: ~0.09s for 557 files (one-time, on initialization)
- **File lookup**: <0.0001s (instant, cached dictionary)
- **File copying**: Fast (files typically 50-500 KB)

**See**: [`ENDF_DOCUMENTATION.md`](ENDF_DOCUMENTATION.md) for complete documentation.

## How It Works

**Automatic downloads are enabled by default!** The system will automatically download ENDF files when needed.

When cross-section data is needed:

1. **Check cache first**: Data is cached in Zarr format for fast access (no download needed if cached)
2. **Check local directory**: If `local_endf_dir` provided, scan for local files (fast O(1) lookup)
3. **Automatic download**: If local file not found, automatically attempts download from multiple sources:
   - NNDC (National Nuclear Data Center) - multiple URL formats
   - IAEA Nuclear Data Services - multiple URL formats
   - Tries multiple URLs until one succeeds
   - Falls back to older library versions if needed (e.g., VIII.1 → VIII.0)
4. **Try SANDY**: If data not cached and SANDY available, use it for parsing
5. **Try simple parser**: If SANDY not available, use built-in parser for common reactions
6. **Error if all fail**: Clear error message with installation instructions and manual download links

### Automatic Download Features

- **No configuration needed**: Works out of the box
- **Multiple URL fallbacks**: Tries 5-7 different URL patterns per nuclide
- **Version fallback**: Automatically tries older library versions if newer ones fail
- **Content validation**: Verifies downloaded files are valid ENDF format
- **Caching**: Downloads are cached locally for future use
- **Error handling**: Clear error messages with solutions if downloads fail

## Installation Recommendations

### For Docker/Production
```bash
# Option 1: Install SANDY (recommended, no build tools)
pip install sandy

# Option 2: Pre-populate cache (no runtime dependencies)
# Pre-process cross-sections and place in cache directory
```

### For Development
```bash
# Install SANDY for best experience
pip install sandy

# Or use the built-in parser (limited features)
# No installation needed
```

## Pre-populating Cache (No Backend Needed)

You can pre-populate the cache directory with processed cross-section data:

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
import numpy as np
import zarr

# Cache location (default: ~/.smrforge/nucdata)
cache_dir = Path.home() / ".smrforge" / "nucdata"

# Pre-populate using any tool (SANDY, NJOY, etc.)
# Data should be stored as: {library}/{nuclide}/{reaction}/{temperature}K/energy and xs
```

## Supported Nuclear Data Libraries

SMRForge supports multiple ENDF library versions:

- **ENDF/B-VIII.1** (August 2024) - Latest version, with local directory support
- **ENDF/B-VIII.0** - Previous version, with automatic fallback from VIII.1
- **JEFF-3.3** - European nuclear data library
- **JENDL-5.0** - Japanese evaluated nuclear data library

The system automatically handles version fallback (e.g., if VIII.1 file not found, tries VIII.0).

## Docker Considerations

The Dockerfile does not require any nuclear data backends. At runtime:

1. **Option 1**: Install SANDY in the running container:
   ```bash
   docker compose exec smrforge pip install sandy
   ```

2. **Option 2**: Use pre-populated cache data mounted as a volume

## Error Messages

If no backend is available, you'll get a clear error message:
```
Failed to parse cross-section data for U235/total. No suitable backend available.

Installed backends: None

To enable cross-section fetching, install SANDY:
  - SANDY (recommended): pip install sandy
    Pure Python, easy to install

Note: SMRForge includes a built-in ENDF parser, but it failed to parse this file.
This may indicate an issue with the ENDF file format or unsupported reaction.
```

## Performance Notes

- **Cached data**: Fastest (no parsing needed)
- **SANDY**: Fast (pure Python, but efficient)
- **Simple parser**: Slowest (basic implementation)

Once data is cached, all backends perform the same (just reading from cache).
