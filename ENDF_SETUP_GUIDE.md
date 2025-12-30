# ENDF Data Setup Guide

SMRForge requires ENDF nuclear data files for cross-section calculations. **ENDF files must be set up manually** - the package does not automatically download them.

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

1. **Download ENDF files**:
   - Visit https://www.nndc.bnl.gov/endf/
   - Download ENDF/B-VIII.1 (recommended) or ENDF/B-VIII.0
   - Extract to a directory

2. **Set up in code**:
   ```python
   from pathlib import Path
   from smrforge.core.reactor_core import NuclearDataCache
   
   cache = NuclearDataCache(
       local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1")
   )
   ```

3. **Validate setup**:
   ```python
   from smrforge.core.endf_setup import validate_endf_setup
   
   is_valid, results = validate_endf_setup(Path("C:/path/to/ENDF-B-VIII.1"))
   if is_valid:
       print(f"✓ Setup valid! Found {results['valid_files']} files")
   else:
       print(f"✗ Setup invalid: {results['errors']}")
   ```

## Standard Directory

The recommended location for ENDF files:

```python
from smrforge.core.reactor_core import get_standard_endf_directory

endf_dir = get_standard_endf_directory()
# Windows: C:\Users\YourName\ENDF-Data
# Linux/Mac: ~/ENDF-Data
```

## Directory Structure

ENDF files can be in any structure - SMRForge will find them automatically:

**Standard structure (recommended):**
```
ENDF-Data/
├── neutrons-version.VIII.1/
│   ├── n-001_H_001.endf
│   ├── n-092_U_235.endf
│   └── ...
```

**Flexible structures (also supported):**
- Flat directory: All `.endf` files in one folder
- Nested directories: Files in subdirectories
- Mixed structures: Any combination

## Validation

The setup wizard automatically validates:
- ✅ File format (valid ENDF files)
- ✅ File naming (can parse nuclide from filename)
- ✅ File integrity (not corrupted)
- ✅ Directory structure
- ✅ Access to common nuclides (U-235, U-238, O-16)

## Organizing Files

If you have ENDF files in a messy structure, organize them:

```python
from pathlib import Path
from smrforge.core.reactor_core import organize_bulk_endf_downloads

stats = organize_bulk_endf_downloads(
    source_dir=Path("C:/Users/YourName/Downloads/ENDF-B-VIII.1"),
    target_dir=Path("C:/Users/YourName/ENDF-Data"),
    library_version="VIII.1"
)

print(f"Organized {stats['files_organized']} files")
```

## Docker Setup

In Docker containers:

1. **Mount your ENDF directory** in `docker-compose.yml`:
   ```yaml
   volumes:
     - ~/ENDF-Data:/app/endf-data:ro
   ```

2. **Run setup wizard**:
   ```bash
   docker compose exec smrforge python -m smrforge.core.endf_setup
   ```

3. **Use in code**:
   ```python
   cache = NuclearDataCache(local_endf_dir=Path("/app/endf-data"))
   ```

See `DOCKER.md` and `DOCKER_ENDF_QUICKSTART.md` for details.

## Troubleshooting

### "ENDF file not found" Error

**Solution**: Run the setup wizard to configure ENDF files:
```bash
python -m smrforge.core.endf_setup
```

### "No valid ENDF files found"

**Possible causes**:
- Files are corrupted
- Files are not in ENDF format
- Directory path is incorrect

**Solution**: 
- Re-download ENDF files
- Check file format
- Verify directory path

### Files Not Discovered

**Solution**: Use the scanning utility:
```python
from smrforge.core.reactor_core import scan_endf_directory

results = scan_endf_directory(Path("C:/path/to/ENDF"))
print(f"Found {results['valid_files']} valid files")
print(f"Structure: {results['directory_structure']}")
```

## See Also

- `BULK_ENDF_STORAGE.md` - Detailed bulk storage guide
- `DOCKER_ENDF_QUICKSTART.md` - Docker-specific guide
- `NUCLEAR_DATA_BACKENDS.md` - Backend information

