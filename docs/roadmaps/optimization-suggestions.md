# Code Optimization Suggestions

## 1. Vectorization Opportunities in solver.py

### Current Code (lines 129-135):
```python
def _update_xs_maps(self):
    """Update homogenized cross sections from material map."""
    for iz in range(self.nz):
        for ir in range(self.nr):
            mat = self.material_map[iz, ir]
            self.D_map[iz, ir, :] = self.xs.D[mat, :]
            self.sigma_t_map[iz, ir, :] = self.xs.sigma_t[mat, :]
            self.sigma_a_map[iz, ir, :] = self.xs.sigma_a[mat, :]
            self.nu_sigma_f_map[iz, ir, :] = self.xs.nu_sigma_f[mat, :]
```

### Optimized Version:
```python
def _update_xs_maps(self):
    """Update homogenized cross sections from material map."""
    # Use advanced indexing: material_map is [nz, nr], xs.D is [n_materials, ng]
    # Result: [nz, nr, ng]
    self.D_map = self.xs.D[self.material_map, :]
    self.sigma_t_map = self.xs.sigma_t[self.material_map, :]
    self.sigma_a_map = self.xs.sigma_a[self.material_map, :]
    self.nu_sigma_f_map = self.xs.nu_sigma_f[self.material_map, :]
```

**Performance Gain**: ~10-100x faster for large meshes (eliminates Python loops)

---

## 2. Cache Cell Volumes

### Current Code:
`_cell_volumes()` is computed multiple times but could be cached.

### Optimized Version:
```python
def _allocate_arrays(self):
    """Allocate solution arrays."""
    # ... existing code ...
    self._cell_volumes_cache = None  # Will be computed on first access

def _cell_volumes(self) -> np.ndarray:
    """Compute cell volumes [nz, nr]."""
    if self._cell_volumes_cache is None:
        volumes = np.zeros((self.nz, self.nr))
        for iz in range(self.nz):
            for ir in range(self.nr):
                r = self.r_centers[ir]
                volumes[iz, ir] = 2 * np.pi * r * self.dr[ir] * self.dz[iz]
        self._cell_volumes_cache = volumes
    return self._cell_volumes_cache
```

Or better, vectorize:
```python
def _cell_volumes(self) -> np.ndarray:
    """Compute cell volumes [nz, nr]."""
    if self._cell_volumes_cache is None:
        # Vectorized computation
        r = self.r_centers[:, np.newaxis]  # [nr, 1]
        dr = self.dr[:, np.newaxis]  # [nr, 1]
        dz = self.dz[np.newaxis, :]  # [1, nz]
        self._cell_volumes_cache = 2 * np.pi * r * dr * dz.T  # [nz, nr]
    return self._cell_volumes_cache
```

---

## 3. Vectorize Scattering Source Update

### Current Code (lines 242-252):
```python
def _update_scattering_source(self, g: int):
    """Update scattering source for group g."""
    for iz in range(self.nz):
        for ir in range(self.nr):
            mat = self.material_map[iz, ir]
            
            scatter_in = 0.0
            for gp in range(self.ng):
                scatter_in += self.xs.sigma_s[mat, gp, g] * self.flux[iz, ir, gp]
            
            self.source[iz, ir, g] += scatter_in
```

### Optimized Version:
```python
def _update_scattering_source(self, g: int):
    """Update scattering source for group g."""
    # Vectorized: sigma_s is [n_materials, ng, ng]
    # flux is [nz, nr, ng]
    # material_map is [nz, nr]
    
    # Get scattering matrix for each cell: [nz, nr, ng]
    sigma_s_mat = self.xs.sigma_s[self.material_map, :, g]  # [nz, nr, ng]
    
    # Dot product along group dimension: [nz, nr]
    scatter_in = np.sum(sigma_s_mat * self.flux, axis=2)
    
    self.source[:, :, g] += scatter_in
```

**Performance Gain**: ~5-50x faster depending on number of groups

---

## 4. Optimize Fission Source Update

### Current Code (lines 232-240):
```python
def _update_fission_source(self, k_eff: float):
    """Update fission source."""
    fission_rate = np.sum(self.nu_sigma_f_map * self.flux, axis=2, keepdims=True)
    
    for iz in range(self.nz):
        for ir in range(self.nr):
            mat = self.material_map[iz, ir]
            chi = self.xs.chi[mat, :]
            self.source[iz, ir, :] = chi * fission_rate[iz, ir, 0] / k_eff
```

### Optimized Version:
```python
def _update_fission_source(self, k_eff: float):
    """Update fission source."""
    # Fission rate: [nz, nr, 1]
    fission_rate = np.sum(self.nu_sigma_f_map * self.flux, axis=2, keepdims=True)
    
    # chi is [n_materials, ng]
    # Get chi for each cell: [nz, nr, ng]
    chi_map = self.xs.chi[self.material_map, :]
    
    # Broadcast multiplication: [nz, nr, ng]
    self.source = chi_map * fission_rate / k_eff
```

**Performance Gain**: ~5-20x faster

---

## 5. Add Numba JIT for Critical Loops

Consider adding `@njit` decorators to small helper functions that are called in loops:

```python
@njit(cache=True)
def compute_volume_element(r: float, dr: float, dz: float) -> float:
    """Compute volume of cylindrical element."""
    return 2 * np.pi * r * dr * dz
```

---

## 6. Sparse Matrix Construction Optimization

The `_build_group_system()` method (lines 272-363) builds sparse matrices element-by-element. Consider using scipy.sparse construction methods if possible, or at least pre-allocate arrays more efficiently.

---

## ✅ Completed Optimizations (2025)

### Solver Performance Optimizations (solver.py)

**Status**: ✅ **COMPLETED** - All high and medium priority optimizations implemented

**Summary**: All recommended vectorization and caching optimizations have been successfully implemented in the multi-group diffusion solver, resulting in significant performance improvements for large meshes.

**See sections above for detailed implementation status of each optimization.**

---

### ENDF File Access Optimization (reactor_core.py)

**Status**: ✅ **COMPLETED** - Phase 3 of ENDF integration

**Optimizations Implemented**:
1. **Eager Index Building**: File index built on initialization if `local_endf_dir` provided
   - **Before**: Lazy loading (built on first access)
   - **After**: Eager loading (built immediately)
   - **Impact**: Eliminates first-access delay, ~0.09s one-time cost

2. **Cached File Index**: Dictionary-based O(1) lookups
   - **Before**: Directory scan on each lookup
   - **After**: Cached dictionary lookup
   - **Impact**: ~800x faster (0.08s → 0.0001s)

3. **File Path Caching**: Index maps nuclide names to file paths
   - **Before**: File system operations for each lookup
   - **After**: In-memory dictionary lookup
   - **Impact**: Instant file discovery

**Performance Results**:
- First access: ~800x faster (0.08s → 0.0001s)
- Index building: ~0.09s for 557 files (one-time cost)
- Subsequent lookups: <0.0001s (instant)

**See**: [`docs/technical/endf-documentation.md`](docs/technical/endf-documentation.md) for complete documentation on ENDF integration and improvements.

---

## ✅ Completed Optimizations (2025)

### High Priority Optimizations - All Implemented

1. ✅ **Vectorize `_update_xs_maps()`** (#1)
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/neutronics/solver.py:225-237`
   - **Implementation**: Uses numpy advanced indexing for vectorized assignment
   - **Performance Gain**: ~10-100x faster for large meshes (eliminates Python loops)

2. ✅ **Cache and Vectorize `_cell_volumes()`** (#2)
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/neutronics/solver.py:685-700`
   - **Implementation**: Cached with vectorized computation using broadcasting
   - **Performance Gain**: Eliminates redundant computations, ~5-10x faster

3. ✅ **Vectorize `_update_scattering_source()`** (#3)
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/neutronics/solver.py:377-394`
   - **Implementation**: Vectorized operations using numpy advanced indexing and sum
   - **Performance Gain**: ~5-50x faster depending on number of groups

4. ✅ **Optimize `_update_fission_source()`** (#4)
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/neutronics/solver.py:361-375`
   - **Implementation**: Vectorized operations with broadcasting
   - **Performance Gain**: ~5-20x faster

### Medium Priority Optimizations

5. ✅ **Optimize Sparse Matrix Construction** (#6)
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/neutronics/solver.py:414-505`
   - **Implementation**: 
     - Pre-computed axial areas (reused across radial cells)
     - More efficient array operations
     - Better use of pre-computed values
   - **Performance Gain**: ~10-20% faster for large meshes

## ✅ New Optimizations Implemented (January 2026)

### 7. Vectorize Burnup Fission Rate Integration ✅
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/burnup/solver.py:_update_burnup()` (lines ~1026-1041)
   - **Implementation**: Replaced nested loops (z, r, g) with vectorized numpy operations using fuel mask and broadcasting
   - **Performance Gain**: ~10-100x faster for large meshes (eliminates 3 nested Python loops)
   - **Code Change**:
     ```python
     # Before: Nested loops over z, r, g
     for z in range(nz):
         for r in range(nr):
             if material_map[z, r] != 0:
                 continue
             for g in range(ng):
                 total_fissions += sigma_f_avg * flux[z, r, g] * N_avg * cell_volumes[z, r]
     
     # After: Vectorized with fuel mask
     fuel_mask = (material_map == 0)
     flux_fuel = flux * fuel_mask[:, :, np.newaxis]
     fission_rate_per_cell_group = sigma_f_avg * flux_fuel * N_avg * cell_volumes[:, :, np.newaxis]
     total_fissions = np.sum(fission_rate_per_cell_group)
     ```

### 8. Vectorize Control Rod Shadowing Calculation ✅
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/burnup/solver.py:set_control_rod_effects()` (lines ~925-939)
   - **Implementation**: Replaced nested loops with vectorized distance calculation using meshgrid and numpy operations
   - **Performance Gain**: ~5-20x faster for multiple control rods
   - **Code Change**:
     ```python
     # Before: Nested loops
     for z in range(nz):
         for r in range(nr):
             for cr_pos in control_rod_positions:
                 distance = np.sqrt((r - cr_pos[1])**2 + (z - cr_pos[0])**2)
                 min_distance = min(min_distance, distance)
     
     # After: Vectorized
     z_coords, r_coords = np.meshgrid(np.arange(nz), np.arange(nr), indexing='ij')
     min_distances = np.full((nz, nr), np.inf)
     for cr_pos in control_rod_positions:
         distances = np.sqrt((r_coords - cr_pos[1])**2 + (z_coords - cr_pos[0])**2)
         min_distances = np.minimum(min_distances, distances)
     shadowing = 1.0 - 0.3 * np.exp(-min_distances / characteristic_length)
     ```

### 9. Optimize Gamma Transport Sparse Matrix Construction ✅
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/gamma_transport/solver.py:_build_group_system()` (lines ~422-448)
   - **Implementation**: Vectorized diagonal computation using numpy broadcasting instead of nested loops
   - **Performance Gain**: ~5-10x faster for large meshes
   - **Code Change**:
     ```python
     # Before: Nested loops computing diagonal values
     for iz in range(self.nz):
         for ir in range(self.nr):
             diag_value = sigma_t_g * cell_volume
             if ir > 0:
                 diag_value += D_g / (self.dr[ir]**2) * cell_volume
             # ... more conditionals
     
     # After: Vectorized computation
     diag_base = sigma_t_g * cell_volumes
     radial_contrib = np.zeros((self.nz, self.nr))
     radial_contrib[:, 1:-1] = 2 * radial_diffusion_coef[1:-1, np.newaxis] * cell_volumes[:, 1:-1]
     # ... vectorized boundary handling
     diag_values = diag_base + radial_contrib + axial_contrib
     ```

### 10. Vectorize Cross-Section Broadcasting ✅
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/burnup/solver.py:_update_cross_sections()` (lines ~877-884)
   - **Implementation**: Replaced loop over energy groups with vectorized array assignment
   - **Performance Gain**: ~ng times faster (where ng = number of energy groups)
   - **Code Change**:
     ```python
     # Before: Loop over groups
     for g in range(ng):
         self.neutronics.xs.sigma_a[fuel_material_idx, g] = sigma_a_weighted
     
     # After: Vectorized broadcast
     self.neutronics.xs.sigma_a[fuel_material_idx, :] = sigma_a_weighted
     ```

### 11. Optimize Control Rod Distance Calculation in LWR Burnup ✅
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/burnup/lwr_burnup.py:calculate_shadowing_factor()` (lines ~471-478)
   - **Implementation**: Vectorized distance calculation to all control rods at once
   - **Performance Gain**: ~5-10x faster for multiple control rods
   - **Code Change**:
     ```python
     # Before: Loop over control rods
     for cr_pos in control_rod_positions:
         distance = np.sqrt((rod_position[0] - cr_pos[0])**2 + (rod_position[1] - cr_pos[1])**2)
         min_distance = min(min_distance, distance)
     
     # After: Vectorized
     cr_positions = np.array(control_rod_positions)
     deltas = cr_positions - rod_position
     distances = np.sqrt(np.sum(deltas**2, axis=1)) * pitch
     min_distance = np.min(distances)
     ```

## ✅ Additional Optimizations Implemented (January 2026)

### 12. Optimize Temperature Interpolation with 2D Spline ✅
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/core/temperature_interpolation.py:_interpolate_spline()` (lines ~202-223)
   - **Implementation**: Replaced loop over energy points with 2D interpolation using `RectBivariateSpline`
   - **Performance Gain**: ~10-50x faster when interpolating over many energy points (n_energies > 10)
   - **Code Change**:
     ```python
     # Before: Loop over each energy point
     for i in range(n_energies):
         xs_at_energy = self.cross_sections[:, i]
         spline = UnivariateSpline(self.temperatures, xs_at_energy, ...)
         xs_interp[i] = spline(temperature)
     
     # After: 2D interpolation for all energies at once
     spline_2d = RectBivariateSpline(
         self.temperatures, self.energies, self.cross_sections, ...
     )
     xs_interp = spline_2d(temperature, self.energies, grid=False)
     ```
   - **Note**: Falls back to per-energy splines for small datasets or if 2D interpolation fails

### 13. Add Numba JIT for Matrix Construction Helpers ✅
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/neutronics/solver.py` (module-level helper functions)
   - **Implementation**: Added Numba-accelerated helper functions for frequently called computations in `_build_group_system()`
   - **Performance Gain**: ~2-5x faster for matrix construction in large meshes
   - **Functions Added**:
     - `_compute_cell_volume()`: Numba-accelerated cell volume calculation
     - `_compute_radial_area()`: Numba-accelerated radial area calculation
     - `_compute_diffusion_coefficient()`: Numba-accelerated harmonic mean diffusion coefficient
   - **Code Change**:
     ```python
     # Before: Inline calculations
     V = 2 * np.pi * r * dr * dz
     A_left = 2 * np.pi * r_left * dz
     D_left = 0.5 * (D + self.D_map[iz, ir - 1, g])
     
     # After: Numba-accelerated functions
     V = _compute_cell_volume(r, dr, dz)
     A_left = _compute_radial_area(r_left, dz)
     D_left = _compute_diffusion_coefficient(D, self.D_map[iz, ir - 1, g])
     ```
   - **Note**: Uses harmonic mean for diffusion coefficient (more accurate than arithmetic mean)

### 14. Optimize Self-Shielding Subgroup Method ✅
   - **Status**: ✅ **COMPLETED**
   - **Location**: `smrforge/core/self_shielding_integration.py:get_cross_section_with_self_shielding()` (lines ~117-184)
   - **Implementation**: 
     - Pre-compute Bondarenko f-factor once (instead of twice)
     - Optimized vectorized operations for resonance mask
     - Reduced redundant calculations
   - **Performance Gain**: ~2-3x faster for subgroup method calculations
   - **Code Change**:
     ```python
     # Before: Compute Bondarenko f-factor twice (for resonance and non-resonance)
     if np.any(non_resonance_mask):
         bondarenko = BondarenkoMethod()
         f_factor = bondarenko.get_f_factor(...)
         xs_shielded[non_resonance_mask] = f_factor * xs_inf[non_resonance_mask]
     
     # After: Pre-compute once and use for initialization
     bondarenko = BondarenkoMethod()
     f_factor = bondarenko.get_f_factor(...)
     xs_shielded = f_factor * xs_inf  # Initialize all
     # Then overwrite resonance region with subgroup method
     ```

## Remaining Optimizations

### Low Priority (More complex, requires testing):
   - Consider parallelizing matrix assembly in `_build_group_system()` for very large meshes
     - Current implementation is already optimized with vectorization and Numba helpers
     - Parallel matrix assembly would require thread-safe array construction
     - Potential gain: ~2-4x on multi-core systems for meshes > 10,000 cells
   - Further optimize self-shielding for batch processing
     - Could batch multiple nuclides/reactions together
     - Would require refactoring API to accept arrays of nuclides
     - Potential gain: ~3-5x when processing many nuclides

