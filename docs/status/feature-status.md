# SMRForge Feature Status

**Last Updated:** February 10, 2026

This document describes the implementation status and stability of SMRForge modules.

**Roadmap:** Roadmaps are in SMRForge-Private (local docs, not in repo). See `SMRForge-Private/roadmaps/CONSOLIDATED-ROADMAP.md` for the consolidated “what to do next”.

---

## 🟢 Stable Features (Production Ready)

These modules are fully implemented, tested, and ready for production use:

### Core Modules
- ✅ **Core Constants** (`smrforge.core.constants`) - Physical constants and nuclear data
- ✅ **Materials Database** (`smrforge.core.materials_database`) - Material properties
- ✅ **Resonance Self-Shielding** (`smrforge.core.resonance_selfshield`) - Resonance treatment
- ✅ **Nuclear Data Cache** (`smrforge.core.reactor_core.NuclearDataCache`) - ENDF file management
  - Supports ENDF/B-VIII.0, ENDF/B-VIII.1, JEFF-3.3, JENDL-5.0
  - Local ENDF directory integration for offline use
  - Automatic file discovery and caching
  - Multi-URL download with fallback
  - Version fallback (VIII.1 → VIII.0)
  - Fast O(1) file lookups via cached index

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
  - OpenMC XML import (basic geometries)
  - Serpent input file import (basic geometries)
  - Geometry validation
  - Support for PrismaticCore and PebbleBedCore
- ✅ **Complex Geometry Import** (`smrforge.geometry.advanced_import`) - **NEW (January 2026)**
  - Full OpenMC CSG parsing and lattice reconstruction
  - Complex Serpent geometry parsing
  - CAD format import (STEP, IGES, STL)
  - MCNP geometry import
  - Advanced geometry conversion utilities
- ✅ **Enhanced Geometry Validation** (`smrforge.geometry.validation`) - **NEW (January 2026)**
  - Comprehensive validation tools (gaps, connectivity, clearances)
  - Assembly placement validation
  - Control rod insertion validation
  - Fuel loading pattern validation
  - Material boundary checking
- ✅ **Control Rod Geometry** (`smrforge.geometry.control_rods`)
  - Control rod positioning and geometry
  - Control rod banks and systems
  - Insertion/withdrawal control
  - Reactivity worth calculations
  - Shutdown margin analysis
  - **Enhanced features (January 2026):**
    - Advanced bank definitions (priority, dependencies, zones)
    - Control rod sequencing with priority/dependency ordering
    - Enhanced scram geometry (full insertion)
    - Advanced worth calculations per position
    - Axial and radial worth profiles (system-wide and per-bank)
- ✅ **Advanced Mesh Generation** (`smrforge.geometry.mesh_generation`)
  - Adaptive mesh refinement
  - Local refinement in regions
  - Mesh quality evaluation (angles, aspect ratio, skewness)
  - 2D unstructured mesh generation (Delaunay triangulation)
- ✅ **Enhanced Mesh Generation** (`smrforge.geometry.advanced_mesh`) - **NEW (January 2026)**
  - 3D structured/unstructured/hybrid mesh generation
  - Parallel mesh generation support (with joblib)
  - Mesh conversion utilities (VTK, STL, XDMF, OBJ, PLY, MSH, MED)
  - Format conversion between different mesh formats
- ✅ **Assembly Management** (`smrforge.geometry.assembly`)
  - Fuel assembly tracking
  - Burnup management
  - Refueling patterns (multi-batch)
  - Shuffle and refueling operations
  - Cycle length estimation
  - **Enhanced features (January 2026):**
    - Fuel shuffling with burnup-dependent geometry
    - Multi-batch fuel management (configurable max_batches)
    - Advanced assembly positioning/orientation (0-360 degrees)
    - Enhanced fuel cycle geometry tracking
    - Position history tracking per assembly

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
- ✅ **Advanced Visualization** (`smrforge.visualization.animations`, `comparison`) - **NEW (January 2026)**
  - Animation support (matplotlib, plotly)
  - 3D transient visualization
  - Comparison views for multiple designs
  - Video/GIF export capabilities
  - Overlaid geometry comparison
  - Time-dependent metric comparison

### Utilities
- ✅ **Utilities Module** (`smrforge.utils`)
  - Logging framework with Rich colorized console output (level colors, rich tracebacks)
  - Logo access functions
  - Structured logging throughout package

### Documentation & Feature Testing
- ✅ **Sphinx Documentation** (`docs/`)
  - Built with Sphinx + RTD theme
  - Supports both reStructuredText and Markdown guides
  - See: `docs/guides/testing-notebooks.md`
- ✅ **Manual Feature Tests (Scripts)** (`testing/test_*.py`)
  - One script per feature area (CLI, reactor creation, burnup, sweeps, visualization, etc.)
  - Test data lives under `testing/test_data/`
  - Outputs written under `testing/results/` (gitignored)
- ✅ **Manual Feature Tests (Notebooks)** (`testing/notebooks/*.ipynb`)
  - One notebook per feature script (thin wrappers that run the scripts and show output inline)
  - Intended for users to try features interactively without copy/paste

### ENDF Data Support
- ✅ **Thermal Scattering Laws** (`smrforge.core.thermal_scattering_parser`)
  - Full ENDF MF=7 parser (MT=2 and MT=4)
  - S(α,β) data extraction and interpolation
  - Temperature support with multi-temperature interpolation
  - Integration with neutronics solver
  - Material name mapping
- ✅ **Fission Yields** (`smrforge.core.fission_yield_parser`)
  - ENDF MF=8, MT=454, 459 parser
  - Independent and cumulative yields
  - Energy-dependent yield support
  - Integration with burnup solver
- ✅ **Decay Data** (`smrforge.core.decay_parser`)
  - ENDF MF=8, MT=457 parser
  - Half-life and decay constant extraction
  - Decay mode and branching ratio parsing
  - Gamma-ray spectrum parsing (MF=8, MT=460)
  - Beta spectrum parsing (MF=8, MT=455)
  - Integration with burnup solver

### Burnup and Depletion
- ✅ **Burnup Solver** (`smrforge.burnup`)
  - Bateman equation solver for nuclide evolution
  - Fission product production via yields
  - Radioactive decay via decay data
  - Cross-section updates based on composition
  - Spatial and energy-dependent flux integration
  - Burnup tracking (MWd/kgU)
  - Decay heat calculation

### Decay Heat
- ✅ **Decay Heat Calculator** (`smrforge.decay_heat`)
  - Time-dependent decay heat calculations
  - Energy-weighted decay heat from gamma/beta spectra
  - Nuclide-by-nuclide contribution tracking
  - Post-shutdown decay heat analysis
  - Integration with decay data parser

### Gamma Transport
- ✅ **Gamma Transport Solver** (`smrforge.gamma_transport`)
  - Multi-group gamma transport using diffusion approximation
  - Source iteration with convergence checking
  - Dose rate computation
  - Shielding calculations
  - Ready for photon cross-section data integration

### I/O and Format Converters
- ✅ **OpenMC integration** (`smrforge.io.openmc_run`, `openmc_export`, `openmc_import`) - Full export/import, subprocess runner, statepoint HDF5 parsing
- ✅ **Serpent run+parse** (`smrforge.io.serpent_run`) - **NEW (February 2026)** - run_serpent, parse_res_file, run_and_parse for Serpent round-trip with Pro export
- ✅ **Converters framework** (`smrforge.io.converters`) - SerpentConverter, OpenMCConverter (Pro delegation for Serpent/OpenMC full export/import)

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
  - LOCA (Loss of Coolant Accident) analysis
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

## 🔴 Not Implemented / Placeholders

Most modules listed above are implemented and covered by automated tests.

If you find a feature exposed in docs but missing in code, treat it as a placeholder and open an issue (or update this status page).


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

*Last Updated: February 2026*
