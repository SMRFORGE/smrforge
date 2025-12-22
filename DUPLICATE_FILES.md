# Duplicate File Structure - Cleanup Plan

## Current Situation

There are duplicate/legacy files in the root directory that mirror files in the `smrforge/` package structure.

### Root-Level Directories (Legacy - Can be removed)
These appear to be legacy files from before the package structure was organized:

- `neutronics/` → Use `smrforge/neutronics/` instead
- `thermal/` → Use `smrforge/thermal/` instead
- `geometry/` → Use `smrforge/geometry/` instead
- `nucdata/` → Use `smrforge/core/` instead
- `safety/` → Use `smrforge/safety/` instead
- `validation/` → Use `smrforge/validation/` instead
- `uncertainty/` → Use `smrforge/uncertainty/` instead
- `presets/` → Use `smrforge/presets/` instead

### Recommendation

**Remove root-level directories** - The package structure (`smrforge/`) is the authoritative source.

However, before removing, we should:
1. Verify all code imports from `smrforge/` package
2. Check if any examples or tests reference root-level files
3. Archive important code if needed

---

## Files to Keep in Root

These are documentation/configuration files and should stay:
- `setup.py`
- `requirements.txt`
- `requirements-dev.txt`
- `pyproject.toml`
- `README.md`
- `LICENSE`
- Documentation files (`*.md`)
- `examples/` directory
- `tests/` directory
- `docs/` directory
- `additional_modules.py` (starter code for future implementation)

---

## Action Plan

### Phase 1: Verification
1. Search codebase for imports from root-level modules
2. Update any imports to use `smrforge/` package
3. Verify tests still pass

### Phase 2: Cleanup
1. Move `backup_*/` to archive if needed
2. Remove root-level module directories
3. Update documentation if needed

---

## Current Status

**Status**: ✅ **COMPLETED** - All legacy root-level directories have been removed.

**Cleanup Date**: 2024-12-21

**Actions Taken**:
1. ✅ Verified all code imports from `smrforge/` package
2. ✅ Updated `pydantic_integration_guide.py` to use correct imports (`smrforge.validation.*`)
3. ✅ Removed all root-level legacy directories:
   - `neutronics/`
   - `thermal/`
   - `geometry/`
   - `nucdata/`
   - `safety/`
   - `validation/`
   - `uncertainty/`
   - `presets/`
   - `profiling/` (also removed)

**Result**: Package structure is now clean with `smrforge/` as the single authoritative source.

---

*Created: 2024-12-21*  
*Completed: 2024-12-21*

