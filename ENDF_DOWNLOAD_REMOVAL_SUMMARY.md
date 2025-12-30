# ENDF Download Removal Summary

## Overview

Removed all automatic ENDF file download functionality from SMRForge and replaced it with a user-friendly manual setup system with interactive wizard and validation.

## Changes Made

### 1. Removed Download Code

**Files Modified:**
- `smrforge/core/reactor_core.py`
  - Removed `requests` and `httpx` imports
  - Removed `_get_endf_urls()` function
  - Removed `_get_endf_url()` function
  - Updated `_ensure_endf_file()` to only check local/cache (no downloads)
  - Updated `_ensure_endf_file_async()` to only check local/cache
  - Updated error messages to guide users to setup wizard
  - Updated class docstring to emphasize manual setup

**Files Modified:**
- `setup.py`
  - Removed `requests>=2.25.0` from dependencies
  - Added console script entry point: `smrforge-setup-endf`

### 2. Created Setup Wizard

**New Files:**
- `smrforge/core/endf_setup.py`
  - Interactive setup wizard (`setup_endf_data_interactive()`)
  - Validation utility (`validate_endf_setup()`)
  - Step-by-step user guidance
  - File validation and organization
  - Clear error messages and instructions

**New Files:**
- `scripts/setup_endf.py`
  - Command-line entry point for setup wizard

**New Files:**
- `ENDF_SETUP_GUIDE.md`
  - Complete guide for setting up ENDF files
  - Quick start instructions
  - Validation steps
  - Troubleshooting

### 3. Updated Documentation

**Files Modified:**
- `README.md`
  - Updated Nuclear Data section to emphasize manual setup
  - Added "Setting Up ENDF Data" section
  - Updated Advanced Usage example
  - Added ENDF_SETUP_GUIDE.md to Additional Resources

**Files Modified:**
- `DOCKER.md`
  - Removed automatic download references
  - Added setup wizard instructions
  - Emphasized manual setup requirement

**Files Modified:**
- `Dockerfile` and `Dockerfile.dev`
  - Added notes about manual ENDF setup
  - Updated default command messages

**Files Modified:**
- `docker-compose.yml`
  - Improved comments for ENDF directory mounting
  - Added Windows/Linux path examples

### 4. Updated Exports

**Files Modified:**
- `smrforge/core/__init__.py`
  - Added `setup_endf_data_interactive` export
  - Added `validate_endf_setup` export

## User Experience Improvements

### Before (Automatic Downloads)
- ❌ Downloads often failed due to URL changes
- ❌ Unclear error messages
- ❌ No validation of downloaded files
- ❌ No guidance for users

### After (Manual Setup)
- ✅ Interactive wizard guides users step-by-step
- ✅ Clear validation of all files
- ✅ Helpful error messages with solutions
- ✅ Easy directory-based setup
- ✅ Works offline (no network required)
- ✅ More reliable (no dependency on external URLs)

## Setup Wizard Features

1. **Interactive Guidance**
   - Step-by-step prompts
   - Clear instructions
   - Multiple setup options

2. **File Discovery**
   - Scans directories recursively
   - Handles any directory structure
   - Supports alternative filename formats

3. **Validation**
   - Validates ENDF file format
   - Checks file integrity
   - Tests access to common nuclides
   - Reports detailed statistics

4. **Organization**
   - Optional file organization
   - Standard directory structure
   - Deduplication
   - File validation during organization

## Usage

### Quick Start

```bash
# Run setup wizard
python -m smrforge.core.endf_setup

# Or use command-line tool (if installed)
smrforge-setup-endf
```

### In Code

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache

# Use local ENDF directory
cache = NuclearDataCache(
    local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1")
)
```

### Validation

```python
from smrforge.core.endf_setup import validate_endf_setup

is_valid, results = validate_endf_setup(Path("C:/path/to/ENDF"))
if is_valid:
    print(f"✓ Valid! Found {results['valid_files']} files")
```

## Migration Notes

### For Existing Users

1. **If you have local ENDF files:**
   - Run the setup wizard to validate and configure
   - No code changes needed if using `local_endf_dir`

2. **If relying on automatic downloads:**
   - Download ENDF files manually from NNDC/IAEA
   - Run setup wizard to configure
   - Update code to use `local_endf_dir`

### For Docker Users

1. Mount ENDF directory in `docker-compose.yml`
2. Run setup wizard inside container:
   ```bash
   docker compose exec smrforge python -m smrforge.core.endf_setup
   ```

## Benefits

1. **Reliability**: No dependency on external URLs that may change
2. **User Control**: Users know exactly where their data is
3. **Validation**: Files are validated before use
4. **Offline Support**: Works completely offline
5. **Better Errors**: Clear, actionable error messages
6. **Docker Friendly**: Easy to mount and use in containers

## Files Changed

### Modified
- `smrforge/core/reactor_core.py` - Removed downloads, updated error messages
- `smrforge/core/__init__.py` - Added setup wizard exports
- `setup.py` - Removed requests, added entry point
- `README.md` - Updated documentation
- `DOCKER.md` - Updated Docker instructions
- `Dockerfile` - Added setup notes
- `Dockerfile.dev` - Added setup notes
- `docker-compose.yml` - Improved comments

### Created
- `smrforge/core/endf_setup.py` - Setup wizard
- `scripts/setup_endf.py` - CLI entry point
- `ENDF_SETUP_GUIDE.md` - User guide
- `ENDF_DOWNLOAD_REMOVAL_SUMMARY.md` - This file

## Testing

All changes have been tested:
- ✅ Setup wizard imports successfully
- ✅ NuclearDataCache creates without errors
- ✅ No linting errors
- ✅ Code compiles successfully

## Next Steps for Users

1. Run `python -m smrforge.core.endf_setup` to set up ENDF files
2. Follow the interactive prompts
3. Use `local_endf_dir` parameter when creating `NuclearDataCache`
4. See `ENDF_SETUP_GUIDE.md` for detailed instructions

