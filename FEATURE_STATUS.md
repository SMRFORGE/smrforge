# SMRForge Feature Status

This document describes the implementation status and stability of SMRForge modules.

---

## 🟢 Stable Features (Production Ready)

These modules are fully implemented, tested, and ready for production use:

### Core Modules
- ✅ **Core Constants** (`smrforge.core.constants`) - Physical constants and nuclear data
- ✅ **Materials Database** (`smrforge.core.materials_database`) - Material properties
- ✅ **Resonance Self-Shielding** (`smrforge.core.resonance_selfshield`) - Resonance treatment

### Neutronics
- ✅ **Multi-Group Diffusion Solver** (`smrforge.neutronics.solver.MultiGroupDiffusion`)
  - Power iteration eigenvalue method (fully implemented)
  - Steady-state solve
  - Power distribution computation
  - Comprehensive test coverage

### Geometry
- ✅ **Core Geometry** (`smrforge.geometry.core_geometry`)
  - Prismatic core support
  - Pebble bed core support
  - Basic mesh generation
- ✅ **Geometry Import/Export** (`smrforge.geometry.importers`)
  - JSON import/export
  - Geometry validation
  - Support for PrismaticCore and PebbleBedCore
- ✅ **Control Rod Geometry** (`smrforge.geometry.control_rods`)
  - Control rod positioning and geometry
  - Control rod banks and systems
  - Insertion/withdrawal control
  - Reactivity worth calculations
  - Shutdown margin analysis
- ✅ **Advanced Mesh Generation** (`smrforge.geometry.mesh_generation`)
  - Adaptive mesh refinement
  - Local refinement in regions
  - Mesh quality evaluation (angles, aspect ratio, skewness)
  - 2D unstructured mesh generation (Delaunay triangulation)
- ✅ **Assembly Management** (`smrforge.geometry.assembly`)
  - Fuel assembly tracking
  - Burnup management
  - Refueling patterns (multi-batch)
  - Shuffle and refueling operations
  - Cycle length estimation

### Validation
- ✅ **Pydantic Models** (`smrforge.validation.models`) - Data validation
- ✅ **Validators** (`smrforge.validation.validators`) - Physics validation
- ✅ **Integration Layer** (`smrforge.validation.integration`) - Validation framework

### Presets
- ✅ **Reference Designs** (`smrforge.presets.htgr`) - Validated reactor designs
  - Valar-10
  - GT-MHR-350
  - HTR-PM-200
  - Micro-HTGR-1

### Convenience API
- ✅ **Convenience Functions** (`smrforge.convenience`) - One-liner APIs
- ✅ **SimpleReactor** - High-level reactor wrapper

### Visualization
- ✅ **Geometry Visualization** (`smrforge.visualization.geometry`)
  - 2D core layout plots (top view, side views)
  - Flux distribution overlays
  - Power distribution visualization
  - Temperature distribution plots
  - Support for prismatic and pebble bed cores
  - Test coverage: 83.5%

### Utilities
- ✅ **Utilities Module** (`smrforge.utils`)
  - Logging framework and configuration
  - Logo access functions
  - Structured logging throughout package

---

## 🟡 Experimental Features (API May Change)

These modules are **functionally complete and well-tested**, but their APIs may change in future versions. They are safe to use, but be prepared for potential API changes:

### Neutronics
- 🟢 **Monte Carlo Solver** (`smrforge.neutronics.monte_carlo`) - Fully validated with comprehensive test coverage (97.7%). Features include:
  - Eigenvalue (k-eff) calculations with power iteration
  - Particle tracking with simplified geometry (cylindrical core + reflector)
  - Reaction sampling (scatter, fission, capture)
  - Tallies (flux, reaction rates)
  - Input validation and error handling
  - Reproducible results via seed parameter
  - Comprehensive logging
  - 51 tests covering all major functionality and edge cases
- 🟢 **Transport Solver** (`smrforge.neutronics.transport`) - Fully implemented with comprehensive test coverage. Features include:
  - High-level Transport class interface
  - Monte Carlo neutron transport with 3D geometry (Sphere, Cylinder, Box)
  - Variance reduction (importance sampling, weight windows)
  - Tallies (flux, reaction rates)
  - Eigenvalue (k-eff) calculations
  - Input validation and error handling
  - Reproducible results via seed parameter
  - Comprehensive logging
  - 55+ tests covering all major functionality

### Thermal-Hydraulics
- 🟢 **Channel Thermal-Hydraulics** (`smrforge.thermal.hydraulics`) - Fully validated with comprehensive test coverage. Features include:
  - 1D channel thermal-hydraulics with momentum and energy equations
  - Fuel rod thermal conduction (steady-state and transient)
  - Porous media flow (pebble bed) using Ergun equation
  - Fluid properties (helium coolant)
  - Conjugate heat transfer coupling
  - Input validation and error handling
  - Comprehensive logging
  - 45+ tests covering all major functionality and validation scenarios

### Safety
- 🟢 **Transient Analysis** (`smrforge.safety.transients`) - Fully validated with comprehensive test coverage. Features include:
  - Point kinetics solver with temperature feedback
  - LOFC (Loss of Forced Cooling) transient analysis
  - ATWS (Anticipated Transient Without Scram) analysis
  - Reactivity Insertion Accident (RIA) analysis
  - Air/Water ingress analysis
  - Decay heat calculations (ANS standard)
  - Input validation and error handling
  - Comprehensive logging
  - 40+ tests covering all major functionality and validation scenarios

### Uncertainty
- 🟢 **Uncertainty Quantification** (`smrforge.uncertainty.uq`) - Fully validated with comprehensive test coverage. Features include:
  - Uncertain parameter definitions (normal, uniform, lognormal, triangular distributions)
  - Monte Carlo, Latin Hypercube, and Sobol sequence sampling
  - Uncertainty propagation through reactor models
  - Global sensitivity analysis (Sobol indices, Morris screening) - requires SALib
  - Visualization tools for UQ results (distributions, scatter matrices, Sobol indices)
  - Input validation and error handling
  - Comprehensive logging
  - 55+ tests covering all major functionality, validation scenarios, and visualization methods

---

## 🔴 Not Implemented (Stubs)

These modules are placeholders with no implementation:

### Fuel Performance
- ❌ **Fuel Module** (`smrforge.fuel`) - Empty stub
  - **Status**: Not implemented
  - **Use Case**: Fuel temperature, swelling, fission gas release
  - **Recommendation**: Use external tools or implement as needed

### Optimization
- ❌ **Optimization Module** (`smrforge.optimization`) - Empty stub
  - **Status**: Not implemented
  - **Use Case**: Design optimization, loading pattern optimization
  - **Recommendation**: Use scipy.optimize or implement as needed

### I/O Utilities
- ✅ **Geometry Import** (`smrforge.geometry.importers`) - Implemented
  - JSON import/export for geometry
  - Geometry validation
  - See Geometry section above
- ❌ **General I/O Module** (`smrforge.io`) - Empty stub
  - **Status**: Not implemented (geometry I/O available via importers)
  - **Use Case**: General reactor design import/export
  - **Recommendation**: Use JSON/Pydantic serialization (already available via models)


### Control Systems
- ❌ **Control Module** (`smrforge.control`) - Empty stub
  - **Status**: Not implemented
  - **Note**: Control rod geometry is available via `smrforge.geometry.control_rods` (see Geometry section)
  - **Use Case**: Reactor control systems, protection systems, control logic
  - **Recommendation**: Implement as needed for specific use cases

### Economics
- ❌ **Economics Module** (`smrforge.economics`) - Empty stub
  - **Status**: Not implemented
  - **Use Case**: Cost analysis, LCOE calculations
  - **Recommendation**: Implement as needed for specific use cases


---

## ⚠️ Incomplete Methods

None - all documented methods are implemented.

---

## API Stability Guarantees

### Stable API (v1.0+)
- Core neutronics solver interface
- Validation models and validators
- Preset reactor designs
- Convenience functions
- Geometry modules (core, import/export, control rods, mesh generation, assembly management)
- Visualization module
- Utilities (logging, logo access)

### Experimental API (May Change)
These features are well-tested and functional, but their APIs may change:
- Monte Carlo solver interface - Functionally complete (97.7% test coverage)
- Transport solver interface - Functionally complete (55+ tests)
- Thermal-hydraulics API details - Functionally complete (45+ tests)
- Safety analysis API - Functionally complete (40+ tests)
- Uncertainty quantification API - Functionally complete (55+ tests)

**Note**: Use these features with confidence, but be prepared for API changes in future versions. The functionality is stable; only the interface may evolve.

### No API (Stubs)
- Empty modules have no API guarantees
- Will be implemented or removed in future versions

---

## Migration Notes

If you're using features that are marked as experimental or not implemented:

1. **Experimental Features**: Test thoroughly and be prepared for API changes
2. **Not Implemented**: Consider alternative approaches or contribute implementation
3. **Incomplete Methods**: Use alternative methods (e.g., power iteration instead of Arnoldi)

---

## Version History

- **v0.1.0 (Current)**: Alpha release
  - Core neutronics stable
  - Validation framework stable
  - Geometry modules stable (core, import/export, control rods, mesh generation, assembly management)
  - Visualization module stable
  - Utilities stable (logging)
  - Many features now stable (previously experimental or stubs)

- **v1.0.0 (Planned)**: Production release
  - All stable features finalized
  - Experimental features either stabilized or removed
  - Stub modules either implemented or removed
  - Performance optimization and validation

---

*Last Updated: 2024-12-28*

