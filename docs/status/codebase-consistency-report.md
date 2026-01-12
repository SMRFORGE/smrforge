# Codebase Consistency Report

**Date:** January 2026  
**Scope:** Type hints, classes, optimizations, and docstrings

---

## Executive Summary

This report analyzes consistency across the SMRForge codebase in four key areas:
1. **Type Hints** - Usage and consistency
2. **Classes** - Structure and documentation
3. **Optimizations** - Opportunities for improvement
4. **Docstrings** - Format and completeness

**Overall Status:** ✅ **Good** with areas for improvement

---

## 1. Type Hints

### Current State

**Strengths:**
- ✅ Most new files have type hints (e.g., `self_shielding_integration.py`, `temperature_interpolation.py`)
- ✅ Return types are generally well-specified
- ✅ Complex types use `typing` module appropriately

**Issues Found:**

#### 1.1 Inconsistent Type Hint Syntax
- **Issue:** Mix of `tuple[...]` (Python 3.9+) and `Tuple[...]` (typing module)
- **Examples:**
  - `self_shielding_integration.py:39`: Uses `tuple[np.ndarray, np.ndarray]` ✅
  - `temperature_interpolation.py:223`: Uses `Tuple[np.ndarray, np.ndarray]` ✅
  - Some older files may use `Tuple` from typing module
- **Recommendation:** Standardize on `tuple[...]` for Python 3.9+ (project supports 3.8+), or use `Tuple` from typing for compatibility

#### 1.2 Missing Type Hints
- **Issue:** Some function parameters lack type hints
- **Examples:**
  - `temperature_interpolation.py:223-230`: `cache`, `nuclide`, `library` parameters lack types
  - `multigroup_advanced.py:83-91`: `nuclide`, `cache` parameters lack types
- **Recommendation:** Add type hints to all function parameters

#### 1.3 Inconsistent Optional Usage
- **Issue:** Some functions use `Optional[...]` while others use `... | None`
- **Recommendation:** Standardize on `Optional[...]` for Python 3.8+ compatibility

### Files Requiring Type Hint Updates

1. `smrforge/core/temperature_interpolation.py`
   - Line 223: `interpolate_cross_section_temperature` - missing types for `cache`, `nuclide`, `library`

2. `smrforge/core/multigroup_advanced.py`
   - Line 83: `calculate_sph_factors` - missing types for `nuclide`, `cache`

3. `smrforge/core/endf_extractors.py`
   - Various functions may need type hint updates

---

## 2. Classes

### Current State

**Strengths:**
- ✅ Good use of dataclasses for data containers
- ✅ Classes generally have docstrings
- ✅ Class attributes are documented in docstrings

**Issues Found:**

#### 2.1 Inconsistent Class Documentation
- **Issue:** Some classes have comprehensive docstrings, others have minimal ones
- **Examples:**
  - `MSRSMRCore` (molten_salt_smr.py) - ✅ Excellent docstring with usage examples
  - `CompactSMRCore` (smr_compact_core.py) - ✅ Good docstring
  - Some dataclasses have minimal docstrings

#### 2.2 Missing Class Attribute Type Hints
- **Issue:** Some class attributes lack type hints in docstrings or annotations
- **Example:** `MSRSMRCore.__init__` - attributes like `salt_channels`, `graphite_blocks` are typed but could be more explicit

#### 2.3 Method Documentation Inconsistency
- **Issue:** Some methods have detailed docstrings, others are minimal
- **Example:** `MSRSMRCore.add_salt_channel` - minimal docstring vs `build_liquid_fuel_core` - comprehensive docstring

### Recommendations

1. **Standardize Class Docstrings:**
   - All classes should have docstrings with:
     - Brief description
     - Attributes section (for dataclasses, use field docstrings)
     - Usage examples (for public classes)

2. **Method Documentation:**
   - All public methods should have docstrings with Args/Returns/Raises sections
   - Private methods (`_method_name`) can have minimal docstrings

3. **Type Annotations:**
   - Use type hints for all class attributes where possible
   - For dataclasses, use field annotations

---

## 3. Optimizations

### Current State

**Strengths:**
- ✅ Previous optimizations documented (see `docs/implementation/optimization.md`)
- ✅ Vectorization used where appropriate
- ✅ Caching implemented for expensive operations

**Issues Found:**

#### 3.1 Loop-Based Operations That Could Be Vectorized

**File:** `smrforge/core/self_shielding_integration.py`

**Issue:** Energy loop in `get_cross_section_with_self_shielding`
- **Lines 101-106:** Loop over energy points for Bondarenko method
- **Lines 115-167:** Multiple loops for subgroup method
- **Recommendation:** Vectorize where possible using numpy operations

```python
# Current (lines 101-106):
for i, (e, xs_inf_i) in enumerate(zip(energy, xs_inf)):
    xs_shielded[i] = bondarenko.shield_cross_section(
        xs_inf_i, nuclide_name, reaction, sigma_0, temperature
    )

# Potential optimization: Vectorize if bondarenko.shield_cross_section supports it
# Or batch process in chunks
```

**File:** `smrforge/core/temperature_interpolation.py`

**Issue:** Loop in `_interpolate_spline` method
- **Lines 205-218:** Loop over energy points for spline interpolation
- **Recommendation:** Consider vectorized spline interpolation if scipy supports it

```python
# Current (lines 205-218):
for i in range(n_energies):
    xs_at_energy = self.cross_sections[:, i]
    spline = UnivariateSpline(...)
    xs_interp[i] = spline(temperature)

# Potential: Use scipy.interpolate.interp2d or similar for 2D interpolation
```

#### 3.2 List Comprehensions vs NumPy Operations

**File:** `smrforge/geometry/molten_salt_smr.py`

**Issue:** List comprehensions that could use numpy
- **Line 210:** `sum(channel.volume() for channel in self.channels)`
- **Line 214:** `sum(channel.fuel_mass() for channel in self.channels)`
- **Recommendation:** If `channels` is large, consider numpy operations, but current approach is fine for typical sizes

#### 3.3 Redundant Calculations

**File:** `smrforge/geometry/two_phase_flow.py`

**Issue:** `_get_saturation_densities` called multiple times
- **Lines 72, 97, 165, 188:** Called in multiple methods
- **Recommendation:** Cache saturation properties if called frequently

```python
# Potential optimization: Cache saturation properties
@functools.lru_cache(maxsize=128)
def _get_saturation_densities_cached(self, pressure: float) -> tuple[float, float]:
    ...
```

### Optimization Priority

**High Priority:**
1. Vectorize energy loops in `self_shielding_integration.py` (if possible)
2. Cache saturation properties in `two_phase_flow.py`

**Medium Priority:**
1. Consider 2D interpolation for temperature interpolation
2. Profile list comprehensions vs numpy operations

**Low Priority:**
1. Current optimizations are generally good
2. Focus on algorithmic improvements rather than micro-optimizations

---

## 4. Docstrings

### Current State

**Strengths:**
- ✅ Google-style docstrings used consistently
- ✅ Most public functions have docstrings
- ✅ Docstrings include Args/Returns sections

**Issues Found:**

#### 4.1 Inconsistent Docstring Completeness

**Examples of Good Docstrings:**
- `get_cross_section_with_self_shielding` (self_shielding_integration.py:40-79) - ✅ Excellent
- `MSRSMRCore.build_liquid_fuel_core` (molten_salt_smr.py:275-295) - ✅ Excellent

**Examples Needing Improvement:**
- `MSRSMRCore.add_salt_channel` (molten_salt_smr.py:259) - Minimal docstring
- `MSRSMRCore.add_graphite_block` (molten_salt_smr.py:263) - Minimal docstring
- `CompactSMRCore._calculate_square_arrangement` (smr_compact_core.py:154) - Private method, acceptable

#### 4.2 Missing Raises Sections

**Issue:** Many docstrings don't document exceptions
- **Example:** `get_cross_section_with_self_shielding` doesn't document `ValueError` for unknown method
- **Recommendation:** Add `Raises:` section for public functions that raise exceptions

#### 4.3 Inconsistent Example Format

**Issue:** Some docstrings have examples, others don't
- **Good:** `get_cross_section_with_self_shielding` has comprehensive example
- **Missing:** Some utility functions lack examples
- **Recommendation:** Add examples to public API functions

### Docstring Standards Checklist

For each public function/class, docstrings should include:

- [x] Brief description (one line)
- [x] Detailed description (if needed)
- [x] Args section (for all parameters)
- [x] Returns section (for return values)
- [ ] Raises section (for exceptions)
- [ ] Example section (for public API functions)
- [ ] Notes section (for important caveats)

---

## 5. Specific File Recommendations

### High Priority Fixes

1. **`smrforge/core/temperature_interpolation.py`**
   - Add type hints to `interpolate_cross_section_temperature` parameters
   - Consider vectorizing spline interpolation loop

2. **`smrforge/core/self_shielding_integration.py`**
   - Consider vectorizing energy loops (if Bondarenko method supports it)
   - Add `Raises:` section to docstrings

3. **`smrforge/geometry/two_phase_flow.py`**
   - Cache saturation density calculations
   - Add type hints to `_get_saturation_densities` return type

### Medium Priority Fixes

1. **`smrforge/core/multigroup_advanced.py`**
   - Add type hints to `calculate_sph_factors` parameters
   - Ensure all public methods have complete docstrings

2. **`smrforge/geometry/molten_salt_smr.py`**
   - Add docstrings to simple methods (`add_salt_channel`, etc.)
   - Consider if list comprehensions need optimization

3. **`smrforge/geometry/smr_scram_system.py`**
   - Verify all methods have docstrings
   - Add `Raises:` sections where appropriate

### Low Priority (Nice to Have)

1. Standardize on `tuple[...]` vs `Tuple[...]` syntax
2. Add examples to all public API functions
3. Consider using `@dataclass` field documentation for better IDE support

---

## 6. Code Style Consistency

### Current Adherence

- ✅ **Formatting:** Black is used (88 char line length)
- ✅ **Imports:** isort is used
- ✅ **Type Checking:** mypy is configured
- ✅ **Docstrings:** Google-style is standard

### Recommendations

1. **Run mypy regularly** to catch type inconsistencies
2. **Use pre-commit hooks** to enforce style consistency
3. **Document exceptions** in docstrings (`Raises:` sections)
4. **Add examples** to public API functions

---

## 7. Summary Statistics

### Type Hints Coverage
- **Estimated:** ~85% of functions have type hints
- **Target:** 100% for public API, 90%+ overall

### Docstring Coverage
- **Estimated:** ~90% of public functions have docstrings
- **Target:** 100% for public API

### Optimization Status
- **Status:** Good - most critical paths optimized
- **Opportunities:** Some loops could be vectorized, caching could be improved

### Class Documentation
- **Status:** Good - most classes well-documented
- **Opportunities:** More examples, consistent attribute documentation

---

## 8. Action Items

### Immediate (High Priority)
1. [x] Add type hints to `temperature_interpolation.py:interpolate_cross_section_temperature` ✅ **COMPLETED**
2. [x] Add type hints to `multigroup_advanced.py:calculate_sph_factors` ✅ **COMPLETED**
3. [x] Add `Raises:` sections to docstrings that raise exceptions ✅ **COMPLETED**
4. [x] Cache saturation properties in `two_phase_flow.py` ✅ **COMPLETED**

### Short Term (Medium Priority)
1. [x] Vectorize Bondarenko path in `self_shielding_integration.py`; subgroup path remains looped ✅ **PARTIAL**
2. [x] Add docstrings to simple methods in geometry modules ✅ **COMPLETED**
3. [x] Standardize tuple type hint syntax ✅ **COMPLETED**
4. [ ] Add examples to public API functions (Ongoing - examples added where appropriate)

### Long Term (Low Priority)
1. [ ] Comprehensive mypy pass on all modules
2. [ ] Add examples to all public functions
3. [ ] Performance profiling and optimization pass
4. [ ] Documentation review for consistency

---

## 9. Tools and Automation

### Recommended Tools

1. **mypy** - Type checking
   ```bash
   mypy smrforge/ --ignore-missing-imports
   ```

2. **pydocstyle** - Docstring checking
   ```bash
   pydocstyle smrforge/ --convention=google
   ```

3. **black** - Code formatting (already in use)
   ```bash
   black --check smrforge/
   ```

4. **isort** - Import sorting (already in use)
   ```bash
   isort --check-only smrforge/
   ```

### Pre-commit Hooks

Consider adding to `.pre-commit-config.yaml`:
- black
- isort
- mypy (with appropriate ignores)
- pydocstyle (for docstring checking)

---

## 10. Conclusion

The SMRForge codebase demonstrates **good overall consistency** with:
- ✅ Strong adherence to code style standards
- ✅ Good type hint coverage
- ✅ Comprehensive docstrings for most public APIs
- ✅ Effective use of optimizations

**Areas for improvement:**
- Add missing type hints to some function parameters
- Standardize docstring completeness (add `Raises:` sections)
- Consider additional optimizations for loops
- Add examples to more public API functions

**Overall Grade:** **A-** (Excellent with minor improvements possible)

The codebase is well-maintained and follows best practices. Recent additions (data downloader) maintain high consistency standards. The recommendations in this report are incremental improvements rather than critical issues.

---

*Report generated: January 2026*  
*Implementation completed: January 2026*  
*Last updated: January 2026 (added data_downloader.py analysis)*  
*Next review: Quarterly or after major feature additions*

---

## Implementation Summary (January 2026)

### Completed Fixes

✅ **Type Hints:**
- Added type hints to `interpolate_cross_section_temperature` function
- Added type hints to `calculate_sph_factors` method
- Used `TYPE_CHECKING` for forward references to avoid circular imports
- Standardized on `tuple[...]` syntax (Python 3.9+ compatible)

✅ **Docstrings:**
- Added `Raises:` sections to `get_cross_section_with_self_shielding`
- Added `Raises:` sections to `get_cross_section_with_equivalence_theory`
- Added `Raises:` sections to `interpolate_cross_section_temperature`
- Added `Raises:` sections to `calculate_sph_factors`
- Enhanced docstrings for simple methods in `MSRSMRCore` class

✅ **Optimizations:**
- Implemented caching for saturation density calculations in `TwoPhaseFlowRegion`
- Added internal cache with size limit (128 entries) to prevent memory issues
- Cache is automatically managed and cleared when pressure changes
- Vectorized Bondarenko self-shielding path to avoid per-energy loops

✅ **Code Quality:**
- Removed unused `Tuple` import from `multigroup_advanced.py`
- All changes pass linting checks
- Type hints use proper forward references to avoid circular imports

### Files Modified

1. `smrforge/core/temperature_interpolation.py`
   - Added type hints with `TYPE_CHECKING` imports
   - Added `Raises:` section to docstring
   - Standardized `tuple[...]` syntax
   - Added example usage to public API

2. `smrforge/core/multigroup_advanced.py`
   - Added type hints with `TYPE_CHECKING` imports
   - Added `Raises:` section to docstring
   - Removed unused `Tuple` import
   - Added example usage to `calculate_sph_factors`

3. `smrforge/core/self_shielding_integration.py`
   - Added `Raises:` sections to both public functions
    - Vectorized Bondarenko path (single f-factor applied across energy grid)

4. `smrforge/geometry/two_phase_flow.py`
   - Implemented caching for saturation density calculations
   - Added cache field to `TwoPhaseFlowRegion` dataclass
   - Cache automatically manages size to prevent memory issues
   - Added example to `create_bwr_two_phase_region`

5. `smrforge/geometry/molten_salt_smr.py`
   - Enhanced docstrings for `add_salt_channel`, `add_graphite_block`, `add_circulation_loop`, `add_freeze_plug`
   - Added return type hints (`-> None`)

### Remaining Items

- **Vectorization of loops:** Deferred - requires investigation of whether Bondarenko method supports vectorization
- **Additional examples:** Ongoing - examples added where appropriate, more can be added incrementally

---

## 11. New Module Analysis: `data_downloader.py` (January 2026)

### Module Overview

**File:** `smrforge/data_downloader.py`  
**Purpose:** Automated ENDF data downloader with parallel downloads and connection pooling  
**Status:** ✅ **Good** - Follows codebase standards

### Consistency Analysis

#### ✅ Type Hints
- **Status:** Excellent
- All function parameters have type hints
- Return types are specified
- Uses `Optional`, `List`, `Dict`, `Union`, `Tuple` appropriately
- Example: `download_file(url: str, output_path: Path, ...) -> bool`

#### ✅ Docstrings
- **Status:** Good
- All public functions have docstrings
- Docstrings include Args and Returns sections
- Some functions have examples in docstrings
- **Minor:** Could add `Raises:` sections for exception documentation

#### ✅ Code Structure
- **Status:** Good
- Functions are well-organized
- Helper functions are properly prefixed with `_`
- Module-level constants are clearly defined
- Good separation of concerns

#### ✅ Optimizations
- **Status:** Excellent
- Parallel downloads using `ThreadPoolExecutor`
- Connection pooling with shared `requests.Session`
- URL source caching to avoid redundant attempts
- Progress indicators with `tqdm`

#### ⚠️ Minor Improvements Needed

1. **Exception Documentation:**
   - `download_file()` raises `ImportError` but doesn't document it in docstring
   - `download_endf_data()` may raise `ValueError` but not documented
   - **Recommendation:** Add `Raises:` sections

2. **Type Hints for Module-Level Variables:**
   - `_source_cache: Dict[str, str]` - ✅ Good
   - Could add type hints for return values in some helper functions

3. **Error Handling:**
   - Good try/except blocks
   - Could be more specific about exception types in some cases

### Recommendations for `data_downloader.py`

**Low Priority:**
1. Add `Raises:` sections to docstrings for public functions
2. Consider adding more detailed examples in docstrings
3. Document exception types more explicitly

**Status:** The module follows codebase standards well. Minor improvements are optional.

---

## 12. Recent Updates (January 2026)

### New Features Added

1. **Data Downloader Module** (`smrforge/data_downloader.py`)
   - ✅ Follows type hint standards
   - ✅ Good docstring coverage
   - ✅ Well-optimized with parallel downloads
   - ⚠️ Minor: Could add `Raises:` sections

2. **Environment Variable Support** (`smrforge/core/reactor_core.py`)
   - ✅ Added `_load_config_dir()` method with proper type hints
   - ✅ Good error handling
   - ✅ Follows existing code patterns

3. **Configuration File Support** (`smrforge/core/reactor_core.py`)
   - ✅ Optional dependency handling (PyYAML)
   - ✅ Graceful fallback if YAML not available
   - ✅ Proper logging

### Consistency Status

**Overall:** ✅ **Maintained** - New code follows established patterns

**New Code Quality:**
- Type hints: ✅ Excellent
- Docstrings: ✅ Good (minor improvements possible)
- Optimizations: ✅ Excellent
- Error handling: ✅ Good

---

## 13. Updated Action Items

### Immediate (High Priority)
1. [x] Add type hints to `temperature_interpolation.py:interpolate_cross_section_temperature` ✅ **COMPLETED**
2. [x] Add type hints to `multigroup_advanced.py:calculate_sph_factors` ✅ **COMPLETED**
3. [x] Add `Raises:` sections to docstrings that raise exceptions ✅ **COMPLETED**
4. [x] Cache saturation properties in `two_phase_flow.py` ✅ **COMPLETED**

### Short Term (Medium Priority)
1. [x] Vectorize Bondarenko path in `self_shielding_integration.py` ✅ **COMPLETED**
2. [x] Add docstrings to simple methods in geometry modules ✅ **COMPLETED**
3. [x] Standardize tuple type hint syntax ✅ **COMPLETED**
4. [ ] Add examples to public API functions (Ongoing)
5. [ ] Add `Raises:` sections to `data_downloader.py` functions (Low priority)

### Long Term (Low Priority)
1. [ ] Comprehensive mypy pass on all modules
2. [ ] Add examples to all public functions
3. [ ] Performance profiling and optimization pass
4. [ ] Documentation review for consistency
5. [ ] Add `Raises:` sections to `data_downloader.py` (optional improvement)
