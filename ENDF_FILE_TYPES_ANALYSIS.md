# ENDF-B-VIII.1 File Types Analysis

**Date:** January 2025  
**Directory:** `C:\Users\cmwha\Downloads\ENDF-B-VIII.1`  
**Purpose:** Analyze available ENDF file types and identify gaps in SMRForge capabilities

---

## Executive Summary

The ENDF-B-VIII.1 bulk download contains **15 different data types** organized into subdirectories. SMRForge currently supports **only neutron cross-section data** (`neutrons-version.VIII.1`). This analysis identifies:

1. **Currently Supported:** Neutron cross-sections (fully functional)
2. **Partially Supported:** Decay data (mentioned in code but not implemented)
3. **Not Supported:** 13 other data types with varying relevance to reactor physics

---

## File Type Inventory

### ✅ 1. Neutrons (`neutrons-version.VIII.1`) - **FULLY SUPPORTED**

**Status:** ✅ **Currently Supported**  
**Files:** ~500+ `.endf` files (e.g., `n-092_U_235.endf`)  
**Current Usage:**
- ✅ File discovery and indexing
- ✅ Cross-section parsing (SANDY + built-in parser)
- ✅ Multi-group cross-section generation
- ✅ Temperature-dependent data (Doppler broadening)
- ✅ Caching system (Zarr + memory cache)

**Relevance:** **CRITICAL** - Core functionality for neutronics calculations

**Gap Analysis:** None - fully functional

---

### ⚠️ 2. Thermal Scattering (`thermal_scatt-version.VIII.1`) - **NOT SUPPORTED**

**Status:** ❌ **Not Supported**  
**Files:** ~150+ files with naming pattern `tsl-*.endf` (e.g., `tsl-HinH2O.endf`, `tsl-OinUO2.endf`)  
**Also includes:** `.leapr` files (LEAPR format), `.readme` files

**What it contains:**
- Thermal neutron scattering laws (S(α,β)) for bound atoms in materials
- Material-specific data for:
  - **Water (H2O)** - Critical for light water reactors
  - **Heavy water (D2O)** - For heavy water reactors
  - **Graphite** - For graphite-moderated reactors
  - **UO2, UC, UN** - Fuel materials at various enrichments
  - **Be, BeO, ZrH** - Moderator and structural materials
  - **Organic moderators** (benzene, methane, etc.)

**Relevance:** **HIGH** - Essential for accurate thermal reactor calculations

**Current Gap:**
- ❌ No thermal scattering law parser
- ❌ No S(α,β) data handling
- ❌ No integration with neutronics solver
- ❌ Thermal scattering effects approximated or ignored

**Impact:** Thermal flux calculations in moderator materials may be inaccurate, especially for:
- Light water reactors (H2O moderation)
- Graphite-moderated reactors
- Heavy water reactors (D2O)

**Recommendation:** **HIGH PRIORITY** - Implement thermal scattering support for accurate thermal reactor modeling

---

### ⚠️ 3. Decay Data (`decay-version.VIII.1`) - **PARTIALLY SUPPORTED**

**Status:** ⚠️ **Partially Supported** (mentioned in code, not implemented)  
**Files:** ~3000+ files with naming pattern `dec-*.endf` (e.g., `dec-092_U_235.endf`)

**What it contains:**
- Radioactive decay constants (half-lives)
- Decay modes (α, β⁻, β⁺, EC, IT, SF)
- Decay product yields
- Gamma-ray emission spectra
- Beta spectra
- Neutrino spectra

**Relevance:** **MEDIUM-HIGH** - Important for:
- Fuel burnup calculations
- Decay heat calculations
- Radioactivity inventory
- Shielding design

**Current Gap:**
- ⚠️ `DecayData` class mentioned in `reactor_core.py` docstring but not implemented
- ❌ No decay data parser
- ❌ No integration with burnup calculations
- ❌ No decay heat calculations

**Impact:** Cannot perform:
- Fuel depletion/burnup analysis
- Post-shutdown decay heat calculations
- Radioactivity inventory tracking

**Recommendation:** **MEDIUM PRIORITY** - Implement decay data support for burnup and decay heat calculations

---

### ❌ 4. Photon Atomic Data (`photoat-version.VIII.1`) - **NOT SUPPORTED**

**Status:** ❌ **Not Supported**  
**Files:** ~100+ files with naming pattern `p-*.endf`

**What it contains:**
- Photon interaction cross-sections (photoelectric, Compton, pair production)
- Atomic form factors
- Scattering functions

**Relevance:** **LOW-MEDIUM** - Important for:
- Gamma-ray transport (shielding)
- Decay heat transport
- Radiation damage calculations

**Current Gap:**
- ❌ No photon transport solver
- ❌ No gamma-ray cross-section handling

**Impact:** Cannot perform gamma-ray shielding or transport calculations

**Recommendation:** **LOW PRIORITY** - Only needed if gamma transport is required

---

### ❌ 5. Gamma Production (`gammas-version.VIII.1`) - **NOT SUPPORTED**

**Status:** ❌ **Not Supported**  
**Files:** Files with naming pattern related to gamma production

**What it contains:**
- Gamma-ray production cross-sections
- Gamma-ray spectra from neutron interactions
- Prompt and delayed gamma data

**Relevance:** **LOW-MEDIUM** - Important for:
- Shielding calculations
- Decay heat (delayed gammas)
- Radiation damage

**Current Gap:**
- ❌ No gamma production data handling
- ❌ No delayed gamma calculations

**Recommendation:** **LOW PRIORITY** - Only needed for shielding/radiation analysis

---

### ❌ 6. Neutron Fission Yields (`nfy-version.VIII.1`) - **NOT SUPPORTED**

**Status:** ❌ **Not Supported**  
**Files:** Fission yield data files

**What it contains:**
- Independent and cumulative fission product yields
- Energy-dependent yields
- Chain yields for burnup calculations

**Relevance:** **HIGH** - Critical for:
- Fuel burnup/depletion calculations
- Fission product inventory
- Decay heat calculations

**Current Gap:**
- ❌ No fission yield data handling
- ❌ Cannot perform burnup calculations
- ❌ Cannot track fission product buildup

**Impact:** Cannot perform fuel depletion analysis

**Recommendation:** **HIGH PRIORITY** - Essential for burnup calculations

---

### ❌ 7. Spontaneous Fission Yields (`sfy-version.VIII.1`) - **NOT SUPPORTED**

**Status:** ❌ **Not Supported**  
**Files:** Spontaneous fission yield data

**What it contains:**
- Spontaneous fission product yields
- Spontaneous fission rates

**Relevance:** **LOW** - Only relevant for:
- Very heavy nuclides (Cf, Es, etc.)
- Specialized applications

**Recommendation:** **LOW PRIORITY** - Not critical for most reactor applications

---

### ❌ 8. Atomic Relaxation (`atomic_relax-version.VIII.1`) - **NOT SUPPORTED**

**Status:** ❌ **Not Supported**  
**Files:** Atomic relaxation data

**What it contains:**
- Electron transition probabilities
- X-ray emission data
- Auger electron data

**Relevance:** **LOW** - Specialized applications only

**Recommendation:** **LOW PRIORITY** - Not needed for reactor physics

---

### ❌ 9-13. Charged Particle Data - **NOT SUPPORTED**

**Status:** ❌ **Not Supported**  
**File Types:**
- `protons-version.VIII.1` - Proton cross-sections
- `deuterons-version.VIII.1` - Deuteron cross-sections
- `tritons-version.VIII.1` - Triton cross-sections
- `helium3s-version.VIII.1` - Helium-3 cross-sections
- `alphas-version.VIII.1` - Alpha particle cross-sections

**Relevance:** **LOW** - Only relevant for:
- Fusion reactor applications
- Accelerator-driven systems
- Specialized research

**Recommendation:** **LOW PRIORITY** - Not needed for thermal reactor physics

---

### ❌ 14. Electrons (`electrons-version.VIII.1`) - **NOT SUPPORTED**

**Status:** ❌ **Not Supported**  
**Files:** Electron interaction data

**Relevance:** **LOW** - Specialized applications only

**Recommendation:** **LOW PRIORITY** - Not needed for reactor physics

---

### ❌ 15. Standards (`standards-version.VIII.1`) - **NOT SUPPORTED**

**Status:** ❌ **Not Supported**  
**Files:** Standard cross-section reference data

**Relevance:** **LOW-MEDIUM** - Used for validation and benchmarking

**Recommendation:** **LOW PRIORITY** - Could be useful for validation but not critical

---

## Priority Recommendations

### 🔴 HIGH PRIORITY (Critical for Core Functionality)

1. **Thermal Scattering Laws** (`thermal_scatt-version.VIII.1`)
   - **Why:** Essential for accurate thermal reactor calculations
   - **Impact:** Improves accuracy of k-eff and flux distributions in thermal reactors
   - **Effort:** Medium-High (requires S(α,β) parser and integration)

2. **Neutron Fission Yields** (`nfy-version.VIII.1`)
   - **Why:** Required for fuel burnup/depletion calculations
   - **Impact:** Enables burnup analysis (currently impossible)
   - **Effort:** Medium (requires yield data parser and burnup solver)

### 🟡 MEDIUM PRIORITY (Important for Extended Functionality)

3. **Decay Data** (`decay-version.VIII.1`)
   - **Why:** Required for burnup and decay heat calculations
   - **Impact:** Enables decay heat and radioactivity inventory
   - **Effort:** Medium (parser exists conceptually, needs implementation)

### 🟢 LOW PRIORITY (Specialized Applications)

4. **Photon/Gamma Data** (`photoat`, `gammas`)
   - **Why:** Only needed for shielding/radiation transport
   - **Impact:** Enables gamma transport calculations
   - **Effort:** High (requires new transport solver)

5. **Charged Particle Data** (protons, deuterons, etc.)
   - **Why:** Only for fusion/accelerator applications
   - **Impact:** Not relevant for thermal reactors
   - **Effort:** High (specialized applications)

---

## Implementation Roadmap

### Phase 1: Thermal Scattering (High Priority)
- [ ] Implement thermal scattering law parser (S(α,β) data)
- [ ] Integrate with neutronics solver
- [ ] Add thermal scattering material definitions
- [ ] Test with H2O, D2O, graphite, UO2

### Phase 2: Fission Yields & Decay Data (High-Medium Priority)
- [ ] Implement fission yield parser
- [ ] Implement decay data parser
- [ ] Create burnup solver framework
- [ ] Integrate with neutronics for coupled burnup calculations

### Phase 3: Gamma Transport (Low Priority)
- [ ] Implement photon cross-section parser
- [ ] Create gamma transport solver
- [ ] Integrate with decay heat calculations

---

## Current Capabilities Summary

| Data Type | Status | Priority | Effort | Impact |
|-----------|--------|----------|--------|--------|
| Neutrons | ✅ Supported | - | - | Critical |
| Thermal Scattering | ❌ Not Supported | 🔴 High | Medium-High | High |
| Fission Yields | ❌ Not Supported | 🔴 High | Medium | High |
| Decay Data | ⚠️ Partial | 🟡 Medium | Medium | Medium-High |
| Photon/Gamma | ❌ Not Supported | 🟢 Low | High | Low-Medium |
| Charged Particles | ❌ Not Supported | 🟢 Low | High | Low |

---

## File Naming Patterns

### Currently Supported
- **Neutrons:** `n-ZZZ_Element_AAA.endf` (e.g., `n-092_U_235.endf`)
- **Pattern:** `^n-(\d+)_([A-Z][a-z]?)_(\d+)([mM]\d?)?\.endf$`

### Not Yet Supported
- **Thermal Scattering:** `tsl-*.endf` (material-based, not nuclide-based)
- **Decay:** `dec-ZZZ_Element_AAA.endf`
- **Photon Atomic:** `p-ZZZ_Element_AAA.endf`
- **Fission Yields:** Various naming patterns (nuclide-specific)

---

## Recommendations for Immediate Action

1. **Document the gaps** in current ENDF support
2. **Prioritize thermal scattering** for next major feature
3. **Plan burnup capability** (requires fission yields + decay data)
4. **Consider file discovery** for other data types (even if not parsed yet)

---

## Notes

- The current codebase is well-structured to add new data types
- File discovery system can be extended to other data types
- Caching system (Zarr) can handle any data type
- Parser architecture supports multiple backends (SANDY, built-in)

---

*This analysis is based on ENDF-B-VIII.1 directory structure and current SMRForge codebase capabilities as of January 2025.*

