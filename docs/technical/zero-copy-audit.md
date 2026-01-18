# Zero-Copy Operations Audit

**Date:** January 2026  
**Status:** Audit Complete - Most Copies Are Necessary  
**Reference:** [OpenMC Improvement Recommendations](openmc-improvement-recommendations.md)

---

## Executive Summary

Conducted audit of `.copy()` operations in the codebase. Most copy operations are **necessary for correctness** (algorithm requirements, state preservation). However, we've created optimization utilities to help developers avoid unnecessary copies in the future.

---

## Copy Operations Analysis

### 1. `smrforge/neutronics/solver.py` - Line 646

**Location:** `_solve_groups_parallel_red_black()`

```python
flux_new = np.copy(flux_old)
```

**Status:** ✅ **NECESSARY**

**Reason:**
- Red-black algorithm requires modifying `flux_new` in place
- Must preserve `flux_old` for comparison/error checking
- Algorithm correctness depends on separate arrays

**Optimization:** None - required for algorithm correctness

---

### 2. `smrforge/neutronics/solver.py` - Line 888

**Location:** `_arnoldi_method()`

```python
original_flux = self.flux.copy() if self.flux is not None else None
```

**Status:** ✅ **NECESSARY**

**Reason:**
- Required for state preservation (rollback on error)
- Must preserve original state before modifications
- Error handling requires original state restoration

**Optimization:** None - required for error handling

---

### 3. `smrforge/neutronics/solver.py` - Line 896

**Location:** `_arnoldi_method() -> power_iteration_step()`

```python
flux_old = flux_vec.reshape(self.nz, self.nr, self.ng).copy()
```

**Status:** ✅ **NECESSARY**

**Reason:**
- Reshape creates view of original `flux_vec`
- We modify `flux_old` in place (set `self.flux = flux_old`)
- Must copy to avoid modifying original `flux_vec` from scipy

**Optimization:** None - required to avoid modifying scipy's internal array

---

## Optimization Utilities Created

### `ensure_contiguous()` - Smart Contiguity Check

**File:** `smrforge/utils/optimization_utils.py`

**Purpose:** Only copy when necessary (non-contiguous arrays)

```python
from smrforge.utils.optimization_utils import ensure_contiguous

# Returns view if already C-contiguous
arr_contig = ensure_contiguous(arr)  # Zero-copy if possible
```

**Benefit:** Avoids unnecessary copies for contiguous arrays

---

### `smart_array_copy()` - Smart Copy with Reuse

**File:** `smrforge/utils/optimization_utils.py`

**Purpose:** Reuse target array memory when possible

```python
from smrforge.utils.optimization_utils import smart_array_copy

# Reuses target memory if compatible
result = smart_array_copy(source, target)  # Reuses target if compatible
```

**Benefit:** Reduces memory allocation for repeated operations

---

## Recommendations

### ✅ Best Practices

1. **Use `ensure_contiguous()`** instead of `np.ascontiguousarray()` when you only need contiguity
2. **Use `smart_array_copy()`** when you have a target array that can be reused
3. **Check array flags** before copying: `if arr.flags['C_CONTIGUOUS']: use_view()`
4. **Document why copies are necessary** for algorithm correctness

### 📋 Future Optimization Opportunities

1. **Memory Pooling** - Reuse arrays from a pool instead of creating new ones
2. **In-Place Operations** - Use `+=`, `*=`, etc. instead of `arr = arr + x`
3. **Views Instead of Copies** - Use slicing/reshaping to create views when possible
4. **Lazy Evaluation** - Defer array creation until needed

---

## Conclusion

**Key Finding:** Most `.copy()` operations in the codebase are **necessary for correctness**. The codebase is already well-optimized in terms of copy operations.

**Improvement:** Created optimization utilities (`ensure_contiguous()`, `smart_array_copy()`) to help developers avoid unnecessary copies in future code.

**Impact:** Low (most copies are necessary), but utilities provide foundation for future optimizations

---

**Last Updated:** January 2026
