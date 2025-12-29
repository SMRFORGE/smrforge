# Experimental Features Summary

Based on `FEATURE_STATUS.md`, here are the features currently marked as **Experimental** (🟡):

## Currently Experimental Features

### 1. Monte Carlo Solver (`smrforge.neutronics.monte_carlo`)
- **Status**: 🟢 Fully validated with comprehensive test coverage (97.7%)
- **Why Experimental**: API may change in future versions
- **Features**:
  - Eigenvalue (k-eff) calculations with power iteration
  - Particle tracking with simplified geometry (cylindrical core + reflector)
  - Reaction sampling (scatter, fission, capture)
  - Tallies (flux, reaction rates)
  - Input validation and error handling
  - Reproducible results via seed parameter
  - 51 tests covering all major functionality

### 2. Transport Solver (`smrforge.neutronics.transport`)
- **Status**: 🟢 Fully implemented with comprehensive test coverage
- **Why Experimental**: API may change in future versions
- **Features**:
  - High-level Transport class interface
  - Monte Carlo neutron transport with 3D geometry (Sphere, Cylinder, Box)
  - Variance reduction (importance sampling, weight windows)
  - Tallies (flux, reaction rates)
  - Eigenvalue (k-eff) calculations
  - 55+ tests covering all major functionality

### 3. Channel Thermal-Hydraulics (`smrforge.thermal.hydraulics`)
- **Status**: 🟢 Fully validated with comprehensive test coverage
- **Why Experimental**: API details may change in future versions
- **Features**:
  - 1D channel thermal-hydraulics with momentum and energy equations
  - Fuel rod thermal conduction (steady-state and transient)
  - Porous media flow (pebble bed) using Ergun equation
  - Fluid properties (helium coolant)
  - Conjugate heat transfer coupling
  - 45+ tests covering all major functionality

### 4. Safety Analysis - Transients (`smrforge.safety.transients`)
- **Status**: 🟢 Fully validated with comprehensive test coverage
- **Why Experimental**: API may change in future versions
- **Features**:
  - Point kinetics solver with temperature feedback
  - LOFC (Loss of Forced Cooling) transient analysis
  - ATWS (Anticipated Transient Without Scram) analysis
  - Reactivity Insertion Accident (RIA) analysis
  - Air/Water ingress analysis
  - Decay heat calculations (ANS standard)
  - 40+ tests covering all major functionality

### 5. Uncertainty Quantification (`smrforge.uncertainty.uq`)
- **Status**: 🟢 Fully validated with comprehensive test coverage
- **Why Experimental**: API may change in future versions
- **Features**:
  - Uncertain parameter definitions (normal, uniform, lognormal, triangular distributions)
  - Monte Carlo, Latin Hypercube, and Sobol sequence sampling
  - Uncertainty propagation through reactor models
  - Global sensitivity analysis (Sobol indices, Morris screening) - requires SALib
  - Visualization tools for UQ results
  - 55+ tests covering all major functionality

---

## Why Are These Experimental?

Even though these features have:
- ✅ Comprehensive test coverage
- ✅ Input validation and error handling
- ✅ Good documentation
- ✅ Extensive logging

They remain **Experimental** because:
- 🔄 **API Stability**: The API interface may change in future versions
- 🔄 **Usage Patterns**: Common usage patterns are still being established
- 🔄 **Integration**: Integration with other modules may evolve

This is noted in the API Stability Guarantees section:
> **Experimental API (May Change)**
> - Monte Carlo solver interface
> - Transport solver interface
> - Thermal-hydraulics API details

---

## Recommendation

These features are **production-ready in terms of functionality and testing**, but users should:
1. ✅ **Feel confident using them** - they're well-tested and validated
2. ⚠️ **Be prepared for API changes** - method signatures may change in future versions
3. ✅ **Test thoroughly** - as with any new code
4. 📝 **Provide feedback** - help shape the API based on real-world usage

---

## What's NOT Experimental (Stable)

The following are marked as **Stable** (✅):

- Multi-Group Diffusion Solver (neutronics.solver)
- Geometry modules (core, import/export, control rods, mesh generation, assembly management)
- Visualization module
- Validation framework
- Preset reactor designs
- Convenience API
- Utilities (logging, etc.)

---

## Status in README.md

In `README.md`, the experimental features are listed as:

```markdown
### 🟡 Experimental (In Development)
- **Monte Carlo Transport**: Particle transport solver with comprehensive test coverage
- **Thermal-Hydraulics**: 1D channel models with fluid properties
- **Safety Analysis**: Transient simulations (LOCA, LOFA, ATWS, RIA) with point kinetics
- **Uncertainty Quantification**: Monte Carlo sampling, sensitivity analysis (Sobol indices, Morris screening)
```

---

*Last checked: Based on FEATURE_STATUS.md and codebase analysis*

