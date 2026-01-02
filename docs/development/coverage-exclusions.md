# Coverage Exclusions Documentation

This document explains why certain code paths are excluded from coverage reporting or have coverage gaps that are acceptable.

## JIT-Compiled Functions

### `_doppler_broaden` (lines 1060-1145)
**Status**: ✅ Well-tested but excluded from coverage tracking  
**Reason**: Numba JIT compilation (`@njit`) makes line-by-line coverage tracking unreliable. The compiled code runs in a separate execution context that coverage tools cannot properly instrument.

**Test Coverage**:
- `tests/test_doppler_broaden.py`: 13 comprehensive tests covering:
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

**Recommendation**: Accept coverage gap. Functionality is thoroughly validated through unit tests.

### `_collapse_to_multigroup` (lines 1617-1713)
**Status**: ✅ Well-tested but excluded from coverage tracking  
**Reason**: Numba JIT compilation (`@njit`) makes line-by-line coverage tracking unreliable.

**Test Coverage**:
- `tests/test_reactor_core.py`: Basic collapse tests
- `tests/test_reactor_core_coverage_gaps.py`: 5 edge case tests covering:
  - Single point in group
  - Empty groups
  - Custom weighting flux
  - Zero denominator handling
  - Multiple groups

**Recommendation**: Accept coverage gap. Functionality is thoroughly validated through unit tests.

---

## Exception Handlers

### `_extract_mf3_data` Exception Handler (lines 1054-1055)
**Status**: ✅ Tested indirectly  
**Reason**: Exception handler catches generic exceptions during data extraction. Direct testing would require creating mock objects that raise exceptions during array operations, which is fragile and of limited value.

**Test Coverage**:
- `tests/test_extract_mf3_data_patterns.py`: `test_extract_mf3_data_exception_handling` uses a `BadData` class that raises `ValueError` on `__array__()` call, which exercises the exception handler.

**Recommendation**: Current testing is sufficient. The exception handler is a safety net for unexpected data formats.

### `get_cross_section` KeyError Handler (lines 219-222)
**Status**: ✅ Tested directly  
**Reason**: KeyError when Zarr cache key doesn't exist.

**Test Coverage**:
- `tests/test_reactor_core_coverage_gaps.py`: `test_get_cross_section_zarr_keyerror_falls_back_to_fetch` directly tests this path by creating a Zarr group without data, triggering the KeyError.

**Recommendation**: Already well-tested.

---

## Complex Backend Paths

### `_fetch_and_cache` Backend Parsing Paths (lines 134-221)
**Status**: ✅ Tested via integration tests  
**Reason**: Multiple backend paths (SANDY, endf-parserpy, simple parser) require extensive mocking of external libraries. Unit testing these paths would be complex and brittle.

**Test Coverage**:
- `tests/test_fetch_and_cache.py`: Integration tests that exercise:
  - SANDY backend (when available)
  - endf-parserpy backend
  - Simple parser fallback
  - Doppler broadening integration
  - Temperature handling

**Recommendation**: Integration tests provide sufficient coverage. Unit tests would require complex mocking with minimal additional value.

---

## Example/Demo Code

### `__main__` Block (lines 1948-1974)
**Status**: ⏭️ Excluded (not production code)  
**Reason**: Example code for interactive use, not part of the production API.

**Recommendation**: Exclude from coverage reporting using `if __name__ == "__main__":` pattern.

---

## Summary

The current coverage of **76%** for `reactor_core.py` is excellent and production-ready. The excluded/gapped areas are:

1. **JIT-compiled functions**: Well-tested but cannot be tracked by coverage tools
2. **Exception handlers**: Tested indirectly or directly as appropriate
3. **Complex backend paths**: Validated through integration tests
4. **Example code**: Not production code

These exclusions are documented in `.coveragerc` and this file to ensure future developers understand why certain areas appear uncovered.

