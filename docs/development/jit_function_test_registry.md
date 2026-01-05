# JIT Function Test Registry

**Date:** January 1, 2026  
**Last Updated:** January 1, 2026

This document tracks all Numba JIT-compiled functions in SMRForge and ensures each has corresponding test files.

---

## Overview

Functions decorated with `@njit` or `@jit` are excluded from coverage reporting (`# pragma: no cover`) because Numba JIT compilation makes line-by-line coverage tracking unreliable. However, these functions must still be thoroughly tested through dedicated test files.

---

## JIT Function Registry

### ✅ Core Module (`smrforge/core/`)

#### 1. `_doppler_broaden` (reactor_core.py)
- **Location:** `smrforge/core/reactor_core.py:1286-1385`
- **Decorator:** `@njit(parallel=True, cache=True)`
- **Purpose:** Fast Doppler broadening of cross sections
- **Test File:** ✅ `tests/test_doppler_broaden.py` (13 comprehensive tests)
- **Test Coverage:**
  - Same temperature (no change)
  - Temperature increases/decreases
  - HTGR operating temperatures
  - High temperatures
  - Different mass numbers
  - Low energy preference
  - Zero energy handling
  - Single point arrays
  - Large arrays
  - Zero cross sections
  - Reversibility checks
- **Status:** ✅ **Well-tested**

#### 2. `_collapse_to_multigroup` (reactor_core.py)
- **Location:** `smrforge/core/reactor_core.py:2611-2710`
- **Decorator:** `@njit(parallel=True, cache=True)`
- **Purpose:** Fast group collapse for multi-group cross sections
- **Test Files:** ✅ Multiple test files
  - `tests/test_reactor_core.py` - Basic collapse tests
  - `tests/test_reactor_core_coverage_gaps.py` - 5 edge case tests
  - `tests/test_reactor_core_critical_comprehensive.py` - Additional tests
  - `tests/test_reactor_core_comprehensive.py` - Comprehensive tests
- **Test Coverage:**
  - Single point in group
  - Empty groups
  - Custom weighting flux
  - Zero denominator handling
  - Multiple groups
  - Large arrays
- **Status:** ✅ **Well-tested**

#### 3. `_compute_subgroup_flux` (resonance_selfshield.py)
- **Location:** `smrforge/core/resonance_selfshield.py:229-245`
- **Decorator:** `@njit(cache=True)`
- **Purpose:** Compute subgroup fluxes using rational approximation
- **Test File:** ✅ `tests/test_resonance_selfshield_critical.py`
- **Test Coverage:**
  - Basic subgroup flux computation
  - Zero background cross-section
  - High background cross-section
- **Status:** ✅ **Tested**

#### 4. `dancoff_factor_hexagonal` (resonance_selfshield.py)
- **Location:** `smrforge/core/resonance_selfshield.py:339-364`
- **Decorator:** `@njit(cache=True)`
- **Purpose:** Dancoff factor for hexagonal lattice of particles
- **Test File:** ✅ `tests/test_resonance_selfshield_comprehensive.py`
- **Test Coverage:**
  - Normal hexagonal lattice
  - Low packing fraction
  - High packing fraction
- **Status:** ✅ **Tested**

#### 5. `escape_probability_sphere` (resonance_selfshield.py)
- **Location:** `smrforge/core/resonance_selfshield.py:367-395`
- **Decorator:** `@njit(cache=True)`
- **Purpose:** Escape probability from sphere (Wigner rational approximation)
- **Test File:** ✅ `tests/test_resonance_selfshield_comprehensive.py`
- **Test Coverage:**
  - Small optical thickness
  - Medium optical thickness
  - Large optical thickness
- **Status:** ✅ **Tested**

#### 6. `graphite_conductivity_fast` (materials_database.py)
- **Location:** `smrforge/core/materials_database.py:945-967`
- **Decorator:** `@njit(cache=True)`
- **Purpose:** Ultra-fast graphite conductivity evaluation
- **Test File:** ✅ `tests/test_materials_database.py`
- **Test Coverage:**
  - All graphite grades (IG-110, H-451, NBG-18)
  - Temperature range validation
  - Array input handling
- **Status:** ✅ **Tested**

#### 7. `helium_properties_fast` (materials_database.py)
- **Location:** `smrforge/core/materials_database.py:970-1010`
- **Decorator:** `@njit(cache=True)`
- **Purpose:** Fast helium property evaluation (density, viscosity, conductivity)
- **Test File:** ✅ `tests/test_materials_database.py`
- **Test Coverage:**
  - Density calculation
  - Viscosity (Sutherland model)
  - Conductivity
  - Pressure dependence
- **Status:** ✅ **Tested**

---

### ✅ Geometry Module (`smrforge/geometry/`)

#### 8. `compute_distance_matrix` (core_geometry.py)
- **Location:** `smrforge/geometry/core_geometry.py:587-610`
- **Decorator:** `@njit(parallel=True, cache=True)`
- **Purpose:** Fast distance matrix computation using Numba
- **Test File:** ✅ `tests/test_geometry.py`
- **Test Coverage:**
  - Basic distance matrix computation
  - Symmetric matrix property
  - Multiple positions
- **Status:** ✅ **Tested**

---

### ✅ Safety Module (`smrforge/safety/`)

#### 9. `decay_heat_ans_standard` (transients.py)
- **Location:** `smrforge/safety/transients.py:1161-1187`
- **Decorator:** `@njit(cache=True)`
- **Purpose:** ANS 5.1 standard decay heat curve
- **Test File:** ✅ `tests/test_safety.py`
- **Test Coverage:**
  - Basic decay heat calculation
  - Edge cases (short time, long time)
  - Operating time dependence
- **Status:** ✅ **Tested**

---

### ✅ Thermal Module (`smrforge/thermal/`)

#### 10. `solve_tridiagonal_fast` (hydraulics.py)
- **Location:** `smrforge/thermal/hydraulics.py:759-791`
- **Decorator:** `@njit(cache=True)`
- **Purpose:** Fast tridiagonal solver using Thomas algorithm
- **Test File:** ✅ `tests/test_thermal.py`
- **Test Coverage:**
  - Basic tridiagonal system solution
  - Forward elimination
  - Back substitution
- **Status:** ✅ **Tested**

---

## Summary

| Module | Function | Test File | Status |
|--------|----------|-----------|--------|
| `core/reactor_core.py` | `_doppler_broaden` | `test_doppler_broaden.py` | ✅ |
| `core/reactor_core.py` | `_collapse_to_multigroup` | Multiple files | ✅ |
| `core/resonance_selfshield.py` | `_compute_subgroup_flux` | `test_resonance_selfshield_critical.py` | ✅ |
| `core/resonance_selfshield.py` | `dancoff_factor_hexagonal` | `test_resonance_selfshield_comprehensive.py` | ✅ |
| `core/resonance_selfshield.py` | `escape_probability_sphere` | `test_resonance_selfshield_comprehensive.py` | ✅ |
| `core/materials_database.py` | `graphite_conductivity_fast` | `test_materials_database.py` | ✅ |
| `core/materials_database.py` | `helium_properties_fast` | `test_materials_database.py` | ✅ |
| `geometry/core_geometry.py` | `compute_distance_matrix` | `test_geometry.py` | ✅ |
| `safety/transients.py` | `decay_heat_ans_standard` | `test_safety.py` | ✅ |
| `thermal/hydraulics.py` | `solve_tridiagonal_fast` | `test_thermal.py` | ✅ |

**Total JIT Functions:** 10  
**Functions with Tests:** 10 (100%)  
**Status:** ✅ **All JIT functions have corresponding test files**

---

## Best Practices for JIT Functions

### 1. Documentation Requirements

All JIT functions should include:
- `# pragma: no cover` comment
- Note in docstring explaining why coverage is excluded
- Reference to test file(s) in docstring
- Example:

```python
@njit(cache=True)
def my_jit_function(...) -> np.ndarray:  # pragma: no cover
    """
    Fast computation using Numba JIT compilation.
    
    Note: This function is excluded from coverage reporting because Numba JIT
    compilation makes line-by-line coverage tracking unreliable. This function
    is extensively tested in tests/test_my_jit_function.py (N tests).
    """
    ...
```

### 2. Test File Naming Convention

- **Dedicated test files:** `test_<function_name>.py` (e.g., `test_doppler_broaden.py`)
- **Module test files:** Include JIT function tests in module test files (e.g., `test_resonance_selfshield_comprehensive.py`)

### 3. Test Coverage Requirements

Each JIT function should have tests covering:
- ✅ Normal operation with typical inputs
- ✅ Edge cases (zero values, empty arrays, extreme values)
- ✅ Boundary conditions
- ✅ Error handling (if applicable)
- ✅ Performance validation (optional but recommended)

### 4. Adding New JIT Functions

When adding a new JIT function:

1. ✅ Add `# pragma: no cover` comment
2. ✅ Document test file in docstring
3. ✅ Create or update corresponding test file
4. ✅ Add entry to this registry
5. ✅ Ensure tests cover all code paths

---

## Verification Script

To verify all JIT functions have tests, run:

```bash
# Find all JIT functions
grep -r "@njit\|@jit" smrforge/ --include="*.py"

# Check for corresponding test files
# (Manual verification required - see registry above)
```

---

## Future Improvements

1. **Automated Test Discovery:** Create script to automatically verify JIT functions have tests
2. **Test Coverage Metrics:** Track test count per JIT function
3. **Performance Benchmarks:** Add performance tests for JIT functions
4. **Documentation Generation:** Auto-generate this registry from code

---

## References

- `docs/development/critical-coverage-issues.md` - Critical Issue #5: Numba JIT Function Coverage
- `docs/development/coverage-exclusions.md` - Coverage exclusions documentation
- `tests/test_doppler_broaden.py` - Example comprehensive JIT function test file

