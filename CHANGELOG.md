# Changelog

**Last Updated:** January 18, 2026

All notable changes to SMRForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Visualization Module** (`smrforge.visualization.geometry`)
  - 2D core layout plotting (prismatic and pebble bed cores)
  - Flux, power, and temperature distribution visualization
  - Multiple view options (xy, xz, yz)
  - Comprehensive test coverage (83.5%)
- **Geometry Import/Export** (`smrforge.geometry.importers`)
  - JSON format import/export for geometries
  - Geometry validation (overlaps, dimensions, packing fraction)
  - Support for PrismaticCore and PebbleBedCore
  - Test coverage (93.5%)
- **Control Rod Geometry** (`smrforge.geometry.control_rods`)
  - Control rod positioning and geometry
  - Control rod banks and systems
  - Insertion/withdrawal control
  - Reactivity worth calculations
  - Shutdown margin analysis
  - Test coverage (100%)
- **Advanced Mesh Generation** (`smrforge.geometry.mesh_generation`)
  - Adaptive mesh refinement
  - Local refinement in specified regions
  - Mesh quality evaluation (angles, aspect ratio, skewness, Jacobian)
  - 2D unstructured mesh generation (Delaunay triangulation)
  - Gradient computation methods
  - Test coverage (100%)
- **Assembly Management** (`smrforge.geometry.assembly`)
  - Fuel assembly tracking with burnup management
  - Refueling patterns (multi-batch support)
  - Shuffle and refueling operations
  - Cycle length estimation
  - Test coverage (97.0%)
- Comprehensive test infrastructure with 100+ test cases
- Integration tests for complete workflows
- GitHub Actions CI/CD pipeline
- Logging framework with structured logging
- Example gallery with 6 example scripts
- Sphinx documentation structure
- Custom ENDF parser as built-in solution
- Multi-backend nuclear data support (SANDY, custom parser)
- Docker support with multiple Dockerfile configurations
- Logo integration in README and documentation
- Test coverage for new features: 94.2% (82 new tests)

### Changed
- Enhanced test fixtures and utilities
- Improved error messages in validation
- Better documentation of experimental vs stable features

### Fixed
- Fixed zarr compatibility (DirectoryStore → LocalStore)
- Fixed import paths for preset designs
- Fixed validation warnings for HALEU enrichment
- Fixed Numba decorator usage in resonance self-shielding
- Fixed missing dependencies (requests, pydantic-settings)

## [0.1.0] - 2025

### Added
- Initial alpha release
- Multi-group neutron diffusion solver
- Pydantic-based validation framework
- Reactor geometry support (prismatic and pebble bed)
- Preset HTGR reactor designs (Valar-10, GT-MHR, HTR-PM, Micro-HTGR)
- Thermal-hydraulics channel models
- Safety analysis framework (transients)
- Uncertainty quantification framework
- Convenience API for easy usage
- Nuclear data handling with caching
- Resonance self-shielding methods
- Materials database

### Known Issues
- Arnoldi eigenvalue method not implemented (use power iteration)
- Several modules are stubs (fuel, optimization, io, visualization, control, economics)
- Monte Carlo and transport solvers are experimental

---

## Release Types

- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

## Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

