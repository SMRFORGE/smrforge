# ENDF-B-VIII.1 Local Data Integration Plan

## Overview
Integrate local ENDF-B-VIII.1 nuclear data files from `C:\Users\cmwha\Downloads\ENDF-B-VIII.1` into SMRForge's NuclearDataCache system.

## Current State Analysis

### File Structure
- **Location**: `C:\Users\cmwha\Downloads\ENDF-B-VIII.1`
- **Sublibraries**: 
  - `neutrons-version.VIII.1/` (558 files) - **Primary focus**
  - `protons-version.VIII.1/`
  - `alphas-version.VIII.1/`
  - `deuterons-version.VIII.1/`
  - `tritons-version.VIII.1/`
  - `helium3s-version.VIII.1/`
  - `electrons-version.VIII.1/`
  - `photoat-version.VIII.1/`
  - `atomic_relax-version.VIII.1/`
  - `decay-version.VIII.1/`
  - `gammas-version.VIII.1/`
  - `nfy-version.VIII.1/`
  - `sfy-version.VIII.1/`
  - `thermal_scatt-version.VIII.1/`
  - `standards-version.VIII.1/`

### File Naming Convention
- Format: `n-ZZZ_Element_AAA.endf` (for neutrons)
  - Example: `n-092_U_235.endf` → U-235
  - Example: `n-001_H_001.endf` → H-1
  - Example: `n-013_Al_026m1.endf` → Al-26m1 (metastable)

### Current System Expectations
- Nuclide class: `Nuclide(Z=92, A=235, m=0)` → `name = "U235"`
- Cache expects: `{cache_dir}/endf/{library}/{nuclide.name}.endf`
- Library enum: `Library.ENDF_B_VIII = "endfb8.0"` (but we have VIII.1)

## Integration Strategy

### 1. File Name Mapping
Create a function to map between:
- ENDF filename format: `n-092_U_235.endf`
- Nuclide name format: `U235`
- Handle metastable states: `n-013_Al_026m1.endf` → `Al26m1`

### 2. Local ENDF Directory Support
Add support for:
- **Local ENDF directory**: User-specified path to ENDF-B-VIII.1 root
- **Automatic discovery**: Scan local directory before attempting download
- **Symlink/copy strategy**: Use symlinks (Windows: junctions) for efficiency

### 3. Library Version Support
- Add `Library.ENDF_B_VIII_1 = "endfb8.1"` enum value
- Support both VIII.0 and VIII.1
- Prefer VIII.1 if available locally

### 4. Implementation Approach

#### Option A: Symlink/Junction Approach (Recommended)
- **Pros**: 
  - No disk space duplication
  - Fast (no copying)
  - Original files remain untouched
- **Cons**: 
  - Requires admin rights on Windows for junctions
  - Path dependencies

#### Option B: Direct File Access
- **Pros**:
  - No copying or symlinks needed
  - Works immediately
  - No admin rights required
- **Cons**:
  - Requires path resolution logic
  - Cache structure becomes more complex

#### Option C: Copy on First Use
- **Pros**:
  - Self-contained cache
  - No path dependencies
- **Cons**:
  - Disk space usage
  - Slower first access

**Recommendation**: **Option B (Direct File Access)** with fallback to Option A for efficiency.

### 5. Data Validation
- Verify ENDF file format (check header)
- Validate nuclide matches filename
- Check library version in file header
- Verify file integrity (size, format)

### 6. Performance Considerations
- **Indexing**: Build index of available files on first access
- **Caching**: Cache file paths to avoid repeated directory scans
- **Lazy loading**: Only scan when needed
- **Parallel processing**: Use async for multiple file operations

## Implementation Plan

### Phase 1: Core Integration
1. Add `local_endf_dir` parameter to `NuclearDataCache.__init__()`
2. Implement filename mapping functions:
   - `_endf_filename_to_nuclide()`: Parse `n-092_U_235.endf` → `Nuclide(Z=92, A=235, m=0)`
   - `_nuclide_to_endf_filename()`: Convert `Nuclide` → `n-092_U_235.endf`
3. Add `_find_local_endf_file()` method
4. Update `_ensure_endf_file()` to check local directory first

### Phase 2: Library Support
1. Add `Library.ENDF_B_VIII_1 = "endfb8.1"`
2. Support library version mapping (VIII.1 → endfb8.1)
3. Handle version fallback (VIII.1 → VIII.0)

### Phase 3: Optimization
1. Build file index on initialization
2. Cache file paths
3. Add validation checks

### Phase 4: User Experience
1. Add configuration option in settings
2. Provide helper script to set up local directory
3. Add documentation

## Code Structure

```python
class NuclearDataCache:
    def __init__(self, cache_dir=None, local_endf_dir=None):
        # ... existing code ...
        self.local_endf_dir = Path(local_endf_dir) if local_endf_dir else None
        self._local_file_index = None  # Lazy-loaded index
    
    def _build_local_file_index(self):
        """Build index of available local ENDF files."""
        # Scan local_endf_dir and create mapping
        
    def _find_local_endf_file(self, nuclide, library):
        """Find ENDF file in local directory."""
        # Check index, return path if found
        
    def _endf_filename_to_nuclide(self, filename):
        """Parse ENDF filename to Nuclide."""
        # Parse n-092_U_235.endf format
        
    def _nuclide_to_endf_filename(self, nuclide):
        """Convert Nuclide to ENDF filename format."""
        # Generate n-092_U_235.endf format
```

## Testing Strategy
1. Test filename parsing (various nuclides, metastable states)
2. Test file discovery (existing files, missing files)
3. Test library version handling
4. Test performance (indexing, caching)
5. Test validation (corrupt files, wrong format)

## Documentation Updates
1. Update `NUCLEAR_DATA_BACKENDS.md` with local directory instructions
2. Add example usage in README
3. Document configuration options

