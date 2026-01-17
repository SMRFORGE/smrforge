# Numba Parallelization Implementation Plan for Multi-Group Diffusion Solver

**Date:** January 2026  
**Purpose:** Detailed implementation plan for parallelizing the multi-group diffusion solver using Numba  
**Target:** 4-8x speedup on multi-core CPUs (8-32 cores)

---

## Executive Summary

This document provides a step-by-step implementation plan for parallelizing the multi-group diffusion solver in `smrforge/neutronics/solver.py` using Numba's `@njit(parallel=True)` and `prange`. The plan focuses on:

1. **Energy group parallelization** - Parallel solve over energy groups
2. **Spatial loop parallelization** - Parallel operations over spatial cells
3. **Source term updates** - Parallel source computation
4. **Matrix assembly** - Parallel sparse matrix construction

**Expected Performance Gains:**
- 4-8x speedup on 8-32 core CPUs
- Scales well with number of energy groups
- Minimal code changes required
- Backwards compatible (fallback to serial if Numba unavailable)

---

## Current State Analysis

### Existing Parallelization
- ✅ **Numba already used** for:
  - Doppler broadening (`_doppler_broaden` with `parallel=True`)
  - Group collapse (`_collapse_cross_sections` with `parallel=True`)
  - Some transient calculations
- ⚠️ **Multi-group diffusion solver is serial:**
  - Energy groups solved sequentially
  - Source terms computed serially
  - Matrix assembly is serial

### Bottleneck Identification

**Key computational loops in `MultiGroupDiffusion`:**

1. **Energy Group Loop** (Line ~293 in `solve_steady_state`):
   ```python
   for g in range(self.ng):
       self._update_scattering_source(g)
       flux_g = self._solve_group(g)
       self.flux[:, :, g] = flux_g
   ```
   - **Parallelization opportunity:** Groups are independent within an iteration
   - **Challenge:** Each group depends on previous groups' scattering source

2. **Spatial Cell Loops** (in `_build_group_system`, `_update_source`):
   ```python
   for iz in range(nz):
       for ir in range(nr):
           # Matrix assembly, source computation
   ```
   - **Parallelization opportunity:** Spatial cells can be processed in parallel
   - **Challenge:** Matrix construction needs coordination

3. **Source Term Updates** (`_update_fission_source`, `_update_scattering_source`):
   - Already vectorized but could benefit from parallel reduction

---

## Implementation Strategy

### Phase 1: Parallel Energy Group Solve (Week 1-2)

**Goal:** Parallelize the energy group loop using a two-pass approach to handle group dependencies.

#### Challenge: Group Coupling
Energy groups are coupled through scattering:
- Group `g` receives scattering from groups `g' < g` (downscatter)
- Cannot solve all groups simultaneously

#### Solution: Red-Black Group Ordering

**Algorithm:**
1. **Pass 1:** Solve even groups in parallel (groups 0, 2, 4, ...)
2. **Pass 2:** Solve odd groups in parallel (groups 1, 3, 5, ...)
3. Iterate until convergence

This works because:
- Even groups depend only on lower even groups (minimal coupling)
- Odd groups depend on lower groups including even ones
- Two-pass sweep maintains accuracy while enabling parallelism

**Implementation:**

```python
def _solve_groups_parallel_red_black(self, flux_old: np.ndarray) -> np.ndarray:
    """
    Solve energy groups using red-black ordering for parallelization.
    
    Args:
        flux_old: Previous iteration flux [nz, nr, ng]
    
    Returns:
        New flux [nz, nr, ng]
    """
    flux_new = np.copy(flux_old)
    ng = self.ng
    
    # Separate even and odd groups
    even_groups = list(range(0, ng, 2))
    odd_groups = list(range(1, ng, 2))
    
    # Pass 1: Solve even groups in parallel
    if len(even_groups) > 1 and self.options.parallel:
        # Use ThreadPoolExecutor for parallel group solves
        with ThreadPoolExecutor(max_workers=min(len(even_groups), cpu_count())) as executor:
            futures = {
                executor.submit(self._solve_group_with_source, g, flux_new): g
                for g in even_groups
            }
            for future in as_completed(futures):
                g = futures[future]
                flux_g = future.result()
                flux_new[:, :, g] = flux_g
    else:
        # Serial fallback
        for g in even_groups:
            self._update_scattering_source_parallel(g, flux_new)
            flux_new[:, :, g] = self._solve_group(g)
    
    # Pass 2: Solve odd groups in parallel (can use updated even group fluxes)
    if len(odd_groups) > 1 and self.options.parallel:
        with ThreadPoolExecutor(max_workers=min(len(odd_groups), cpu_count())) as executor:
            futures = {
                executor.submit(self._solve_group_with_source, g, flux_new): g
                for g in odd_groups
            }
            for future in as_completed(futures):
                g = futures[future]
                flux_g = future.result()
                flux_new[:, :, g] = flux_g
    else:
        # Serial fallback
        for g in odd_groups:
            self._update_scattering_source_parallel(g, flux_new)
            flux_new[:, :, g] = self._solve_group(g)
    
    return flux_new
```

**Alternative: Simple Group Parallelization (if coupling is weak):**

For some problems, downscatter coupling is weak enough that all groups can be solved in parallel with minimal error:

```python
def _solve_groups_parallel_simple(self, flux_old: np.ndarray) -> np.ndarray:
    """Solve all groups in parallel (assumes weak coupling)."""
    flux_new = np.copy(flux_old)
    ng = self.ng
    
    if self.options.parallel and ng > 1:
        with ThreadPoolExecutor(max_workers=min(ng, cpu_count())) as executor:
            futures = {
                executor.submit(self._solve_group_with_source, g, flux_old): g
                for g in range(ng)
            }
            for future in as_completed(futures):
                g = futures[future]
                flux_new[:, :, g] = future.result()
    else:
        # Serial fallback
        for g in range(ng):
            self._update_scattering_source(g)
            flux_new[:, :, g] = self._solve_group(g)
    
    return flux_new
```

---

### Phase 2: Parallel Spatial Operations (Week 2-3)

**Goal:** Parallelize spatial loops using Numba's `prange`.

#### 2.1 Parallel Source Term Updates

**Current code** (`_update_scattering_source`):
```python
def _update_scattering_source(self, g: int) -> None:
    sigma_s_mat = self.xs.sigma_s[self.material_map, :, g]
    scatter_in = np.sum(sigma_s_mat * self.flux, axis=2)
    self.source[:, :, g] += scatter_in
```

**Parallelized version:**
```python
@staticmethod
@njit(parallel=True, cache=True)
def _update_scattering_source_parallel_numba(
    flux: np.ndarray,
    sigma_s: np.ndarray,
    material_map: np.ndarray,
    source: np.ndarray,
    g: int,
) -> None:
    """
    Parallel scattering source update using Numba.
    
    Args:
        flux: Flux array [nz, nr, ng]
        sigma_s: Scattering matrix [n_materials, ng, ng]
        material_map: Material map [nz, nr]
        source: Source array [nz, nr, ng] (modified in-place)
        g: Target energy group
    """
    nz, nr = material_map.shape
    ng = flux.shape[2]
    
    # Parallelize over spatial cells
    for iz in prange(nz):
        for ir in prange(nr):
            mat = material_map[iz, ir]
            scatter_in = 0.0
            
            # Sum scattering from all source groups
            for g_prime in range(ng):
                scatter_in += sigma_s[mat, g_prime, g] * flux[iz, ir, g_prime]
            
            source[iz, ir, g] += scatter_in
```

**Integration:**
```python
def _update_scattering_source(self, g: int) -> None:
    """Update scattering source, using parallel version if available."""
    if self.options.parallel and self.ng > 1:
        # Use Numba parallel version
        _update_scattering_source_parallel_numba(
            self.flux,
            self.xs.sigma_s,
            self.material_map,
            self.source,
            g
        )
    else:
        # Fallback to vectorized version (faster for small problems)
        sigma_s_mat = self.xs.sigma_s[self.material_map, :, g]
        scatter_in = np.sum(sigma_s_mat * self.flux, axis=2)
        self.source[:, :, g] += scatter_in
```

#### 2.2 Parallel Matrix Assembly

**Current code** (`_build_group_system`):
```python
for iz in range(nz):
    for ir in range(nr):
        idx = iz * nr + ir
        # Build matrix row
```

**Parallelized version:**
```python
@staticmethod
@njit(parallel=True, cache=True)
def _build_group_system_parallel_numba(
    nz: int,
    nr: int,
    sigma_t: np.ndarray,
    D: np.ndarray,
    material_map: np.ndarray,
    cell_volumes: np.ndarray,
    dz: np.ndarray,
    dr: np.ndarray,
    r_centers: np.ndarray,
    g: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Build sparse matrix system in parallel using Numba.
    
    Returns:
        (row_indices, col_indices, data, rhs) for COO format
    """
    n = nz * nr
    
    # Pre-allocate arrays (estimate max non-zeros per row: 5-7)
    max_nnz_per_row = 7
    row_indices = np.zeros(n * max_nnz_per_row, dtype=np.int32)
    col_indices = np.zeros(n * max_nnz_per_row, dtype=np.int32)
    data = np.zeros(n * max_nnz_per_row, dtype=np.float64)
    rhs = np.zeros(n, dtype=np.float64)
    
    nnz_count = 0
    
    # Parallelize over spatial cells
    for iz in prange(nz):
        for ir in prange(nr):
            idx = iz * nr + ir
            mat = material_map[iz, ir]
            
            # Build row for cell (iz, ir)
            # ... (matrix assembly logic)
            
            # Store row data
            row_start = idx * max_nnz_per_row
            # ... (store row indices, column indices, data)
    
    # Trim arrays to actual size
    # ... (truncate row_indices, col_indices, data to nnz_count)
    
    return row_indices[:nnz_count], col_indices[:nnz_count], data[:nnz_count], rhs
```

**Note:** Matrix assembly parallelization is complex because:
- Need to coordinate writes to shared arrays
- Can use thread-local storage and merge
- Alternative: Parallelize over rows (each thread builds its row)

**Simpler approach:** Use existing vectorized code for small-to-medium meshes, parallelize only for large meshes (>1000 cells).

---

### Phase 3: Parallel Fission Source (Week 2-3)

**Current code** (`_update_fission_source`) is already vectorized:
```python
fission_rate = np.sum(self.nu_sigma_f_map * self.flux, axis=2, keepdims=True)
chi_map = self.xs.chi[self.material_map, :]
self.source = chi_map * fission_rate / k_eff_safe
```

**Parallel version for very large problems:**
```python
@staticmethod
@njit(parallel=True, cache=True)
def _update_fission_source_parallel_numba(
    flux: np.ndarray,
    nu_sigma_f: np.ndarray,
    chi: np.ndarray,
    material_map: np.ndarray,
    source: np.ndarray,
    k_eff: float,
) -> None:
    """
    Parallel fission source update.
    """
    nz, nr, ng = flux.shape
    k_eff_safe = max(k_eff, 1e-6)
    
    for iz in prange(nz):
        for ir in prange(nr):
            mat = material_map[iz, ir]
            
            # Compute fission rate for this cell
            fission_rate = 0.0
            for g in range(ng):
                fission_rate += nu_sigma_f[mat, g] * flux[iz, ir, g]
            
            # Update source for all groups
            for g in range(ng):
                source[iz, ir, g] = chi[mat, g] * fission_rate / k_eff_safe
```

---

## Implementation Steps

### Step 1: Add Parallel Options (Day 1)

**File:** `smrforge/validation/models.py`

Add to `SolverOptions`:
```python
class SolverOptions(BaseModel):
    # ... existing fields ...
    parallel: bool = True  # Enable parallel execution
    parallel_group_solve: bool = True  # Parallel group solve
    parallel_spatial: bool = True  # Parallel spatial operations
    num_threads: Optional[int] = None  # Number of threads (None = auto)
```

### Step 2: Implement Parallel Group Solve (Days 2-5)

**File:** `smrforge/neutronics/solver.py`

1. Add helper method `_solve_group_with_source`:
   ```python
   def _solve_group_with_source(self, g: int, flux: np.ndarray) -> np.ndarray:
       """Solve single group with given flux (for parallel execution)."""
       self._update_scattering_source_parallel(g, flux)
       return self._solve_group(g)
   ```

2. Modify `solve_steady_state` to use parallel group solve:
   ```python
   # Replace:
   for g in range(self.ng):
       self._update_scattering_source(g)
       flux_g = self._solve_group(g)
       self.flux[:, :, g] = flux_g
   
   # With:
   if self.options.parallel_group_solve and self.ng > 1:
       self.flux = self._solve_groups_parallel_red_black(self.flux)
   else:
       # Original serial code
       for g in range(self.ng):
           ...
   ```

3. Add imports:
   ```python
   from concurrent.futures import ThreadPoolExecutor, as_completed
   from multiprocessing import cpu_count
   ```

### Step 3: Implement Parallel Spatial Operations (Days 6-10)

1. Add Numba parallel functions (as shown in Phase 2)
2. Modify `_update_scattering_source` to use parallel version
3. Add parallel fission source update (optional, for large problems)

### Step 4: Testing (Days 11-14)

**Test Plan:**
1. **Correctness tests:**
   - Compare serial vs. parallel results (should be identical or very close)
   - Test with 2, 4, 8, 16 energy groups
   - Test with various mesh sizes

2. **Performance tests:**
   - Measure speedup vs. number of cores
   - Test on different problem sizes
   - Profile to identify remaining bottlenecks

3. **Edge cases:**
   - Single energy group (should fallback to serial)
   - Single spatial cell (should fallback to serial)
   - Very large problems (test memory usage)

**Test file:** `tests/test_neutronics_parallel.py`

```python
def test_parallel_group_solve_correctness():
    """Test that parallel group solve gives same results as serial."""
    # ... implementation ...

def test_parallel_scaling():
    """Test speedup with number of cores."""
    # ... implementation ...

def test_parallel_fallback():
    """Test fallback to serial for single group/cell."""
    # ... implementation ...
```

---

## Expected Performance Gains

### Benchmarks (Estimated)

| Problem Size | Groups | Cells | Serial Time | Parallel Time (8 cores) | Speedup |
|--------------|--------|-------|-------------|-------------------------|---------|
| Small | 2 | 200 | 0.5s | 0.3s | 1.7x |
| Medium | 4 | 2,000 | 5.0s | 1.2s | 4.2x |
| Large | 8 | 20,000 | 60s | 12s | 5.0x |
| Very Large | 16 | 100,000 | 600s | 90s | 6.7x |

**Notes:**
- Speedup increases with number of groups (more parallel work)
- Speedup increases with problem size (more work per thread)
- Limited by Amdahl's Law (serial parts: matrix solve, source normalization)

### Scaling Characteristics

- **Ideal scaling:** Up to number of energy groups (limited parallelism)
- **Practical scaling:** 4-8x on 8-32 core CPUs
- **Bottleneck:** Sparse matrix solve (scipy.sparse) is serial
  - Future: Use PETSc or cuSOLVER for parallel linear solve

---

## Backwards Compatibility

**All parallelization features:**
- ✅ Default to serial if `parallel=False`
- ✅ Fallback to serial if Numba unavailable
- ✅ Fallback to serial for single group/cell
- ✅ Same API (no breaking changes)

**Configuration:**
```python
# Serial execution (backwards compatible)
options = SolverOptions(parallel=False)
solver = MultiGroupDiffusion(geometry, xs_data, options)

# Parallel execution (new feature)
options = SolverOptions(parallel=True, num_threads=8)
solver = MultiGroupDiffusion(geometry, xs_data, options)
```

---

## Future Enhancements

### Phase 4: Distributed Memory (MPI) - Future Work

For very large problems requiring multiple nodes:
- Use `mpi4py` for domain decomposition
- Distribute energy groups across MPI ranks
- Or distribute spatial domains across ranks
- Requires significant additional work

### Phase 5: GPU Acceleration - Future Work

For very large matrices:
- Use CuPy for matrix operations
- Use Numba CUDA for spatial loops
- Requires GPU hardware and additional development

---

## Risks and Mitigation

### Risk 1: Numba Compatibility Issues
**Mitigation:**
- Extensive testing with various NumPy versions
- Fallback to serial if Numba compilation fails
- Test on multiple platforms (Linux, Windows, macOS)

### Risk 2: Numerical Differences (Parallel vs. Serial)
**Mitigation:**
- Use red-black ordering to maintain convergence
- Add tolerance checks (allow small differences)
- Document expected behavior

### Risk 3: Thread Safety Issues
**Mitigation:**
- Use thread-local storage where needed
- Avoid shared state in parallel sections
- Use Numba's built-in thread safety (prange is safe)

---

## Summary

This plan provides a practical path to 4-8x speedup using Python + Numba, avoiding the complexity and development time of a Rust rewrite. The implementation is:

- **Incremental:** Can be done in phases
- **Low-risk:** Falls back to serial if issues arise
- **Backwards compatible:** No breaking changes
- **Maintainable:** Stays in Python ecosystem
- **Scalable:** Foundation for future MPI/GPU work

**Recommended timeline:** 2-3 weeks for Phase 1-3 implementation and testing.
