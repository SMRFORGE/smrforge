# Data Import Improvement Summary

**Date:** January 2026  
**Quick Reference:** See [Full Comparison](data-import-comparison-and-improvement-plan.md) for detailed analysis

---

## Quick Comparison

| Feature | OpenMC | SMRForge | Status |
|---------|--------|----------|--------|
| **Pre-generated libraries** | ✅ | ❌ | 🔴 Gap |
| **Automated download** | ✅ | ❌ | 🔴 Gap |
| **Environment variables** | ✅ | ❌ | 🟡 Gap |
| **Selective download** | ✅ | ❌ | 🟡 Gap |
| **Raw ENDF support** | ⚠️ | ✅ | ✅ Advantage |
| **Offline capability** | ⚠️ | ✅ | ✅ Advantage |
| **Setup wizard** | ❌ | ✅ | ✅ Advantage |

---

## Critical Gaps in SMRForge

### 1. ❌ No Automated Download (🔴 CRITICAL)

**Current:** Users must manually visit NNDC/IAEA websites and download files  
**OpenMC:** `openmc_data_downloader` package downloads automatically  
**Impact:** High barrier to entry, error-prone

**Solution:** Create `smrforge_data_downloader` module

---

### 2. ❌ No Pre-Processed Libraries (🔴 CRITICAL)

**Current:** Must parse raw ENDF files on first use  
**OpenMC:** Pre-generated HDF5 libraries ready to use  
**Impact:** Slower first-time access, requires parsing setup

**Solution:** Generate and host pre-processed Zarr libraries

---

### 3. ⚠️ No Environment Variable Support (🟡 MEDIUM)

**Current:** Must specify directory in code  
**OpenMC:** `OPENMC_CROSS_SECTIONS` environment variable  
**Impact:** Less convenient for global configuration

**Solution:** Add `SMRFORGE_ENDF_DIR` environment variable support

---

## Implementation Plan

### Phase 1: Automated Download (Weeks 1-6) 🔴 **HIGH PRIORITY**

**Create:** `smrforge/data_downloader.py`

**Features:**
- Download ENDF files from NNDC/IAEA programmatically
- Selective downloads (by element, isotope, library)
- Progress indicators
- Resume capability
- Automatic validation

**API:**
```python
from smrforge.data_downloader import download_endf_data

# Download full library
download_endf_data(library="ENDF/B-VIII.1", output_dir="~/ENDF-Data")

# Download specific elements
download_endf_data(
    library="ENDF/B-VIII.1",
    elements=["U", "Pu", "Th"],
    output_dir="~/ENDF-Data"
)
```

**Estimated Effort:** 2-3 weeks  
**Impact:** ⬆️⬆️⬆️ Setup time: 30-60 min → 5-10 min

---

### Phase 2: Pre-Processed Libraries (Weeks 7-12) 🔴 **HIGH PRIORITY**

**Create:** Pre-processed Zarr libraries for common SMR nuclides

**Features:**
- Pre-parsed cross-sections
- Common temperature points (300K, 600K, 900K, 1200K)
- Fast lookup indices
- Hosted on GitHub Releases + Zenodo

**API:**
```python
from smrforge.data_downloader import download_preprocessed_library

download_preprocessed_library(
    library="ENDF/B-VIII.1",
    nuclides="common_smr",  # Pre-selected set
    output_dir="~/ENDF-Data"
)
```

**Estimated Effort:** 2-3 weeks  
**Impact:** ⬆️⬆️⬆️⬆️ Setup time: 5-10 min → 1-2 min

---

### Phase 3: UX Improvements (Weeks 13-16) 🟡 **MEDIUM PRIORITY**

**Features:**
- Environment variable support (`SMRFORGE_ENDF_DIR`)
- Configuration file support (`~/.smrforge/config.yaml`)
- Improved error messages
- Progress indicators

**Estimated Effort:** 1-2 weeks  
**Impact:** ⬆️⬆️ Better user experience

---

## Expected Outcomes

### Before Improvements
- **Setup Time:** 30-60 minutes
- **Error Rate:** ~20%
- **User Satisfaction:** Medium

### After Phase 1 (Automated Download)
- **Setup Time:** 5-10 minutes
- **Error Rate:** ~5%
- **User Satisfaction:** High

### After Phase 2 (Pre-Processed Libraries)
- **Setup Time:** 1-2 minutes
- **Error Rate:** ~1%
- **User Satisfaction:** Very High

---

## Implementation Status

### ✅ Phase 1: Automated Download Tool (COMPLETE)

**Implemented:**
- ✅ `smrforge/data_downloader.py` module created
- ✅ Download from NNDC/IAEA programmatically
- ✅ Selective downloads (by element, isotope, nuclide_set)
- ✅ Progress indicators with `tqdm`
- ✅ Resume capability
- ✅ Automatic validation
- ✅ Automatic organization into standard structure
- ✅ Integration with `NuclearDataCache`

**Files Created:**
- `smrforge/data_downloader.py` - Main downloader module
- `examples/data_downloader_example.py` - Usage examples
- `docs/guides/data-downloader-guide.md` - Complete guide

**API:**
```python
from smrforge.data_downloader import download_endf_data

# Download specific isotopes
download_endf_data(
    library="ENDF/B-VIII.1",
    isotopes=["U235", "U238", "Pu239"],
    output_dir="~/ENDF-Data"
)
```

### ✅ Phase 3: UX Improvements (COMPLETE)

**Implemented:**
- ✅ Environment variable support (`SMRFORGE_ENDF_DIR`)
- ✅ Configuration file support (`~/.smrforge/config.yaml`)
- ✅ Improved error messages in `NuclearDataCache`

**Files Modified:**
- `smrforge/core/reactor_core.py` - Added env var and config support
- `requirements.txt` - Added `tqdm` and `pyyaml`

### ⏳ Phase 2: Pre-Processed Libraries (PENDING)

**Status:** Not yet implemented (placeholder function exists)

**Next Steps:**
- Create library generator
- Generate common SMR nuclide library
- Host on GitHub Releases
- Add download function for pre-processed libraries

---

## Next Steps

1. ✅ **Phase 1 Complete** - Automated download tool implemented
2. ✅ **Phase 3 Complete** - Environment variables and config file support
3. ⏳ **Phase 2 Pending** - Pre-processed libraries (future work)
4. ✅ **Documentation Updated** - Complete guide available

---

**See:** [Full Comparison Document](data-import-comparison-and-improvement-plan.md) for detailed analysis, code examples, and technical specifications.
