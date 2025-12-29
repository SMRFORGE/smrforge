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

---

## 🟡 Experimental Features (In Development)

These modules exist but are not fully tested or may have limitations:

### Neutronics
- 🟡 **Monte Carlo Solver** (`smrforge.neutronics.monte_carlo`) - Basic implementation, needs validation
- 🟡 **Transport Solver** (`smrforge.neutronics.transport`) - Framework exists, needs completion

### Thermal-Hydraulics
- 🟡 **Channel Thermal-Hydraulics** (`smrforge.thermal.hydraulics`) - Implementation exists, needs more testing

### Safety
- 🟡 **Transient Analysis** (`smrforge.safety.transients`) - LOCA, LOFA, REA, ATWS - Implemented but needs validation

### Uncertainty
- 🟡 **Uncertainty Quantification** (`smrforge.uncertainty.uq`) - Basic framework exists

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

### Visualization
- ✅ **Geometry Visualization** (`smrforge.visualization.geometry`)
  - **Status**: Implemented and tested (83.5% coverage)
  - **Features**:
    - 2D core layout plots (top view, side views)
    - Flux distribution overlays
    - Power distribution visualization
    - Temperature distribution plots
    - Support for prismatic and pebble bed cores
  - **Use Case**: Plotting geometry, flux, power, and temperature distributions

### Control Systems
- ❌ **Control Module** (`smrforge.control`) - Empty stub
  - **Status**: Not implemented
  - **Use Case**: Reactor control, protection systems
  - **Recommendation**: Implement as needed for specific use cases

### Economics
- ❌ **Economics Module** (`smrforge.economics`) - Empty stub
  - **Status**: Not implemented
  - **Use Case**: Cost analysis, LCOE calculations
  - **Recommendation**: Implement as needed for specific use cases

### Utilities
- ❌ **Utils Module** (`smrforge.utils`) - Empty stub
  - **Status**: Not implemented
  - **Use Case**: Helper functions
  - **Recommendation**: Add utilities as needed

---

## ⚠️ Incomplete Methods

### Neutronics Solver
- ⚠️ **Arnoldi Eigenvalue Method** (`MultiGroupDiffusion._arnoldi_method()`)
  - **Status**: Not implemented (raises `NotImplementedError`)
  - **Alternative**: Power iteration method is fully functional and tested
  - **Impact**: Low - power iteration works well for most problems
  - **Recommendation**: Use power iteration method (default)

---

## API Stability Guarantees

### Stable API (v1.0+)
- Core neutronics solver interface
- Validation models and validators
- Preset reactor designs
- Convenience functions

### Experimental API (May Change)
- Monte Carlo solver interface
- Transport solver interface
- Thermal-hydraulics API details

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
  - Most other features experimental or stubs

- **v1.0.0 (Planned)**: Production release
  - All stable features finalized
  - Experimental features either stabilized or removed
  - Stub modules either implemented or removed

---

*Last Updated: 2024-12-28*

