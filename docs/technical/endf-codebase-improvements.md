# Recommended Codebase Improvements Based on Mounted ENDF Files

## Analysis Summary

**Current State:**
- ✅ 557 valid ENDF files found in `/app/endf-data/neutrons-version.VIII.1/`
- ✅ File discovery and parsing working correctly
- ✅ Standard filename format: `n-ZZZ_Element_AAA.endf` (e.g., `n-092_U_235.endf`)
- ✅ Conversion function implemented but uses approximations

**Key Findings:**
- Cross-sections are being extracted successfully (3 energy points for U235 fission)
- Current conversion uses hardcoded values for `nu` (neutrons per fission) and `chi` (fission spectrum)
- Scattering matrix uses simplified downscattering model
- Missing extraction of ENDF-specific data (nu, chi, detailed scattering)

---

## Recommended Improvements

### 1. Extract nu (Neutrons per Fission) from ENDF Files ⭐ **HIGH PRIORITY**

**Current Issue:**
- Using hardcoded values: `nu = 2.5` for U235, `nu = 2.4` for U238
- ENDF files contain actual nu data that varies with energy

**ENDF Location:**
- MF=1, MT=452: Average number of neutrons per fission (nu-bar)
- MF=3, MT=456: Energy-dependent nu (nu(E))

**Recommended Changes:**

```python
# In convert_nuclide_to_material_xs() or new helper function
def extract_nu_from_endf(cache: NuclearDataCache, nuclide: Nuclide, 
                         group_structure: np.ndarray, temperature: float) -> np.ndarray:
    """
    Extract nu (neutrons per fission) from ENDF file.
    
    Returns:
        nu values for each energy group [n_groups]
    """
    try:
        # Try to get nu directly from ENDF (if parser supports it)
        # Fallback to energy-dependent nu if available
        # Otherwise use nuclide-specific defaults
        if nuclide.name == "U235":
            # U235: nu varies from ~2.4 (thermal) to ~2.6 (fast)
            nu_base = 2.5
        elif nuclide.name == "U238":
            # U238: nu varies from ~2.4 (thermal) to ~2.7 (fast)
            nu_base = 2.4
        else:
            nu_base = 2.5  # Default
        
        # Energy-dependent correction (simplified)
        # Fast neutrons produce more neutrons per fission
        nu = np.ones(len(group_structure) - 1) * nu_base
        # Add energy dependence if group structure available
        return nu
    except Exception:
        # Fallback to defaults
        return np.ones(len(group_structure) - 1) * 2.5
```

**Files to Modify:**
- `examples/complete_integration_example.py`: Update `convert_nuclide_to_material_xs()`
- `smrforge/core/reactor_core.py`: Add `get_nu()` method to `NuclearDataCache`
- `smrforge/core/endf_parser.py`: Add nu extraction capability

---

### 2. Extract chi (Fission Spectrum) from ENDF Files ⭐ **HIGH PRIORITY**

**Current Issue:**
- Using hardcoded Watt spectrum approximation
- ENDF files contain actual fission spectrum data

**ENDF Location:**
- MF=5: Fission spectrum (chi)
- MT=18: Fission spectrum for total fission
- Contains energy-dependent chi(E) data

**Recommended Changes:**

```python
def extract_chi_from_endf(cache: NuclearDataCache, nuclide: Nuclide,
                          group_structure: np.ndarray) -> np.ndarray:
    """
    Extract chi (fission spectrum) from ENDF file.
    
    Returns:
        chi values for each energy group [n_groups], normalized to sum=1
    """
    try:
        # Try to parse MF=5 from ENDF file
        # If not available, use nuclide-specific Watt spectrum
        from smrforge.core.constants import FISSION_SPECTRUM_PARAMS, watt_spectrum
        
        # Get Watt parameters for this nuclide
        key = f"{nuclide.name}_thermal"
        if key in FISSION_SPECTRUM_PARAMS:
            params = FISSION_SPECTRUM_PARAMS[key]
        else:
            params = {"a": 0.988, "b": 2.249}  # Default U235
        
        # Convert group boundaries to MeV and compute spectrum
        group_centers_mev = (group_structure[:-1] + group_structure[1:]) / 2 / 1e6
        chi = watt_spectrum(group_centers_mev, params["a"], params["b"])
        
        # Normalize
        chi = chi / np.sum(chi)
        return chi
    except Exception:
        # Fallback to hardcoded spectrum
        chi = np.zeros(len(group_structure) - 1)
        chi[0] = 0.6
        chi[1] = 0.3
        chi[2] = 0.08
        chi[3] = 0.015
        chi[4] = 0.004
        chi[5] = 0.001
        return chi / np.sum(chi)
```

**Files to Modify:**
- `examples/complete_integration_example.py`: Update `convert_nuclide_to_material_xs()`
- `smrforge/core/endf_parser.py`: Add MF=5 parsing for chi
- `smrforge/core/reactor_core.py`: Add `get_chi()` method

---

### 3. Improve Scattering Matrix Computation ⭐ **MEDIUM PRIORITY**

**Current Issue:**
- Using simplified downscattering model (80% same group, 15% next, 5% skip)
- ENDF files contain detailed scattering matrices

**ENDF Location:**
- MF=6: Energy-angle distributions
- Contains detailed scattering probability matrices

**Recommended Changes:**

```python
def compute_scattering_matrix_from_endf(cache: NuclearDataCache, nuclide: Nuclide,
                                       group_structure: np.ndarray, 
                                       temperature: float) -> np.ndarray:
    """
    Compute scattering matrix from ENDF file.
    
    Returns:
        Scattering matrix [n_groups, n_groups]
    """
    try:
        # Get elastic scattering cross-section
        energy, sigma_elastic = cache.get_cross_section(
            nuclide, "elastic", temperature
        )
        
        # For now, use improved downscattering model
        # Future: Parse MF=6 for detailed angular distributions
        n_groups = len(group_structure) - 1
        sigma_s = np.zeros((n_groups, n_groups))
        
        # Collapse elastic XS to groups
        elastic_mg = collapse_to_multigroup(energy, sigma_elastic, group_structure)
        
        for g in range(n_groups):
            # Improved model based on energy
            # Fast groups: more downscattering
            # Thermal groups: mostly same group
            if g < n_groups // 3:  # Fast groups
                sigma_s[g, g] = 0.7 * elastic_mg[g]
                if g < n_groups - 1:
                    sigma_s[g, g + 1] = 0.25 * elastic_mg[g]
                if g < n_groups - 2:
                    sigma_s[g, g + 2] = 0.05 * elastic_mg[g]
            else:  # Thermal groups
                sigma_s[g, g] = 0.9 * elastic_mg[g]
                if g < n_groups - 1:
                    sigma_s[g, g + 1] = 0.1 * elastic_mg[g]
        
        return sigma_s
    except Exception:
        # Fallback to simple model
        return create_simple_scattering_matrix(n_groups)
```

**Files to Modify:**
- `examples/complete_integration_example.py`: Update scattering computation
- `smrforge/core/endf_parser.py`: Add MF=6 parsing (future enhancement)

---

### 4. Add Support for More Reactions ⭐ **MEDIUM PRIORITY**

**Current Support:**
- total, fission, capture, elastic

**Additional Reactions Available in ENDF:**
- n,2n (MT=16)
- n,3n (MT=17)
- n,alpha (MT=107)
- n,p (MT=103)
- Inelastic scattering (MT=4)

**Recommended Changes:**

```python
# In convert_nuclide_to_material_xs(), add support for:
reactions_to_try = ['total', 'fission', 'capture', 'elastic', 'n,2n', 'n,alpha']

# Update absorption calculation:
# sigma_a = capture + fission + n,2n + n,alpha + ...
```

**Files to Modify:**
- `examples/complete_integration_example.py`: Expand reaction list
- `smrforge/core/reactor_core.py`: Add reaction name mappings

---

### 5. Improve Unit Conversion and Atom Density Handling ⭐ **MEDIUM PRIORITY**

**Current Issue:**
- Atom densities are hardcoded in composition dict
- Unit conversion might not account for all nuclides properly

**Recommended Changes:**

```python
def compute_material_cross_sections(
    xs_df: pl.DataFrame,
    composition: Dict[str, float],  # atoms/barn-cm
    material_density: Optional[float] = None,  # g/cm³ (for validation)
    n_groups: int = 8,
) -> CrossSectionData:
    """
    Improved version with better unit handling.
    
    Args:
        composition: Dict of {nuclide: atom_density [atoms/barn-cm]}
        material_density: Optional physical density [g/cm³] for validation
    """
    # Validate composition sums to reasonable value
    total_density = sum(composition.values())
    
    # Convert from barns to 1/cm
    # sigma [1/cm] = sigma [barns] * N [atoms/barn-cm]
    # Note: 1 barn = 1e-24 cm², so atoms/barn-cm = atoms * 1e24 / cm³
    
    # For each material, use appropriate density
    # Fuel: use composition density
    # Reflector: use graphite density (~1.7 g/cm³ → ~0.085 atoms/barn-cm)
```

**Files to Modify:**
- `examples/complete_integration_example.py`: Improve unit conversion
- Add validation for physical densities

---

### 6. Add Caching for Converted Cross-Sections ⭐ **LOW PRIORITY**

**Current Issue:**
- Conversion happens every time, even if inputs haven't changed

**Recommended Changes:**

```python
# Cache converted CrossSectionData objects
# Key: hash of (xs_df hash, composition, n_groups, group_structure)
# Store in NuclearDataCache or separate cache

@lru_cache(maxsize=10)
def convert_nuclide_to_material_xs_cached(
    xs_df_hash: str,
    composition_str: str,
    n_groups: int,
    group_structure_hash: str,
) -> CrossSectionData:
    # ... conversion logic
```

**Files to Modify:**
- `examples/complete_integration_example.py`: Add caching decorator
- Consider moving to `smrforge/core/reactor_core.py` as a utility function

---

### 7. Add Better Error Handling and Validation ⭐ **MEDIUM PRIORITY**

**Current Issue:**
- Conversion fails silently in some cases
- No validation of resulting cross-sections

**Recommended Changes:**

```python
def convert_nuclide_to_material_xs(...) -> CrossSectionData:
    # ... conversion logic ...
    
    # Validate results
    if np.any(sigma_t < 0):
        raise ValueError("Negative total cross-section found")
    if np.any(sigma_a > sigma_t):
        raise ValueError("Absorption exceeds total cross-section")
    if np.any(sigma_f > sigma_a):
        raise ValueError("Fission exceeds absorption cross-section")
    
    # Check chi normalization
    for m in range(n_materials):
        if np.any(sigma_f[m, :] > 0):
            chi_sum = np.sum(chi[m, :])
            if not np.isclose(chi_sum, 1.0, rtol=1e-3):
                raise ValueError(f"chi for material {m} doesn't sum to 1.0: {chi_sum}")
    
    return CrossSectionData(...)
```

**Files to Modify:**
- `examples/complete_integration_example.py`: Add validation
- `smrforge/validation/data_validation.py`: Add cross-section validation helpers

---

### 8. Optimize DataFrame Operations ⭐ **LOW PRIORITY**

**Current Issue:**
- Multiple filter operations on DataFrame
- Could be optimized with better Polars usage

**Recommended Changes:**

```python
# Instead of filtering multiple times:
for g in range(n_groups):
    group_data = nuc_data.filter(pl.col("group") == g)
    total_xs = group_data.filter(pl.col("reaction") == "total")
    # ...

# Use pivot or groupby once:
pivoted = nuc_data.pivot(
    values="xs", index="group", columns="reaction"
)
# Then access: pivoted["total"][g]
```

**Files to Modify:**
- `examples/complete_integration_example.py`: Optimize DataFrame operations

---

## Implementation Priority

### Phase 1: Critical Improvements (Do First)
1. ✅ Extract nu from ENDF files (or at least use energy-dependent values)
2. ✅ Extract chi from ENDF files (or use proper Watt spectrum)
3. ✅ Add validation to conversion function

### Phase 2: Important Enhancements
4. ✅ Improve scattering matrix computation
5. ✅ Better unit conversion and density handling
6. ✅ Add support for more reactions

### Phase 3: Optimization
7. ✅ Add caching for converted cross-sections
8. ✅ Optimize DataFrame operations

---

## Files to Create/Modify

### New Files
- `smrforge/core/endf_extractors.py`: Helper functions for extracting nu, chi, etc. from ENDF
- `tests/test_endf_conversion.py`: Tests for conversion function

### Files to Modify
- `examples/complete_integration_example.py`: Improve `convert_nuclide_to_material_xs()`
- `smrforge/core/reactor_core.py`: Add methods for nu, chi extraction
- `smrforge/core/endf_parser.py`: Add MF=5 (chi) and MF=1 (nu) parsing
- `smrforge/core/constants.py`: Add more fission spectrum parameters

---

## Testing Recommendations

1. **Test with actual ENDF files:**
   - Verify nu values match ENDF data
   - Verify chi spectrum matches ENDF data
   - Compare converted cross-sections with reference values

2. **Test edge cases:**
   - Missing reactions
   - Missing nuclides
   - Invalid compositions
   - Extreme group structures

3. **Performance testing:**
   - Measure conversion time for large datasets
   - Test caching effectiveness

---

## Notes

- The current implementation works but uses approximations
- ENDF files contain much more detailed data than currently used
- Priority should be on extracting nu and chi, as these significantly affect k_eff
- Scattering matrix improvements can come later (less critical for initial results)
- Consider using external libraries (SANDY, endf-parserpy) for complex extractions if needed

