# Advanced Capabilities Gaps Analysis

**Date:** January 1, 2026  
**Focus:** Gaps in advanced capabilities for `reactor_core.py` and geometry functions  
**Scope:** Missing advanced features that would enhance reactor simulation capabilities

---

## Executive Summary

This analysis examines `smrforge/core/reactor_core.py` and geometry functions to identify gaps in advanced capabilities. While the codebase has strong foundational features, several advanced capabilities are missing that would enhance reactor simulation, design optimization, and analysis workflows.

---

## 🔴 HIGH PRIORITY Gaps in `reactor_core.py`

### 1. **Advanced Cross-Section Processing** ⚠️

**Current State:**
- ✅ Basic cross-section fetching (fission, capture, elastic, total)
- ✅ Temperature-dependent Doppler broadening
- ✅ Multi-group collapse with flux weighting
- ✅ Support for multiple nuclear data libraries (ENDF/B-VIII.0, VIII.1, JEFF-3.3, JENDL-5.0)

**Missing Advanced Capabilities:**

#### 1.1 **Resonance Self-Shielding Treatment**
- ❌ **No resonance self-shielding corrections** for heterogeneous geometries
- ❌ **No Bondarenko factors** (f-factors) for resonance treatment
- ❌ **No subgroup method** for resonance treatment
- ❌ **No equivalence theory** (Bell-Wigner) implementation

**Impact:** Cross-sections in fuel regions may be inaccurate for heterogeneous geometries (e.g., fuel pins in moderator). Critical for accurate k-eff calculations.

**Recommendation:** 🔴 **HIGH PRIORITY** - Essential for accurate reactor physics calculations

#### 1.2 **Advanced Scattering Matrix Processing**
- ✅ Basic scattering matrix computation exists (energy-dependent downscattering)
- ✅ **S(α,β) thermal scattering law** parser implemented (`thermal_scattering_parser.py`)
- ⚠️ **TSL integration** - Parser exists and can compute thermal scattering cross-sections, but integration with neutronics solver is unclear
- ❌ **No MF=6 (energy-angle distributions)** parsing
- ❌ **No anisotropic scattering** (P0, P1, P2, etc. Legendre moments)
- ❌ **No thermal upscattering** treatment in scattering matrix
- ⚠️ **TSL in scattering matrix** - `compute_improved_scattering_matrix()` has `use_tsl` parameter but may not be fully utilized

**Impact:** Scattering physics may be oversimplified, especially anisotropic scattering. TSL data exists but may not be fully integrated into neutronics calculations.

**Recommendation:** 🟡 **MEDIUM PRIORITY** - TSL parser exists, but verify full integration with neutronics solver and add anisotropic scattering support

#### 1.3 **Advanced Fission Data**
- ⚠️ Basic chi (fission spectrum) extraction exists
- ❌ **No MF=5 (fission product yield)** parsing (independent/cumulative yields)
- ❌ **No delayed neutron data** (MF=1, MT=455) parsing
- ❌ **No prompt/delayed chi separation**
- ❌ **No nu-bar (average neutrons per fission)** energy dependence

**Impact:** Cannot perform accurate burnup calculations or transient analysis with delayed neutrons.

**Recommendation:** 🔴 **HIGH PRIORITY** - Required for burnup and transient analysis

#### 1.4 **Uncertainty Quantification in Nuclear Data**
- ❌ **No covariance data** (MF=33) parsing
- ❌ **No uncertainty propagation** in cross-sections
- ❌ **No sensitivity coefficients** for nuclear data uncertainties
- ❌ **No TMC (Total Monte Carlo)** support

**Impact:** Cannot quantify uncertainty in results due to nuclear data uncertainties.

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Important for uncertainty quantification workflows

---

### 2. **Advanced Multi-Group Processing** ⚠️

**Current State:**
- ✅ Basic multi-group collapse with flux weighting
- ✅ 1/E weighting fallback
- ✅ Trapezoidal rule integration

**Missing Advanced Capabilities:**

#### 2.1 **Advanced Group Collapse Methods**
- ❌ **No fine-to-coarse group mapping** with preservation of reaction rates
- ❌ **No superhomogenization (SPH) method** for heterogeneous regions
- ❌ **No generalized equivalence theory** for group collapse
- ❌ **No energy condensation** with reaction rate preservation

**Impact:** Multi-group cross-sections may not preserve reaction rates accurately.

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Important for accurate multi-group calculations

#### 2.2 **Advanced Flux Weighting**
- ⚠️ Basic flux weighting exists
- ❌ **No adjoint flux weighting** for importance-weighted collapse
- ❌ **No spectrum weighting** (e.g., Maxwellian, 1/E, Watt spectrum)
- ❌ **No multi-spectrum weighting** (e.g., fast + thermal)
- ❌ **No critical spectrum** calculation for weighting

**Impact:** Group-averaged cross-sections may not be optimal for specific applications.

**Recommendation:** 🟢 **LOW PRIORITY** - Nice to have for specialized applications

---

### 3. **Advanced Nuclear Data Management** ⚠️

**Current State:**
- ✅ Zarr-based caching system
- ✅ In-memory cache for hot data
- ✅ Local ENDF file discovery
- ✅ Multiple parser backends (endf-parserpy, SANDY, built-in)

**Missing Advanced Capabilities:**

#### 3.1 **Advanced Caching Strategies**
- ❌ **No distributed caching** (e.g., Redis, Memcached)
- ❌ **No cache invalidation** strategies for updated ENDF files
- ❌ **No cache compression** optimization (currently uses default zlib)
- ❌ **No cache statistics** (hit rate, size, etc.)

**Impact:** Performance may be suboptimal for large-scale calculations or distributed computing.

**Recommendation:** 🟢 **LOW PRIORITY** - Optimization opportunity

#### 3.2 **Advanced File Management**
- ⚠️ Basic file discovery exists
- ❌ **No automatic ENDF file download** (users must download manually)
- ❌ **No file integrity verification** (checksums, validation)
- ❌ **No incremental updates** for ENDF libraries
- ❌ **No version management** for multiple library versions

**Impact:** User experience could be improved with automatic downloads and updates.

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Improves usability

---

### 4. **Advanced Data Structures** ⚠️

**Current State:**
- ✅ Polars DataFrames for multi-group cross-sections
- ✅ NumPy arrays for continuous-energy data
- ✅ Basic Nuclide dataclass

**Missing Advanced Capabilities:**

#### 4.1 **Advanced Nuclide Management**
- ❌ **No nuclide inventory tracking** (atom densities, concentrations)
- ❌ **No nuclide decay chain** representation
- ❌ **No metastable state handling** (beyond basic m parameter)
- ❌ **No isomeric branching** ratios

**Impact:** Cannot track isotope evolution during burnup or decay.

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Required for burnup calculations

#### 4.2 **Advanced Cross-Section Data Structures**
- ⚠️ Basic (energy, xs) tuple format
- ❌ **No uncertainty information** in data structures
- ❌ **No temperature interpolation** (only Doppler broadening)
- ❌ **No interpolation methods** (linear, log-log, spline)
- ❌ **No extrapolation** strategies for out-of-range energies

**Impact:** Limited flexibility in cross-section usage and interpolation.

**Recommendation:** 🟢 **LOW PRIORITY** - Enhancement opportunity

---

## 🔴 HIGH PRIORITY Gaps in Geometry Functions

### 1. **Advanced Geometry Representations** ⚠️

**Current State:**
- ✅ Prismatic core (hexagonal blocks)
- ✅ Pebble bed core
- ✅ Basic mesh generation (2D/3D)
- ✅ Control rod geometry
- ✅ Assembly management

**Missing Advanced Capabilities:**

#### 1.1 **Advanced Core Types**
- ❌ **No annular core** support (beyond enum definition)
- ❌ **No hybrid core** implementation (beyond enum definition)
- ❌ **No fast reactor geometries** (e.g., sodium-cooled, lead-cooled)
- ❌ **No molten salt reactor** geometries
- ❌ **No light water reactor (LWR)** geometries (PWR, BWR) - **CRITICAL GAP**
- ❌ **No small modular reactor (SMR)** specific geometries (LWR-based)
- ❌ **No heavy water reactor (CANDU)** geometries
- ❌ **No research reactor** geometries

**Impact:** Limited to HTGR designs only (~5% of global nuclear capacity). Missing LWR support (PWR/BWR represent ~85% of global capacity) severely limits applicability.

**Recommendation:** 🔴 **HIGH PRIORITY** - Critical for broad industry applicability

**See:** `docs/status/missing-reactor-types-analysis.md` for detailed analysis of all missing reactor types

#### 1.2 **Advanced Lattice Structures**
- ⚠️ Hexagonal, square, triangular lattices defined
- ❌ **No rectangular lattices** (e.g., PWR fuel assemblies)
- ❌ **No irregular lattices** (non-uniform spacing)
- ❌ **No nested lattices** (lattice within lattice)
- ❌ **No rotated lattices** (arbitrary orientation)

**Impact:** Cannot model many reactor types (PWR, BWR, etc.).

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Important for broader applicability

#### 1.3 **Advanced Geometry Primitives**
- ⚠️ Basic shapes (hexagons, circles, rectangles)
- ❌ **No complex CSG operations** (union, intersection, difference)
- ❌ **No NURBS surfaces** for curved geometries
- ❌ **No parametric surfaces** (splines, Bezier curves)
- ❌ **No boolean operations** on complex shapes

**Impact:** Limited to simple geometric shapes.

**Recommendation:** 🟢 **LOW PRIORITY** - Specialized applications

---

### 2. **Advanced Mesh Generation** ⚠️

**Current State:**
- ✅ 2D/3D mesh generation
- ✅ Adaptive refinement
- ✅ Mesh quality evaluation
- ✅ Structured/unstructured/hybrid meshes

**Missing Advanced Capabilities:**

#### 2.1 **Advanced Mesh Refinement**
- ⚠️ Basic adaptive refinement exists
- ❌ **No error-based refinement** (using solution error estimates)
- ❌ **No gradient-based refinement** (refine where gradients are high)
- ❌ **No physics-based refinement** (e.g., refine near fuel/moderator interfaces)
- ❌ **No anisotropic refinement** (different refinement in different directions)

**Impact:** Meshes may not be optimal for specific physics problems.

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Improves accuracy and efficiency

#### 2.2 **Advanced Mesh Types**
- ⚠️ Basic structured/unstructured/hybrid
- ❌ **No polyhedral meshes** (for complex geometries)
- ❌ **No cut-cell meshes** (for immersed boundary methods)
- ❌ **No hanging node meshes** (for non-conforming refinement)
- ❌ **No meshless methods** (SPH, RBF, etc.)

**Impact:** Limited mesh flexibility for complex geometries.

**Recommendation:** 🟢 **LOW PRIORITY** - Specialized applications

#### 2.3 **Advanced Mesh Operations**
- ⚠️ Basic mesh generation and conversion
- ❌ **No mesh coarsening** (reverse of refinement)
- ❌ **No mesh smoothing** (Laplacian, optimization-based)
- ❌ **No mesh optimization** (improve quality without changing topology)
- ❌ **No mesh adaptation** during simulation (dynamic refinement)

**Impact:** Cannot improve mesh quality after generation.

**Recommendation:** 🟢 **LOW PRIORITY** - Enhancement opportunity

---

### 3. **Advanced Geometry-Physics Coupling** ⚠️

**Current State:**
- ✅ Basic material region definitions
- ✅ Temperature field storage
- ✅ Power density tracking

**Missing Advanced Capabilities:**

#### 3.1 **Advanced Material Mapping**
- ⚠️ Basic material regions exist
- ❌ **No material interpolation** (e.g., temperature-dependent properties)
- ❌ **No material mixing** (e.g., fuel + moderator mixtures)
- ❌ **No material homogenization** (e.g., fuel pin homogenization)
- ❌ **No material history tracking** (e.g., burnup-dependent properties)

**Impact:** Cannot model complex material distributions or time-dependent properties.

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Important for realistic modeling

#### 3.2 **Advanced Field Mapping**
- ⚠️ Basic temperature field storage
- ❌ **No flux-to-power mapping** (requires neutronics solver integration)
- ❌ **No power-to-temperature mapping** (requires thermal-hydraulics integration)
- ❌ **No multi-physics field coupling** (neutronics ↔ thermal-hydraulics)
- ❌ **No field interpolation** between different mesh resolutions

**Impact:** Cannot perform coupled multi-physics simulations.

**Recommendation:** 🔴 **HIGH PRIORITY** - Essential for realistic reactor simulation

#### 3.3 **Advanced Boundary Conditions**
- ❌ **No boundary condition definitions** (reflective, vacuum, periodic)
- ❌ **No interface conditions** (material boundaries, control rod interfaces)
- ❌ **No symmetry conditions** (1/6, 1/4, 1/2 core models)
- ❌ **No boundary layer treatment** (for thermal-hydraulics)

**Impact:** Cannot properly model reactor boundaries or interfaces.

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Important for accurate modeling

---

### 4. **Advanced Geometry Validation** ⚠️

**Current State:**
- ✅ Basic geometry validation (gaps, boundaries, connectivity)
- ✅ Assembly placement validation
- ✅ Control rod insertion validation
- ✅ Fuel loading pattern validation

**Missing Advanced Capabilities:**

#### 4.1 **Advanced Consistency Checks**
- ⚠️ Basic consistency checks exist
- ❌ **No volume conservation** checks (total volume = sum of parts)
- ❌ **No mass conservation** checks (material densities)
- ❌ **No energy conservation** checks (power balance)
- ❌ **No geometric constraints** validation (e.g., minimum clearances)

**Impact:** May miss geometric errors that affect physics calculations.

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Improves reliability

#### 4.2 **Advanced Error Detection**
- ⚠️ Basic error detection exists
- ❌ **No automatic error correction** (suggest fixes)
- ❌ **No error prioritization** (critical vs. warning)
- ❌ **No error visualization** (highlight errors in geometry)
- ❌ **No error reporting** (detailed reports with recommendations)

**Impact:** Users may struggle to fix geometry errors.

**Recommendation:** 🟢 **LOW PRIORITY** - Usability enhancement

---

## 🟡 MEDIUM PRIORITY Gaps

### 1. **Advanced Nuclear Data Processing**

- ❌ **No multi-temperature cross-section libraries** (pre-computed at multiple temperatures)
- ❌ **No cross-section interpolation** between library versions
- ❌ **No cross-section perturbation** (for sensitivity studies)
- ❌ **No cross-section editing** (manual modifications)

### 2. **Advanced Geometry Operations**

- ❌ **No geometry transformations** (rotation, translation, scaling)
- ❌ **No geometry duplication** (copy, mirror, array)
- ❌ **No geometry simplification** (reduce complexity)
- ❌ **No geometry optimization** (minimize volume, maximize surface area)

### 3. **Advanced Integration**

- ❌ **No direct integration** with external solvers (OpenMC, Serpent, MCNP)
- ❌ **No geometry export** to all major formats (OpenMC, Serpent, MCNP, DAGMC)
- ❌ **No automated workflow** for geometry → solver → results
- ❌ **No geometry versioning** (track changes over time)

---

## 🟢 LOW PRIORITY / Future Enhancements

### 1. **Performance Optimizations**

- ❌ **No GPU acceleration** for cross-section processing
- ❌ **No parallel processing** for multi-group collapse
- ❌ **No distributed computing** support
- ❌ **No just-in-time compilation** for hot paths (beyond Numba)

### 2. **Advanced Features**

- ❌ **No machine learning** integration (e.g., cross-section prediction)
- ❌ **No uncertainty quantification** in geometry parameters
- ❌ **No design optimization** integration
- ❌ **No automated design generation** (genetic algorithms, etc.)

---

## Priority Recommendations

### 🔴 Immediate Focus (Next 1-3 months)

1. **Resonance Self-Shielding** - Critical for accurate reactor physics
2. **Advanced Fission Data** (MF=5, delayed neutrons) - Required for burnup/transients
3. **Geometry-Physics Coupling** - Essential for multi-physics simulations

### 🟡 Medium-term (3-6 months)

4. **Advanced Scattering Matrix** (MF=6, anisotropic scattering)
5. **Advanced Multi-Group Processing** (SPH, equivalence theory)
6. **Advanced Core Types** (annular, hybrid, fast reactors)

### 🟢 Long-term (6+ months)

7. **Advanced Mesh Operations** (coarsening, smoothing, optimization)
8. **Performance Optimizations** (GPU, distributed computing)
9. **Advanced Integration** (external solvers, automated workflows)

---

## Summary Table

| Capability Area | Priority | Status | Impact | Effort |
|----------------|----------|--------|--------|--------|
| Resonance Self-Shielding | 🔴 HIGH | ❌ Missing | Critical | High |
| Advanced Fission Data | 🔴 HIGH | ⚠️ Partial | Critical | Medium |
| Geometry-Physics Coupling | 🔴 HIGH | ⚠️ Partial | Critical | High |
| Advanced Scattering | 🟡 MEDIUM | ⚠️ Partial | High | Medium |
| Advanced Multi-Group | 🟡 MEDIUM | ⚠️ Partial | High | Medium |
| Advanced Core Types | 🟡 MEDIUM | ⚠️ Partial | Medium | Medium |
| Advanced Mesh Operations | 🟢 LOW | ⚠️ Partial | Medium | Low |
| Performance Optimizations | 🟢 LOW | ❌ Missing | Low | High |

---

## Conclusion

The codebase has strong foundational capabilities in nuclear data management and geometry handling. However, several advanced capabilities are missing that would significantly enhance reactor simulation accuracy and applicability:

1. **Resonance self-shielding** is critical for accurate heterogeneous reactor calculations
2. **Advanced fission data** (yields, delayed neutrons) is required for burnup and transient analysis
3. **Geometry-physics coupling** is essential for realistic multi-physics simulations
4. **Advanced scattering and multi-group processing** would improve accuracy

These gaps should be addressed in priority order to maximize impact on reactor simulation capabilities.
