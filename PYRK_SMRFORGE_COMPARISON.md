# SMRForge vs PyRK: Side-by-Side Comparison

**Date:** January 2026  
**Purpose:** Comprehensive comparison to identify gaps in SMRForge that would enhance SMR development and simulation

---

## Executive Summary

**PyRK** (Python for Reactor Kinetics) is a mature, open-source tool for 0-D coupled neutronic and thermal-hydraulic reactor transient analysis, focused on point kinetics and lumped-parameter thermal hydraulics.

**SMRForge** is a comprehensive Python toolkit for nuclear reactor design, analysis, and optimization with emphasis on Small Modular Reactors (SMRs), featuring spatially-resolved neutronics, advanced nuclear data handling, and extensive geometry support.

**Key Finding:** SMRForge already exceeds PyRK in most areas, but there are specific PyRK strengths that could enhance SMRForge for SMR development.

---

## Detailed Feature Comparison

### 1. Neutronics Modeling

| Feature | PyRK | SMRForge | Notes |
|---------|------|----------|-------|
| **Spatial Resolution** | ❌ 0-D only (point kinetics) | ✅ Multi-group diffusion (2D/3D) | **SMRForge advantage:** Spatially resolved neutronics |
| **Point Kinetics** | ✅ Primary focus | ✅ Available (for transients) | **Both have:** Point kinetics with delayed neutrons |
| **Delayed Neutron Groups** | ✅ 6 groups | ✅ 6 groups (configurable) | **Equal:** Standard 6-group model |
| **Transport Methods** | ❌ None | ✅ Monte Carlo (experimental, 97.7% test coverage) | **SMRForge advantage:** Multiple solution methods |
| **Precursor Tracking** | ✅ Built-in | ✅ Available via PointKineticsSolver | **Both have:** Delayed neutron precursor tracking |
| **Eigenvalue Methods** | ✅ Basic (PRKE) | ✅ Power iteration, Arnoldi | **SMRForge advantage:** Multiple eigenvalue solvers |

**Verdict:** SMRForge has significantly more advanced neutronics capabilities than PyRK.

---

### 2. Thermal-Hydraulics Modeling

| Feature | PyRK | SMRForge | Notes |
|---------|------|----------|-------|
| **Model Type** | ✅ Lumped-parameter (0-D thermal circuits) | ✅ 1D channel models | **Different approaches:** PyRK uses lumped capacitance, SMRForge uses 1D flow |
| **Spatial Resolution** | ❌ 0-D (material lumps) | ✅ 1D axial (axial profiles) | **SMRForge advantage:** Higher spatial fidelity |
| **Flow Modeling** | ❌ None (no detailed flow) | ✅ 1D flow (momentum + energy equations) | **SMRForge advantage:** Actual flow calculations |
| **Fluid Properties** | ✅ Basic | ✅ Comprehensive (helium, water, etc.) | **Both have:** Fluid property libraries |
| **Heat Transfer Correlations** | ⚠️ Simplified | ✅ Dittus-Boelter, friction factor correlations | **SMRForge advantage:** More detailed correlations |
| **Porous Media Flow** | ❌ None | ✅ Pebble bed flow (Ergun equation) | **SMRForge advantage:** SMR-specific capabilities |
| **Conjugate Heat Transfer** | ⚠️ Implicit in lumped model | ✅ Explicit coupled solver | **SMRForge advantage:** Explicit coupling |
| **Two-Phase Flow** | ❌ Not modeled | ⚠️ Stub (mentioned in BWR SMR docs) | **Both lacking:** Two-phase flow needs work |

**Verdict:** SMRForge has more advanced thermal-hydraulics, but PyRK's lumped-parameter approach has advantages for fast transient analysis.

---

### 3. Transient Analysis & Safety

| Feature | PyRK | SMRForge | Notes |
|---------|------|----------|-------|
| **Transient Scenarios** | ✅ Generic (reactivity insertion, ATWS, startup/shutdown) | ✅ Comprehensive (HTGR + LWR SMR specific) | **SMRForge advantage:** More reactor-type specific scenarios |
| **Point Kinetics Transients** | ✅ Primary capability | ✅ Full implementation | **Both have:** Comprehensive point kinetics |
| **Temperature Feedback** | ✅ Fuel + moderator coefficients | ✅ Fuel + moderator coefficients | **Both have:** Temperature-dependent reactivity |
| **Decay Heat** | ✅ ANS/ANSI standard | ✅ ANS 5.1 standard | **Both have:** Industry-standard decay heat |
| **Reactivity Insertion** | ✅ Supported | ✅ Supported (RIA class) | **Both have:** Reactivity insertion accidents |
| **ATWS (Anticipated Transient Without Scram)** | ✅ Supported | ✅ Supported | **Both have:** ATWS analysis |
| **LOFC (Loss of Forced Cooling)** | ❌ Not explicitly mentioned | ✅ Supported (HTGR-specific) | **SMRForge advantage:** SMR-specific transients |
| **LOCA (Loss of Coolant Accident)** | ❌ Generic only | ✅ HTGR + LWR SMR specific | **SMRForge advantage:** Multiple LOCA scenarios |
| **LWR SMR Transients** | ❌ Not supported | ✅ PWR/BWR/Integral SMR transients | **SMRForge advantage:** Extensive LWR SMR support |
| **Steam Line Break** | ❌ Not mentioned | ✅ PWR SMR specific | **SMRForge advantage:** Industry-relevant scenarios |
| **Control Rod Kinetics** | ⚠️ Simplified | ✅ Spatial control rod modeling | **SMRForge advantage:** More realistic control rod behavior |

**Verdict:** SMRForge has significantly more comprehensive transient analysis capabilities, especially for SMR-specific scenarios.

---

### 4. Nuclear Data & Materials

| Feature | PyRK | SMRForge | Notes |
|---------|------|----------|-------|
| **Nuclear Data Library** | ✅ Built-in material library | ✅ ENDF/B-VIII.0, VIII.1, JEFF-3.3, JENDL-5.0 | **SMRForge advantage:** Full ENDF parsing |
| **Cross-Section Handling** | ✅ Pre-defined | ✅ Parsed from ENDF files | **SMRForge advantage:** More flexible |
| **Temperature-Dependent XS** | ⚠️ Limited | ✅ Temperature-dependent via ENDF | **SMRForge advantage:** Advanced nuclear data features |
| **Resonance Self-Shielding** | ❌ Not mentioned | ✅ Bondarenko, Subgroup, Equivalence theory | **SMRForge advantage:** Advanced self-shielding |
| **Fission Yield Data** | ❌ Not mentioned | ✅ MF=5 parsing (independent/cumulative yields) | **SMRForge advantage:** Complete fission product data |
| **Delayed Neutron Data** | ✅ Built-in (6-group) | ✅ MT=455 parsing from ENDF | **SMRForge advantage:** Data extracted from standards |
| **Thermal Scattering Laws (TSL)** | ❌ Not mentioned | ✅ MF=7 parsing (H2O, graphite, D2O, BeO) | **SMRForge advantage:** Advanced moderator modeling |
| **Material Library** | ✅ Comprehensive | ✅ Comprehensive + extensible | **Both have:** Good material support |

**Verdict:** SMRForge has significantly more advanced nuclear data capabilities, including ENDF parsing and advanced features like self-shielding.

---

### 5. Geometry & Spatial Modeling

| Feature | PyRK | SMRForge | Notes |
|---------|------|----------|-------|
| **Spatial Dimensions** | ❌ 0-D only | ✅ 2D (radial-axial, R-Z) and 3D | **SMRForge advantage:** Full spatial modeling |
| **Geometry Types** | ❌ None (point model) | ✅ Prismatic, pebble bed, LWR assemblies | **SMRForge advantage:** Multiple reactor types |
| **Mesh Generation** | ❌ None | ✅ Automatic mesh generation | **SMRForge advantage:** Automated meshing |
| **Assembly-Level Modeling** | ❌ None | ✅ Fuel assemblies, control rods, nozzles | **SMRForge advantage:** Detailed geometry |
| **PWR SMR Support** | ❌ None | ✅ NuScale-style cores | **SMRForge advantage:** LWR SMR geometries |
| **BWR SMR Support** | ❌ None | ✅ BWR cores with two-phase regions | **SMRForge advantage:** Multiple LWR types |
| **Integral SMR Support** | ❌ None | ✅ In-vessel steam generators | **SMRForge advantage:** Integral SMR designs |
| **HTGR Support** | ⚠️ Generic only | ✅ Prismatic + pebble bed | **SMRForge advantage:** Multiple HTGR geometries |

**Verdict:** SMRForge has vastly superior geometry capabilities; PyRK has none.

---

### 6. Burnup & Depletion

| Feature | PyRK | SMRForge | Notes |
|---------|------|----------|-------|
| **Burnup Calculations** | ❌ Not mentioned (no isotopic evolution) | ✅ Full burnup solver with nuclide tracking | **SMRForge advantage:** Complete burnup capability |
| **Nuclide Inventory Tracking** | ❌ None | ✅ Atom density tracking | **SMRForge advantage:** Detailed inventory |
| **Decay Chain Utilities** | ❌ None | ✅ Bateman equation solver, chain visualization | **SMRForge advantage:** Advanced decay chain tools |
| **Isotopic Evolution** | ❌ None | ✅ Transmutation, fission, decay | **SMRForge advantage:** Full isotopic modeling |
| **Fuel Cycle Analysis** | ❌ None | ✅ Assembly refueling, cycle analysis | **SMRForge advantage:** Fuel management |

**Verdict:** SMRForge has burnup/depletion capabilities; PyRK does not.

---

### 7. Validation & Standards

| Feature | PyRK | SMRForge | Notes |
|---------|------|----------|-------|
| **Validation Benchmarks** | ⚠️ Limited (intended for prototyping) | ✅ Validation framework with benchmarks | **SMRForge advantage:** Structured validation |
| **ANS Standards** | ✅ ANS/ANSI decay heat, precursor data | ✅ ANS 5.1 decay heat | **Both have:** Industry standard compliance |
| **Unit Checking** | ✅ Pint (dimensional analysis) | ⚠️ Manual validation | **PyRK advantage:** Automated unit checking |
| **Verification** | ⚠️ Limited public validation | ✅ Comprehensive test suite (79.2% coverage) | **SMRForge advantage:** Extensive testing |

**Verdict:** SMRForge has more comprehensive validation, but PyRK has unit checking via Pint.

---

### 8. Code Architecture & Usability

| Feature | PyRK | SMRForge | Notes |
|---------|------|----------|-------|
| **Modularity** | ✅ Object-oriented, modular | ✅ Object-oriented, modular | **Both have:** Good architecture |
| **Extensibility** | ✅ Extensible materials/TH components | ✅ Plugin architecture, presets | **Both have:** Good extensibility |
| **API Design** | ✅ Clean, documented | ✅ Comprehensive with convenience functions | **Both have:** Good APIs |
| **Documentation** | ✅ Available (pyrk.github.io) | ✅ Comprehensive (GitHub Pages, ReadTheDocs) | **Both have:** Good documentation |
| **CLI** | ❌ Not mentioned | ✅ Comprehensive CLI with nested subcommands | **SMRForge advantage:** Command-line interface |
| **Web Dashboard** | ❌ None | ✅ Interactive web-based dashboard | **SMRForge advantage:** User-friendly GUI |
| **Convenience API** | ⚠️ Basic | ✅ One-liner functions, presets | **SMRForge advantage:** Higher-level abstractions |
| **Examples** | ✅ Available | ✅ 27+ comprehensive examples | **Both have:** Good examples |

**Verdict:** SMRForge has better usability features (CLI, dashboard, convenience API).

---

### 9. Performance & Scalability

| Feature | PyRK | SMRForge | Notes |
|---------|------|----------|-------|
| **Performance** | ✅ Lightweight (pure Python + SciPy) | ✅ Rust-powered dependencies (Pydantic, Polars) | **SMRForge advantage:** Performance optimizations |
| **Parallelization** | ❌ Not mentioned | ⚠️ Limited (some Monte Carlo parallelization) | **Both lacking:** Full parallelization |
| **HPC Support** | ❌ Not mentioned | ❌ Not implemented | **Both lacking:** HPC backends |
| **Scalability** | ✅ Good for 0-D models | ⚠️ Limited for large spatial models | **Different use cases:** PyRK faster for 0-D, SMRForge for spatial |

**Verdict:** Different performance characteristics due to different modeling approaches.

---

### 10. Reactor Type Support

| Reactor Type | PyRK | SMRForge | Notes |
|--------------|------|----------|-------|
| **Generic Reactors** | ✅ Primary focus | ✅ Supported | **Both have:** Generic capability |
| **HTGR (Prismatic)** | ⚠️ Generic only | ✅ Full support (Valar-10, GT-MHR, etc.) | **SMRForge advantage:** Specific designs |
| **HTGR (Pebble Bed)** | ⚠️ Generic only | ✅ Full support (HTR-PM, Micro-HTGR) | **SMRForge advantage:** Multiple HTGR types |
| **PWR SMR** | ❌ None | ✅ NuScale-style, square lattice | **SMRForge advantage:** LWR SMR support |
| **BWR SMR** | ❌ None | ✅ BWR cores | **SMRForge advantage:** BWR SMR support |
| **Integral SMR** | ❌ None | ✅ In-vessel steam generators | **SMRForge advantage:** Integral designs |
| **MSR (Molten Salt)** | ❌ None | ⚠️ Geometry support only | **Both lacking:** Full MSR support |

**Verdict:** SMRForge has much broader reactor type support, especially for SMRs.

---

## Key PyRK Strengths (What SMRForge Could Learn From)

### 1. **Unit Checking with Pint**
- **PyRK:** Uses Pint for dimensional analysis and automatic unit conversion
- **SMRForge:** Manual unit validation
- **Recommendation:** Integrate Pint for automatic unit checking and conversion
- **Impact:** Prevents unit errors, improves code reliability, better user experience

### 2. **Lightweight Lumped-Parameter Thermal-Hydraulics**
- **PyRK:** Fast 0-D thermal circuits for rapid transient analysis
- **SMRForge:** More detailed 1D models (slower but more accurate)
- **Recommendation:** Add optional lumped-parameter TH mode for fast screening calculations
- **Impact:** Faster preliminary analysis, especially for long transients (72+ hours)

### 3. **Optimized for Long Transients**
- **PyRK:** Designed for long-term transient analysis (hours to days)
- **SMRForge:** Currently optimized for shorter transients
- **Recommendation:** Optimize transient solvers for long time scales (adaptive time stepping, sparse ODE solvers)
- **Impact:** Better capability for decay heat removal, extended ATWS scenarios

### 4. **Simple, Focused API for Point Kinetics**
- **PyRK:** Very clean, simple API specifically for point kinetics transients
- **SMRForge:** More complex API (more powerful, but steeper learning curve)
- **Recommendation:** Create simplified "quick transient" API wrapping PointKineticsSolver
- **Impact:** Easier adoption for users who just need point kinetics

---

## Critical Gaps in SMRForge (Compared to PyRK's Use Cases)

### 1. **Unit Checking System**
**Status:** ❌ Missing  
**Priority:** High  
**Effort:** Medium  
**Benefit:** Prevents common errors, improves code quality

**Implementation:**
```python
# Add Pint-based unit checking
from pint import UnitRegistry
ureg = UnitRegistry()

# Example usage
power = 10 * ureg.megawatt
temperature = 500 * ureg.kelvin
reactivity = -5e-5 * ureg.dimensionless  # dk/k
```

### 2. **Lumped-Parameter Thermal-Hydraulics Option**
**Status:** ⚠️ Partially (has ConjugateHeatTransfer, but not lightweight lumped)  
**Priority:** Medium  
**Effort:** Medium  
**Benefit:** Faster transient analysis for screening

**Implementation:** Create `LumpedThermalHydraulics` class similar to PyRK's approach:
- Material lumps (fuel, moderator, coolant)
- Thermal capacitance (C = m*cp)
- Thermal resistance (R = 1/(h*A))
- Simple ODE system: C*dT/dt = Q_in - Q_out

### 3. **Optimized Long-Term Transient Analysis**
**Status:** ⚠️ Works but not optimized for 72+ hour transients  
**Priority:** Medium  
**Effort:** High  
**Benefit:** Better performance for extended scenarios (decay heat removal, ATWS)

**Optimizations:**
- Adaptive time stepping (large steps when slow, small steps when fast)
- Sparse ODE solvers for stiff systems
- Implicit methods for long time scales
- Decay heat approximation for very long times (t > 1 day)

### 4. **Simplified Point Kinetics API**
**Status:** ⚠️ Has PointKineticsSolver but complex API  
**Priority:** Low  
**Effort:** Low  
**Benefit:** Easier adoption for point kinetics users

**Implementation:** Create convenience wrapper:
```python
# Quick transient analysis
result = smr.quick_transient(
    power=10e6,  # W
    temperature=1200.0,  # K
    reactivity_insertion=0.001,  # dk/k
    transient_type="reactivity_insertion",
    duration=100.0  # seconds
)
```

---

## What SMRForge Has That PyRK Doesn't (Major Advantages)

1. **Spatially-Resolved Neutronics** - Multi-group diffusion, Monte Carlo
2. **Advanced Nuclear Data** - ENDF parsing, self-shielding, TSL, fission yields
3. **Burnup/Depletion** - Full isotopic evolution, decay chains
4. **Comprehensive Geometry** - 2D/3D, multiple reactor types
5. **LWR SMR Support** - PWR, BWR, integral SMRs
6. **Extensive Transient Scenarios** - Reactor-specific accidents
7. **CLI & Dashboard** - User-friendly interfaces
8. **Validation Framework** - Structured benchmarking
9. **Monte Carlo Transport** - Higher fidelity option
10. **Advanced Visualization** - 3D, animations, dashboards

---

## Recommendations for SMRForge Enhancement

### High Priority (Immediate Impact)

1. **Add Pint-based Unit Checking**
   - Integrate Pint for automatic unit validation
   - Prevents unit errors in calculations
   - Improves code reliability

2. **Create Lumped-Parameter TH Option**
   - Lightweight thermal circuit model
   - Fast screening for long transients
   - Complement to existing 1D models

### Medium Priority (Significant Enhancement)

3. **Optimize Long-Term Transients**
   - Adaptive time stepping
   - Implicit ODE solvers for stiff systems
   - Sparse matrix methods
   - Decay heat approximations for t > 1 day

4. **Add Simplified Point Kinetics API**
   - Quick transient analysis wrapper
   - Easier adoption for new users
   - Maintains full API for advanced users

### Low Priority (Nice to Have)

5. **Two-Phase Flow Modeling**
   - Both PyRK and SMRForge lack this
   - Critical for BWR SMRs and LOCA scenarios
   - High development effort

6. **HPC/Parallelization**
   - Both tools would benefit
   - Enables larger spatial models
   - Long-term enhancement

---

## Conclusion

**Overall Assessment:** SMRForge already exceeds PyRK in most areas, especially:
- Spatial neutronics (vs. 0-D only)
- Nuclear data capabilities (ENDF parsing, self-shielding)
- Reactor type support (LWR SMR, HTGR variants)
- Burnup/depletion modeling
- Geometry and visualization

**Key PyRK Advantages to Adopt:**
1. Unit checking with Pint (prevents errors)
2. Lightweight lumped-parameter TH (fast screening)
3. Optimized long-term transient analysis (72+ hour scenarios)

**Final Verdict:** SMRForge is well-positioned for SMR development. The recommended enhancements (Pint integration, lumped-parameter TH, optimized long transients) would make it even more competitive while maintaining its superior spatial modeling and nuclear data capabilities.

---

## References

- **PyRK:** https://github.com/pyrk/pyrk
- **PyRK Documentation:** https://pyrk.github.io
- **SMRForge Repository:** https://github.com/cmwhalen/smrforge
- **SMRForge Documentation:** https://cmwhalen.github.io/smrforge/

---

**Document Created:** January 2026  
**Last Updated:** January 2026
