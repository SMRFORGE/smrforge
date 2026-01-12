# Data Import Comparison: OpenMC vs SMRForge

**Date:** January 2026  
**Status:** Analysis and Improvement Plan

---

## Executive Summary

This document compares how users import nuclear data into OpenMC and SMRForge, identifies gaps and limitations in both approaches, and provides a comprehensive plan to improve SMRForge's data import user experience.

**Key Finding:** OpenMC provides a more streamlined, automated data import experience with pre-generated libraries and Python tools, while SMRForge requires manual setup but offers more flexibility for offline use and custom data sources.

---

## Comparison: OpenMC vs SMRForge

### OpenMC Data Import Mechanisms

#### 1. **Pre-Generated HDF5 Libraries** ✅ **STRENGTH**

**How it works:**
- OpenMC provides pre-generated HDF5 cross-section libraries on their website
- Users download and unpack the library
- Set `OPENMC_CROSS_SECTIONS` environment variable to point to `cross_sections.xml`
- OpenMC automatically discovers and uses all data files

**User Experience:**
```bash
# 1. Download library from openmc.org
# 2. Unpack to directory
# 3. Set environment variable
export OPENMC_CROSS_SECTIONS=/path/to/cross_sections.xml

# 4. Use in Python
import openmc
# Data is automatically available
```

**Advantages:**
- ✅ **Zero configuration** - Just download and set one environment variable
- ✅ **Pre-processed** - Data already in optimal format (HDF5)
- ✅ **Fast access** - HDF5 format is optimized for reading
- ✅ **Reproducible** - Same library version for all users
- ✅ **Well-documented** - Clear instructions on website

**Limitations:**
- ⚠️ **Large downloads** - Full libraries are 1-2 GB
- ⚠️ **Limited customization** - Must use pre-generated libraries
- ⚠️ **Version dependency** - Tied to OpenMC's processing pipeline
- ⚠️ **Network required** - Initial download needs internet

---

#### 2. **openmc_data_downloader Python Package** ✅ **STRENGTH**

**How it works:**
- Python package: `pip install openmc_data_downloader`
- Allows selective download of specific isotopes/elements
- Downloads pre-processed HDF5 data from OpenMC's servers
- Creates reproducible data libraries

**User Experience:**
```python
from openmc_data_downloader import download

# Download specific isotopes
download(
    libraries=['ENDF/B-8.0'],
    elements=['U', 'Pu'],
    output='nuclear_data'
)

# Or download full library
download(
    libraries=['ENDF/B-8.0'],
    output='nuclear_data'
)
```

**Advantages:**
- ✅ **Selective downloads** - Only download what you need
- ✅ **Python API** - Programmatic control
- ✅ **Reproducible** - Version-controlled downloads
- ✅ **Multiple libraries** - Supports ENDF/B, JEFF, JENDL
- ✅ **Automatic setup** - Creates proper directory structure

**Limitations:**
- ⚠️ **Requires internet** - All downloads need network access
- ⚠️ **Pre-processed only** - Cannot use raw ENDF files directly
- ⚠️ **OpenMC-specific format** - HDF5 format tied to OpenMC

---

#### 3. **Custom Library Generation** ✅ **FLEXIBILITY**

**How it works:**
- OpenMC provides Python API to convert ACE/ENDF files to HDF5
- Users can process their own data files
- Generate custom `cross_sections.xml` files

**User Experience:**
```python
import openmc.data

# Convert ACE file to HDF5
u235 = openmc.data.IncidentNeutron.from_ace('92235.710nc')
u235.export_to_hdf5('U235.h5')

# Generate cross_sections.xml
openmc.data.cross_sections = 'cross_sections.xml'
```

**Advantages:**
- ✅ **Full control** - Process any ACE/ENDF file
- ✅ **Custom data** - Use experimental or custom evaluations
- ✅ **Flexible** - Mix and match data sources

**Limitations:**
- ⚠️ **Complex** - Requires understanding of ACE/ENDF formats
- ⚠️ **Time-consuming** - Manual processing for each file
- ⚠️ **Technical knowledge** - Not beginner-friendly

---

### SMRForge Data Import Mechanisms

#### 1. **Manual ENDF File Setup** ⚠️ **LIMITATION**

**How it works:**
- Users must manually download ENDF files from NNDC/IAEA
- Extract files to a directory
- Point `NuclearDataCache` to the directory
- SMRForge discovers and uses files automatically

**User Experience:**
```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache

# Manual setup required
cache = NuclearDataCache(
    local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1")
)

# Then use
u235 = Nuclide(Z=92, A=235)
energy, xs = cache.get_cross_section(u235, "total")
```

**Advantages:**
- ✅ **Offline capable** - Works without internet after setup
- ✅ **Raw ENDF files** - Direct access to original data
- ✅ **Flexible** - Use any ENDF version or custom files
- ✅ **Fast local access** - Once set up, very fast
- ✅ **Multiple libraries** - Supports ENDF/B, JEFF, JENDL

**Limitations:**
- ❌ **Manual download** - Must visit websites and download manually
- ❌ **Large files** - Full libraries are 500 MB - 2 GB
- ❌ **No automation** - No Python tool to download files
- ❌ **Setup complexity** - Multiple steps required
- ❌ **Error-prone** - Easy to misconfigure

---

#### 2. **Interactive Setup Wizard** ✅ **STRENGTH**

**How it works:**
- Run `python -m smrforge.core.endf_setup`
- Step-by-step wizard guides users
- Scans and validates files
- Organizes files into standard structure

**User Experience:**
```bash
python -m smrforge.core.endf_setup

# Wizard guides through:
# 1. Choose setup option (existing files or download instructions)
# 2. Locate ENDF files
# 3. Scan and validate
# 4. Organize files (optional)
# 5. Final validation
```

**Advantages:**
- ✅ **User-friendly** - Guided step-by-step process
- ✅ **Validation** - Checks files before use
- ✅ **Organization** - Can organize files automatically
- ✅ **Error messages** - Helpful feedback

**Limitations:**
- ⚠️ **Still manual** - Wizard doesn't download files
- ⚠️ **CLI only** - No GUI or web interface
- ⚠️ **One-time setup** - Must be run manually

---

#### 3. **Bulk File Organization** ✅ **STRENGTH**

**How it works:**
- `organize_bulk_endf_downloads()` function
- Scans directory for ENDF files
- Organizes into standard structure
- Creates index for fast lookup

**User Experience:**
```python
from smrforge.core.reactor_core import organize_bulk_endf_downloads

stats = organize_bulk_endf_downloads(
    source_dir=Path("C:/Downloads/ENDF-B-VIII.1"),
    library_version="VIII.1"
)
```

**Advantages:**
- ✅ **Flexible input** - Works with any directory structure
- ✅ **Automatic organization** - Creates standard structure
- ✅ **Validation** - Checks files during organization
- ✅ **Indexing** - Creates fast lookup index

**Limitations:**
- ⚠️ **Post-download** - Only works after files are downloaded
- ⚠️ **No download** - Doesn't download files itself

---

## Gap Analysis

### OpenMC Gaps and Limitations

#### 1. **Pre-Processed Format Dependency** ⚠️
- **Issue:** Must use HDF5 format, cannot use raw ENDF files directly
- **Impact:** Less flexible for users who want raw ENDF access
- **Workaround:** Can convert ENDF → ACE → HDF5, but complex

#### 2. **Environment Variable Configuration** ⚠️
- **Issue:** Requires setting environment variable
- **Impact:** Can be forgotten, not Python-native
- **Workaround:** Can set in Python, but not default

#### 3. **Limited Offline Support** ⚠️
- **Issue:** Initial setup requires internet for downloads
- **Impact:** Difficult in air-gapped environments
- **Workaround:** Can transfer pre-downloaded libraries

#### 4. **Library Version Tied to OpenMC** ⚠️
- **Issue:** HDF5 libraries are OpenMC-specific
- **Impact:** Cannot easily switch between tools
- **Workaround:** Must regenerate libraries for other tools

---

### SMRForge Gaps and Limitations

#### 1. **No Automated Download** ❌ **CRITICAL GAP**
- **Issue:** Must manually download from websites
- **Impact:** High barrier to entry, error-prone
- **Comparison:** OpenMC has `openmc_data_downloader`
- **Priority:** 🔴 **HIGH**

#### 2. **No Pre-Processed Libraries** ❌ **CRITICAL GAP**
- **Issue:** Must process raw ENDF files
- **Impact:** Slower first-time access, requires parsing
- **Comparison:** OpenMC provides ready-to-use HDF5 libraries
- **Priority:** 🔴 **HIGH**

#### 3. **No Environment Variable Support** ⚠️ **MEDIUM GAP**
- **Issue:** Must specify directory in code
- **Impact:** Less convenient for global configuration
- **Comparison:** OpenMC uses `OPENMC_CROSS_SECTIONS` env var
- **Priority:** 🟡 **MEDIUM**

#### 4. **No Selective Download** ⚠️ **MEDIUM GAP**
- **Issue:** Must download entire library
- **Impact:** Large downloads even if only need few nuclides
- **Comparison:** OpenMC allows element/isotope selection
- **Priority:** 🟡 **MEDIUM**

#### 5. **No Progress Indicators** ⚠️ **LOW GAP**
- **Issue:** No feedback during file operations
- **Impact:** Users don't know if process is working
- **Comparison:** OpenMC downloader shows progress
- **Priority:** 🟢 **LOW**

#### 6. **Limited Error Recovery** ⚠️ **LOW GAP**
- **Issue:** Errors can leave setup in inconsistent state
- **Impact:** Difficult to recover from failures
- **Comparison:** OpenMC has better error handling
- **Priority:** 🟢 **LOW**

---

## Improvement Plan for SMRForge

### Phase 1: Automated Download Tool (High Priority) 🔴

**Goal:** Create Python package similar to `openmc_data_downloader` for SMRForge

#### 1.1 Create `smrforge_data_downloader` Package

**Features:**
- Download ENDF files from NNDC/IAEA programmatically
- Support selective downloads (by element, isotope, or library)
- Progress indicators and resume capability
- Automatic validation after download
- Integration with SMRForge's cache system

**API Design:**
```python
from smrforge_data_downloader import download_endf_data

# Download full library
download_endf_data(
    library="ENDF/B-VIII.1",
    output_dir="~/ENDF-Data",
    show_progress=True
)

# Download specific elements
download_endf_data(
    library="ENDF/B-VIII.1",
    elements=["U", "Pu", "Th"],
    output_dir="~/ENDF-Data"
)

# Download specific isotopes
download_endf_data(
    library="ENDF/B-VIII.1",
    isotopes=["U235", "U238", "Pu239"],
    output_dir="~/ENDF-Data"
)

# Resume interrupted download
download_endf_data(
    library="ENDF/B-VIII.1",
    output_dir="~/ENDF-Data",
    resume=True
)
```

**Implementation:**
- **File:** `smrforge/data_downloader.py` (new module)
- **Dependencies:** `requests`, `tqdm` (for progress bars)
- **Features:**
  - Multi-threaded downloads
  - Checksum validation
  - Automatic retry on failure
  - Resume capability
  - Integration with `organize_bulk_endf_downloads()`

**Estimated Effort:** 2-3 weeks  
**Priority:** 🔴 **HIGH**

---

#### 1.2 Add Environment Variable Support

**Goal:** Support `SMRFORGE_ENDF_DIR` environment variable

**Implementation:**
```python
# In NuclearDataCache.__init__
import os

def __init__(self, cache_dir: Optional[Path] = None, 
             local_endf_dir: Optional[Path] = None):
    # Check environment variable if local_endf_dir not provided
    if local_endf_dir is None:
        env_dir = os.getenv("SMRFORGE_ENDF_DIR")
        if env_dir:
            local_endf_dir = Path(env_dir).expanduser().resolve()
    
    # ... rest of initialization
```

**Usage:**
```bash
# Set environment variable
export SMRFORGE_ENDF_DIR=~/ENDF-Data

# Or in Python
import os
os.environ["SMRFORGE_ENDF_DIR"] = "~/ENDF-Data"

# Now works without specifying directory
cache = NuclearDataCache()  # Automatically uses env var
```

**Estimated Effort:** 1-2 days  
**Priority:** 🟡 **MEDIUM**

---

### Phase 2: Pre-Processed Data Libraries (High Priority) 🔴

**Goal:** Create pre-processed Zarr cache libraries for common use cases

#### 2.1 Create Pre-Processed Library Generator

**Features:**
- Process ENDF files into optimized Zarr format
- Include common nuclides for SMR analysis
- Create library metadata and index
- Support multiple library versions

**Implementation:**
```python
# New module: smrforge/core/library_generator.py
def generate_preprocessed_library(
    source_endf_dir: Path,
    output_dir: Path,
    nuclides: Optional[List[Nuclide]] = None,
    library_version: str = "VIII.1"
) -> Dict[str, Any]:
    """
    Generate pre-processed Zarr library from ENDF files.
    
    Creates optimized cache with:
    - Pre-parsed cross-sections
    - Common temperature points
    - Fast lookup indices
    - Metadata and validation
    """
    pass
```

**Estimated Effort:** 2-3 weeks  
**Priority:** 🔴 **HIGH**

---

#### 2.2 Host Pre-Processed Libraries

**Options:**
1. **GitHub Releases** - Host on SMRForge GitHub releases
2. **Zenodo** - Long-term archival and DOI assignment
3. **Cloud Storage** - AWS S3, Google Cloud Storage (with CDN)
4. **PyPI Data Package** - Separate package for data

**Recommended:** Combination of GitHub Releases (easy access) + Zenodo (archival)

**Library Contents:**
- Common SMR nuclides (U-235, U-238, Pu-239, Th-232, etc.)
- Common temperatures (300K, 600K, 900K, 1200K)
- Standard reactions (total, elastic, fission, capture)
- Metadata and validation checksums

**Estimated Effort:** 1 week (setup) + ongoing maintenance  
**Priority:** 🔴 **HIGH**

---

#### 2.3 Add Library Download Function

**Implementation:**
```python
from smrforge.data_downloader import download_preprocessed_library

# Download pre-processed library
download_preprocessed_library(
    library="ENDF/B-VIII.1",
    nuclides="common_smr",  # or list of specific nuclides
    output_dir="~/ENDF-Data",
    use_cache=True  # Use Zarr cache instead of raw ENDF
)
```

**Estimated Effort:** 1 week  
**Priority:** 🔴 **HIGH**

---

### Phase 3: Enhanced User Experience (Medium Priority) 🟡

#### 3.1 Add Progress Indicators

**Implementation:**
- Use `tqdm` for download progress
- Show parsing progress for ENDF files
- Display cache operations progress

**Estimated Effort:** 2-3 days  
**Priority:** 🟡 **MEDIUM**

---

#### 3.2 Improve Error Messages

**Current:** Generic error messages  
**Improved:** Context-specific, actionable error messages

**Example:**
```python
# Current
FileNotFoundError: ENDF file not found

# Improved
FileNotFoundError: ENDF file not found for U235 (ENDF/B-VIII.1)

Suggested actions:
1. Run: python -m smrforge.core.endf_setup
2. Or download: smrforge-data-downloader --library ENDF/B-VIII.1 --isotopes U235
3. Or set: export SMRFORGE_ENDF_DIR=/path/to/endf/files
```

**Estimated Effort:** 3-5 days  
**Priority:** 🟡 **MEDIUM**

---

#### 3.3 Add Configuration File Support

**Goal:** Support configuration file for default settings

**Implementation:**
```python
# ~/.smrforge/config.yaml
endf:
  default_library: "ENDF/B-VIII.1"
  default_directory: "~/ENDF-Data"
  auto_download: true
  cache_dir: "~/.smrforge/cache"

# In code
cache = NuclearDataCache()  # Reads from config file
```

**Estimated Effort:** 1 week  
**Priority:** 🟡 **MEDIUM**

---

#### 3.4 Add Data Validation Dashboard

**Goal:** Visual tool to check data availability and quality

**Implementation:**
```python
from smrforge.data_tools import validate_data_setup

report = validate_data_setup()
# Returns:
# - Available nuclides
# - Missing nuclides
# - Data quality metrics
# - Recommendations
```

**Estimated Effort:** 1 week  
**Priority:** 🟢 **LOW**

---

### Phase 4: Advanced Features (Low Priority) 🟢

#### 4.1 Multi-Library Support

**Goal:** Seamlessly use multiple libraries (ENDF/B, JEFF, JENDL)

**Implementation:**
```python
cache = NuclearDataCache(
    libraries={
        "primary": Library.ENDF_B_VIII_1,
        "fallback": Library.JEFF_33
    }
)
```

**Estimated Effort:** 1-2 weeks  
**Priority:** 🟢 **LOW**

---

#### 4.2 Data Update Notifications

**Goal:** Notify users when new library versions are available

**Implementation:**
- Check for updates on startup (optional)
- Show notification if newer version available
- Provide upgrade instructions

**Estimated Effort:** 3-5 days  
**Priority:** 🟢 **LOW**

---

#### 4.3 Cloud Cache Support

**Goal:** Optional cloud-based cache for faster access

**Implementation:**
- Support S3-compatible storage
- Automatic sync for common nuclides
- Offline-first with cloud backup

**Estimated Effort:** 2-3 weeks  
**Priority:** 🟢 **LOW**

---

## Implementation Roadmap

### Short-Term (1-2 months)

**Priority 1: Automated Download Tool**
- ✅ Create `smrforge_data_downloader` module
- ✅ Add download functions for NNDC/IAEA
- ✅ Support selective downloads
- ✅ Add progress indicators
- ✅ Integrate with existing setup wizard

**Priority 2: Environment Variable Support**
- ✅ Add `SMRFORGE_ENDF_DIR` support
- ✅ Update documentation
- ✅ Add to setup wizard

**Expected Impact:**
- **User Experience:** ⬆️⬆️⬆️ (Significant improvement)
- **Barrier to Entry:** ⬇️⬇️⬇️ (Much lower)
- **Coverage Gain:** +0.5-1.0% (from better error handling)

---

### Medium-Term (3-4 months)

**Priority 3: Pre-Processed Libraries**
- ✅ Create library generator
- ✅ Host pre-processed libraries
- ✅ Add download function
- ✅ Create common SMR nuclide sets

**Priority 4: Enhanced UX**
- ✅ Improve error messages
- ✅ Add configuration file support
- ✅ Add validation dashboard

**Expected Impact:**
- **User Experience:** ⬆️⬆️⬆️⬆️ (Excellent)
- **Performance:** ⬆️⬆️ (Faster first-time access)
- **Adoption:** ⬆️⬆️⬆️ (Easier for new users)

---

### Long-Term (6+ months)

**Priority 5: Advanced Features**
- Multi-library support
- Data update notifications
- Cloud cache support

**Expected Impact:**
- **User Experience:** ⬆️⬆️⬆️⬆️⬆️ (Best-in-class)
- **Flexibility:** ⬆️⬆️⬆️ (More options)
- **Enterprise Ready:** ✅ (Production-grade)

---

## Comparison Matrix

| Feature | OpenMC | SMRForge | Gap | Priority |
|---------|--------|----------|-----|----------|
| **Pre-generated libraries** | ✅ Yes | ❌ No | 🔴 Critical | High |
| **Automated download** | ✅ Yes | ❌ No | 🔴 Critical | High |
| **Environment variables** | ✅ Yes | ❌ No | 🟡 Medium | Medium |
| **Selective download** | ✅ Yes | ❌ No | 🟡 Medium | Medium |
| **Raw ENDF support** | ⚠️ Limited | ✅ Yes | ✅ Advantage | - |
| **Offline capability** | ⚠️ Limited | ✅ Yes | ✅ Advantage | - |
| **Setup wizard** | ❌ No | ✅ Yes | ✅ Advantage | - |
| **Progress indicators** | ✅ Yes | ❌ No | 🟢 Low | Low |
| **Configuration files** | ⚠️ Limited | ❌ No | 🟡 Medium | Medium |
| **Multi-library support** | ✅ Yes | ⚠️ Partial | 🟢 Low | Low |

---

## Recommended Implementation Order

### Week 1-2: Quick Wins
1. ✅ Add environment variable support (`SMRFORGE_ENDF_DIR`)
2. ✅ Improve error messages with actionable suggestions
3. ✅ Add progress indicators to existing operations

### Week 3-6: High-Impact Features
4. ✅ Create `smrforge_data_downloader` module
5. ✅ Implement automated download from NNDC/IAEA
6. ✅ Add selective download (by element/isotope)
7. ✅ Integrate with setup wizard

### Month 2-3: Pre-Processed Libraries
8. ✅ Create library generator
9. ✅ Generate common SMR nuclide library
10. ✅ Host on GitHub Releases
11. ✅ Add download function for pre-processed libraries

### Month 4+: Polish
12. ✅ Add configuration file support
13. ✅ Create validation dashboard
14. ✅ Multi-library support
15. ✅ Documentation updates

---

## Success Metrics

### User Experience Metrics

**Before Improvements:**
- Setup time: 30-60 minutes (manual download + setup)
- Error rate: ~20% (common configuration mistakes)
- User satisfaction: Medium (frustrating for beginners)

**After Phase 1 (Automated Download):**
- Setup time: 5-10 minutes (automated download)
- Error rate: ~5% (better error handling)
- User satisfaction: High (much easier)

**After Phase 2 (Pre-Processed Libraries):**
- Setup time: 1-2 minutes (download pre-processed)
- Error rate: ~1% (validated libraries)
- User satisfaction: Very High (excellent UX)

---

## Code Examples: Improved User Experience

### Example 1: Automated Download (After Phase 1)

```python
from smrforge.data_downloader import download_endf_data
from smrforge.core.reactor_core import NuclearDataCache, Nuclide

# One-line setup - downloads and configures automatically
download_endf_data(
    library="ENDF/B-VIII.1",
    elements=["U", "Pu", "Th"],  # Only download what's needed
    output_dir="~/ENDF-Data"
)

# Use immediately
cache = NuclearDataCache()  # Uses SMRFORGE_ENDF_DIR or default
u235 = Nuclide(Z=92, A=235)
energy, xs = cache.get_cross_section(u235, "total")
```

### Example 2: Pre-Processed Library (After Phase 2)

```python
from smrforge.data_downloader import download_preprocessed_library
from smrforge.core.reactor_core import NuclearDataCache

# Download optimized pre-processed library
download_preprocessed_library(
    library="ENDF/B-VIII.1",
    nuclides="common_smr",  # Pre-selected common SMR nuclides
    output_dir="~/ENDF-Data"
)

# Instant access - no parsing needed
cache = NuclearDataCache()
# Data is already in optimized Zarr format
```

### Example 3: Environment Variable (After Phase 1)

```bash
# Set once, use everywhere
export SMRFORGE_ENDF_DIR=~/ENDF-Data

# In any Python script
from smrforge.core.reactor_core import NuclearDataCache
cache = NuclearDataCache()  # Automatically uses env var
```

### Example 4: Configuration File (After Phase 3)

```yaml
# ~/.smrforge/config.yaml
endf:
  default_library: "ENDF/B-VIII.1"
  default_directory: "~/ENDF-Data"
  auto_download: true
  cache_dir: "~/.smrforge/cache"
```

```python
# In code - reads from config automatically
cache = NuclearDataCache()  # Uses config file settings
```

---

## Technical Considerations

### Download Implementation Details

**NNDC/IAEA URLs:**
- NNDC: `https://www.nndc.bnl.gov/endf/b8.1/`
- IAEA: `https://www-nds.iaea.org/exfor/endf/`

**File Naming:**
- Standard: `n-ZZZ_Element_AAA.endf` (e.g., `n-092_U_235.endf`)
- Alternative formats to handle

**Download Strategy:**
- Multi-threaded downloads (5-10 concurrent)
- Resume capability (check existing files)
- Checksum validation (MD5/SHA256)
- Progress bars with `tqdm`

### Pre-Processed Library Format

**Zarr Structure:**
```
library/
  metadata.json
  nuclides/
    U235/
      reactions/
        total/
          energy.zarr
          xs_300K.zarr
          xs_600K.zarr
          ...
        fission/
          ...
```

**Metadata:**
- Library version
- Nuclide list
- Temperature points
- Reactions available
- Checksums
- Creation date

---

## Risk Assessment

### Technical Risks

1. **Network Reliability** ⚠️
   - **Risk:** Downloads may fail or be slow
   - **Mitigation:** Resume capability, multiple mirrors, retry logic

2. **File Format Changes** ⚠️
   - **Risk:** NNDC/IAEA may change file formats
   - **Mitigation:** Version detection, flexible parsing

3. **Storage Requirements** ⚠️
   - **Risk:** Pre-processed libraries may be large
   - **Mitigation:** Selective downloads, compression

### User Experience Risks

1. **Complexity** ⚠️
   - **Risk:** Too many options may confuse users
   - **Mitigation:** Sensible defaults, clear documentation

2. **Backward Compatibility** ⚠️
   - **Risk:** Changes may break existing setups
   - **Mitigation:** Maintain old API, deprecation warnings

---

## Conclusion

SMRForge currently requires manual data setup, which creates a significant barrier to entry. By implementing automated download tools and pre-processed libraries (similar to OpenMC), SMRForge can provide a much better user experience while maintaining its advantages (raw ENDF support, offline capability, flexibility).

**Recommended Priority:**
1. 🔴 **HIGH:** Automated download tool (Phase 1)
2. 🔴 **HIGH:** Pre-processed libraries (Phase 2)
3. 🟡 **MEDIUM:** Environment variables and UX improvements (Phase 3)
4. 🟢 **LOW:** Advanced features (Phase 4)

**Expected Outcome:**
- Setup time: 30-60 min → 1-2 min (30x improvement)
- User satisfaction: Medium → Very High
- Adoption rate: Significant increase
- Competitive parity: Match or exceed OpenMC's ease of use

---

**See Also:**
- [ENDF Documentation](technical/endf-documentation.md) - Current setup guide
- [Nuclear Data Backends](technical/nuclear-data-backends.md) - Backend options
- [Coverage Completion Plan](coverage-completion-plan.md) - Testing improvements
