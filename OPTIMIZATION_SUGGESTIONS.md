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

## Implementation Priority

1. **High Priority** (Easy, High Impact):
   - Vectorize `_update_xs_maps()` (#1)
   - Vectorize `_update_scattering_source()` (#3)
   - Vectorize `_update_fission_source()` (#4)

2. **Medium Priority**:
   - Cache `_cell_volumes()` (#2)
   - Optimize sparse matrix construction (#6)

3. **Low Priority** (More complex):
   - Add Numba JIT decorators (#5) - Test to ensure compatibility first

