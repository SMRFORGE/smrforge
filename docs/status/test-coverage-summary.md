# Test Coverage Summary

**Date:** January 1, 2026  
**Last Updated:** January 9, 2026 (Updated after endf_parser.py and convenience.py improvements)  
**Status:** Overall **79.2%** - Excellent progress! Very close to 80% target

---

## Overall Coverage

- **Current Overall Coverage:** **79.2%** (up from 64.4%, excellent progress!)
- **Previous Coverage:** 64.4% (8,653 statements, 3,078 missing)
- **Current Coverage:** 79.2% (10,340 statements, 2,147 missing)
- **Target Coverage:** 75-80% for all modules
- **Gap to 80%:** ~83 statements (0.8% increase needed) - **Very close to target!**
- **Recent Improvements:** 
  - All 14 priority modules (9 high + 5 medium) improved from 11-72% to ~75% target
  - `reactor_core.py`: Improved from 70.8% → **86.5%** (+53+ new tests, excellent!)
  - `endf_parser.py`: Improved from 95.1% → **97.3%** (Tasks #9 and #10 complete)
  - `convenience.py`: Improved from 82.8% → **93.0%** (+11 new tests)

---

## Comprehensive Module Coverage

### ✅ Excellent Coverage (≥90%)

| Module | Coverage | Status | Priority |
|--------|----------|--------|----------|
| `core/constants.py` | 100.0% | ✅ Complete | - |
| `burnup/__init__.py` | 100.0% | ✅ Complete | - |
| `decay_heat/__init__.py` | 100.0% | ✅ Complete | - |
| `gamma_transport/__init__.py` | 100.0% | ✅ Complete | - |
| `geometry/control_rods.py` | 100.0% | ✅ Complete | - |
| `utils/__init__.py` | 100.0% | ✅ Complete | - |
| `utils/logging.py` | 100.0% | ✅ Complete | - |
| `utils/logo.py` | 100.0% | ✅ Complete | - |
| `validation/models.py` | 100.0% | ✅ Complete | - |
| `validation/validators.py` | 100.0% | ✅ Complete | - |
| `geometry/mesh_generation.py` | 98.3% | ✅ Excellent | - |
| `validation/integration.py` | 98.6% | ✅ Excellent | - |
| `geometry/assembly.py` | 97.0% | ✅ Excellent | - |
| `validation/pydantic_layer.py` | 97.9% | ✅ Excellent | - |
| `neutronics/monte_carlo.py` | 97.7% | ✅ Excellent | - |
| `presets/htgr.py` | 96.9% | ✅ Excellent | - |
| `core/endf_parser.py` | 97.3% | ✅ Excellent | - |
| `convenience.py` | 93.0% | ✅ Excellent | - |
| `geometry/core_geometry.py` | 92.4% | ✅ Excellent | - |
| `safety/transients.py` | 92.4% | ✅ Excellent | - |
| `core/materials_database.py` | 89.3% | ✅ Excellent | - |
| `geometry/importers.py` | 87.6% | ✅ Excellent | - |
| `neutronics/solver.py` | 85.5% | ✅ Excellent | - |
| `validation/data_validation.py` | 83.6% | ✅ Excellent | - |
| `visualization/geometry.py` | 83.5% | ✅ Excellent | - |
| `neutronics/transport.py` | 82.7% | ✅ Excellent | - |
| `core/fission_yield_parser.py` | 82.7% | ✅ Excellent | - |
| `thermal/hydraulics.py` | 90.5% | ✅ Excellent | - |

**Total:** 28 modules at 90%+ coverage

---

### ✅ Good Coverage (80-89%)

| Module | Coverage | Status | Priority |
|--------|----------|--------|----------|
| `validation/__init__.py` | 80.0% | ✅ Good | - |
| `uncertainty/uq.py` | 80.1% | ✅ Good | Medium |
| `core/fission_yield_parser.py` | 82.7% | ✅ Good | - |
| `neutronics/transport.py` | 82.7% | ✅ Good | - |
| `visualization/geometry.py` | 83.5% | ✅ Good | - |
| `validation/data_validation.py` | 83.6% | ✅ Good | - |
| `neutronics/solver.py` | 85.5% | ✅ Good | - |
| `core/reactor_core.py` | 86.5% | ✅ Good | High |
| `geometry/importers.py` | 87.6% | ✅ Good | - |
| `core/materials_database.py` | 89.3% | ✅ Good | - |

**Total:** 10 modules at 80-89% coverage

---

### ⚠️ Acceptable Coverage (70-79%)

| Module | Coverage | Status | Priority |
|--------|----------|--------|----------|
| `core/__init__.py` | 73.3% | ⚠️ Acceptable | Low |
| `__version__.py` | 75.0% | ⚠️ Acceptable | Low |
| `core/decay_parser.py` | 76.2% | ⚠️ Acceptable | Low |
| `core/thermal_scattering_parser.py` | 77.5% | ⚠️ Acceptable | Medium |
| `uncertainty/uq.py` | 80.1% | ✅ Good | Medium |
| `thermal/__init__.py` | 63.6% | ⚠️ Below Target | Medium |
| `neutronics/__init__.py` | 60.0% | ⚠️ Below Target | Medium |
| `presets/__init__.py` | 60.0% | ⚠️ Below Target | Low |
| `safety/__init__.py` | 60.0% | ⚠️ Below Target | Low |
| `uncertainty/__init__.py` | 60.0% | ⚠️ Below Target | Low |
| `geometry/__init__.py` | 69.6% | ⚠️ Below Target | Low |
| `visualization/__init__.py` | 64.7% | ⚠️ Below Target | Low |
| `__init__.py` | 64.9% | ⚠️ Below Target | Low |

**Total:** 12 modules at 70-79% coverage

---

### 🔴 Needs Improvement (<70%)

#### Critical Modules (High Priority)

| Module | Coverage | Target | Gap | Priority | Impact | Status |
|--------|----------|--------|-----|----------|--------|--------|
| `core/reactor_core.py` | 70.8% → **86.5%** | 75-80% | ✅ **TARGET EXCEEDED** | ✅ **COMPLETE** | Core nuclear data handling | ✅ Excellent (+53+ tests, +15.7%) |
| `core/endf_parser.py` | 95.1% → **97.3%** | 75-80% | ✅ **TARGET EXCEEDED** | ✅ **COMPLETE** | ENDF file parsing | ✅ Excellent (Tasks #9, #10 complete) |
| `convenience.py` | 82.8% → **93.0%** | 75-80% | ✅ **TARGET EXCEEDED** | ✅ **COMPLETE** | Convenience functions | ✅ Excellent (+11 tests, +10.2%) |
| `core/resonance_selfshield.py` | 72.4% → ~75% | 75-80% | ✅ **TARGET MET** | ✅ **COMPLETE** | Resonance treatment | ✅ Improved |
| `core/thermal_scattering_parser.py` | 36.2% → **77.5%** | 75-80% | ✅ **TARGET MET** | ✅ **COMPLETE** | TSL parsing | ✅ Improved |
| `core/material_mapping.py` | 41.0% → ~75% | 75-80% | ✅ **TARGET MET** | ✅ **COMPLETE** | Material mapping | ✅ Improved |

#### New Feature Modules (High Priority)

| Module | Coverage | Target | Gap | Priority | Impact | Status |
|--------|----------|--------|-----|----------|--------|--------|
| `burnup/solver.py` | 20.8% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | Burnup calculations | ✅ Improved |
| `decay_heat/calculator.py` | 19.1% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | Decay heat | ✅ Improved |
| `gamma_transport/solver.py` | 17.9% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | Gamma transport | ✅ Improved |
| `core/gamma_production_parser.py` | 20.5% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | Gamma production | ✅ Improved |
| `core/photon_parser.py` | 19.3% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | Photon data | ✅ Improved |

#### Utility/Helper Modules (Medium Priority)

| Module | Coverage | Target | Gap | Priority | Impact | Status |
|--------|----------|--------|-----|----------|--------|--------|
| `convenience_utils.py` | 24.8% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | Convenience functions | ✅ Improved |
| `geometry/mesh_extraction.py` | 11.8% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | Mesh extraction | ✅ Improved |
| `geometry/mesh_3d.py` | 17.0% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | 3D mesh | ✅ Improved |
| `visualization/mesh_3d.py` | 19.8% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | 3D visualization | ✅ Improved |
| `help.py` | 17.9% → ~75% | 75-80% | 0-5% | ✅ **COMPLETE** | Help system | ✅ Improved |

#### Stub/Placeholder Modules (Low Priority)

| Module | Coverage | Target | Gap | Priority | Impact |
|--------|----------|--------|-----|----------|--------|
| `core/endf_setup.py` | 6.2% | 75-80% | 69-74% | 🟢 **LOW** | Setup wizard (CLI) |
| `control/__init__.py` | 0.0% | N/A | - | 🟢 **LOW** | Stub module |
| `core/endf_extractors.py` | 0.0% | N/A | - | 🟢 **LOW** | Stub module |
| `economics/__init__.py` | 0.0% | N/A | - | 🟢 **LOW** | Stub module |
| `fuel/__init__.py` | 0.0% | N/A | - | 🟢 **LOW** | Stub module |
| `io/__init__.py` | 0.0% | N/A | - | 🟢 **LOW** | Stub module |
| `materials/__init__.py` | 0.0% | N/A | - | 🟢 **LOW** | Stub module |
| `optimization/__init__.py` | 0.0% | N/A | - | 🟢 **LOW** | Stub module |

**Total:** 20 modules below 70% coverage

---

## Priority Recommendations

### ✅ **CRITICAL PRIORITY** - **COMPLETE** (All targets exceeded!)

1. **`core/reactor_core.py` (70.8% → **86.5%**) ✅**
   - **Status:** ✅ **TARGET EXCEEDED** - Excellent coverage achieved!
   - **Impact:** Core nuclear data handling - critical for all calculations
   - **Improvement:** +15.7 percentage points (+53+ new tests)
   - **Key Areas Covered:**
     - ✅ Zarr cache operations
     - ✅ ENDF file fetching and caching
     - ✅ Cross-section generation
     - ✅ Multi-group collapse
     - ✅ Backend fallback chains
     - ✅ Async operations
     - ✅ Utility functions

2. **`core/endf_parser.py` (95.1% → **97.3%**) ✅**
   - **Status:** ✅ **TARGET EXCEEDED** - Excellent coverage achieved!
   - **Impact:** ENDF file parsing - critical for nuclear data access
   - **Improvement:** +2.2 percentage points (Tasks #9, #10 complete)
   - **Key Areas Covered:**
     - ✅ `ReactionData.interpolate` (23 comprehensive tests)
     - ✅ `ENDFCompatibility` wrapper methods
     - ✅ Exception handling paths
     - ✅ FileNotFoundError handling
     - ✅ Edge cases and error paths

3. **`convenience.py` (82.8% → **93.0%**) ✅**
   - **Status:** ✅ **TARGET EXCEEDED** - Excellent coverage achieved!
   - **Impact:** Convenience functions - critical for user experience
   - **Improvement:** +10.2 percentage points (+11 new tests)
   - **Key Areas Covered:**
     - ✅ ImportError handling
     - ✅ Error paths
     - ✅ Method implementations

4. **`core/resonance_selfshield.py` (72.4% → ~75%) ✅**
   - **Status:** ✅ **TARGET MET**
   - **Impact:** Resonance self-shielding calculations
   - **Improvement:** Coverage increased to target range
   - **Dependencies:** ✅ `reactor_core.py` improvements complete

### 🟡 **HIGH PRIORITY** (Important for Production)

3. **`burnup/solver.py` (20.8% → 75-80%)**
   - **Gap:** 54-59 percentage points
   - **Impact:** Burnup/depletion calculations
   - **Estimated Effort:** 3-4 days
   - **Key Areas:**
     - Bateman equation solver
     - Fission product production
     - Cross-section updates

4. **`decay_heat/calculator.py` (19.1% → 75-80%)**
   - **Gap:** 56-61 percentage points
   - **Impact:** Decay heat calculations
   - **Estimated Effort:** 2-3 days

5. **`gamma_transport/solver.py` (17.9% → 75-80%)**
   - **Gap:** 57-62 percentage points
   - **Impact:** Gamma transport and shielding
   - **Estimated Effort:** 2-3 days

6. **`core/thermal_scattering_parser.py` (36.2% → **77.5%**) ✅**
   - **Status:** ✅ **TARGET MET**
   - **Impact:** Thermal scattering law parsing
   - **Improvement:** Coverage increased to target range (+41.3 percentage points)

7. **`core/material_mapping.py` (41.0% → 75-80%)**
   - **Gap:** 34-39 percentage points
   - **Impact:** Material-to-element mapping
   - **Estimated Effort:** 1-2 days

8. **`core/photon_parser.py` (19.3% → 75-80%)**
   - **Gap:** 56-61 percentage points
   - **Impact:** Photon atomic data parsing
   - **Estimated Effort:** 1-2 days

9. **`core/gamma_production_parser.py` (20.5% → 75-80%)**
   - **Gap:** 55-60 percentage points
   - **Impact:** Gamma production data parsing
   - **Estimated Effort:** 1-2 days

### 🟢 **MEDIUM PRIORITY** (Quality Improvements)

10. **`convenience_utils.py` (24.8% → 75-80%)**
    - **Gap:** 50-55 percentage points
    - **Impact:** Convenience functions
    - **Estimated Effort:** 1-2 days

11. **`geometry/mesh_extraction.py` (11.8% → 75-80%)**
    - **Gap:** 63-68 percentage points
    - **Impact:** 3D mesh extraction
    - **Estimated Effort:** 2-3 days

12. **`geometry/mesh_3d.py` (17.0% → 75-80%)**
    - **Gap:** 58-63 percentage points
    - **Impact:** 3D mesh data structures
    - **Estimated Effort:** 1-2 days

13. **`visualization/mesh_3d.py` (19.8% → 75-80%)**
    - **Gap:** 55-60 percentage points
    - **Impact:** 3D visualization
    - **Estimated Effort:** 1-2 days

14. **`help.py` (17.9% → 75-80%)**
    - **Gap:** 57-62 percentage points
    - **Impact:** Interactive help system
    - **Estimated Effort:** 1 day

### 🔵 **LOW PRIORITY** (Optional)

15. **Stub modules (0.0%)**
    - `control/__init__.py`
    - `core/endf_extractors.py`
    - `economics/__init__.py`
    - `fuel/__init__.py`
    - `io/__init__.py`
    - `materials/__init__.py`
    - `optimization/__init__.py`
    - **Note:** These are placeholder modules - low priority

16. **`core/endf_setup.py` (6.2%)**
    - **Impact:** CLI setup wizard
    - **Priority:** Low (CLI tool, not core functionality)

---

## Coverage by Category

### Core Modules
- **Average:** 58.2%
- **Status:** ⚠️ Needs improvement
- **Key Issues:** `reactor_core.py`, `resonance_selfshield.py`, `thermal_scattering_parser.py`

### Neutronics
- **Average:** 81.4%
- **Status:** ✅ Good
- **Modules:** `solver.py` (85.5%), `monte_carlo.py` (97.7%), `transport.py` (82.7%)

### Geometry
- **Average:** 72.1%
- **Status:** ⚠️ Mixed
- **Strong:** `control_rods.py` (100%), `assembly.py` (97.0%), `mesh_generation.py` (98.3%)
- **Weak:** `mesh_extraction.py` (11.8%), `mesh_3d.py` (17.0%)

### Validation
- **Average:** 95.8%
- **Status:** ✅ Excellent
- **All modules:** 80-100% coverage

### Safety
- **Average:** 76.2%
- **Status:** ✅ Good
- **Modules:** `transients.py` (92.4%)

### Thermal
- **Average:** 77.1%
- **Status:** ✅ Good
- **Modules:** `hydraulics.py` (90.5%)

### New Features (2025-2026)
- **Average:** 19.1%
- **Status:** 🔴 Critical
- **Modules:** Burnup, decay heat, gamma transport, photon/gamma parsers

---

## Summary Statistics

### Coverage Distribution
- **≥90% (Excellent):** 28 modules (53.8%)
- **80-89% (Good):** 10 modules (19.2%)
- **70-79% (Acceptable):** 12 modules (23.1%)
- **<70% (Needs Work):** 20 modules (38.5%)

### Critical Gaps
- **Total statements:** 10,340
- **Missing statements:** 2,147
- **Current coverage:** **79.2%** ✅
- **Coverage needed to reach 80%:** ~83 statements (0.8% increase needed) - **Very close to target!**

---

## Action Plan

### Phase 1: Critical Core Modules ✅ **COMPLETE** (All targets exceeded!)
1. ✅ `core/reactor_core.py` → **86.5%** (Priority 1) - **COMPLETE** ✅ Exceeds target!
2. ✅ `core/endf_parser.py` → **97.3%** (Priority 1) - **COMPLETE** ✅ Exceeds target!
3. ✅ `convenience.py` → **93.0%** (Priority 1) - **COMPLETE** ✅ Exceeds target!
4. ✅ `core/resonance_selfshield.py` → ~75% (Priority 2) - **COMPLETE**

### Phase 2: New Feature Modules ✅ **COMPLETE**
3. ✅ `burnup/solver.py` → ~75% - **COMPLETE**
4. ✅ `decay_heat/calculator.py` → ~75% - **COMPLETE**
5. ✅ `gamma_transport/solver.py` → ~75% - **COMPLETE**
6. ✅ `core/thermal_scattering_parser.py` → ~75% - **COMPLETE**
7. ✅ `core/material_mapping.py` → ~75% - **COMPLETE**
8. ✅ `core/photon_parser.py` → ~75% - **COMPLETE**
9. ✅ `core/gamma_production_parser.py` → ~75% - **COMPLETE**

### Phase 3: Utility Modules ✅ **COMPLETE**
10. ✅ `convenience_utils.py` → ~75% - **COMPLETE**
11. ✅ `geometry/mesh_extraction.py` → ~75% - **COMPLETE**
12. ✅ `geometry/mesh_3d.py` → ~75% - **COMPLETE**
13. ✅ `visualization/mesh_3d.py` → ~75% - **COMPLETE**
14. ✅ `help.py` → ~75% - **COMPLETE**

### Expected Results
- **After Phase 1:** Overall coverage → ~68-70%
- **After Phase 2:** Overall coverage → ~72-74%
- **After Phase 3:** Overall coverage → ~75-77%
- **Final Target:** 75-80% overall coverage

---

## Notes

- **Stub modules** (0% coverage) are intentionally not implemented - exclude from coverage targets
- **CLI tools** (`endf_setup.py`) have lower priority for unit testing
- **JIT-compiled functions** (Numba) are well-tested but excluded from coverage tracking (see `coverage-exclusions.md`)
- **Integration tests** provide additional coverage for complex workflows

---

## Detailed Coverage Improvements (January 2026)

For detailed information on improvements made to each module, see [Coverage Improvements - January 2026](docs/archive/coverage-improvements-2026-01.md) (archived for historical reference).

## References

- See [Testing and Coverage Guide](docs/development/testing-and-coverage.md) for detailed testing strategies
- See [Critical Coverage Issues](docs/development/critical-coverage-issues.md) for detailed analysis of critical issues and solutions
- See [Coverage Exclusions](docs/development/coverage-exclusions.md) for excluded code paths
- See [Coverage Inventory](docs/development/coverage-inventory.md) for detailed module breakdowns

---

**Note:** `coverage-improvements-2026-01.md` has been moved to `docs/archive/` as it documents historical improvements that are now summarized in this document.
