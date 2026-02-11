# Changelog

**Last Updated:** February 2026

All notable changes to SMRForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Convenience functions:** `load_reactor(path)` loads a reactor from JSON (full schema or simplified `power_mw` format). `quick_validate(reactor_or_path, constraint_set=None)` validates a design in one call. `create_reactor(config=path)` creates a reactor from a JSON config file.

### Added
- **New convenience functions:** `quick_sweep()` (parameter sweep), `quick_economics()` (cost estimate), `quick_optimize()` (design optimization), `quick_uq()` (uncertainty quantification), `list_reactor_types()`, `list_fuel_types()` for easier discovery and workflows.
- **Discovery helpers:** `get_default_endf_dir()`, `list_endf_libraries()`, `list_geometry_types()`, `list_analysis_types()`, `list_surrogates()`. **quick_download_endf()** for one-liner ENDF data downloads.
- **Discovery and help functions:** `system_info()` (version and capabilities), `help_topics()`, `list_constraint_sets()`, `get_constraint_set()`, `get_example_path()`, `list_examples()`, `list_nuclides()`, `list_sweepable_params()`, `get_default_output_dir()`.
- **Rich display options:** `system_info(display=True)` prints capabilities table; `quick_sweep`, `quick_economics`, `quick_optimize`, `quick_uq` support `display=True` for Rich summary tables; ENDF setup wizard uses Rich Panel/Table when available.

### Changed
- **Convenience API consolidation:** Removed legacy `smrforge/convenience.py`; all convenience functionality now lives in `smrforge/convenience/` package. No public API changes—`from smrforge.convenience import create_reactor` and `smrforge.create_reactor` work unchanged.

### Fixed
- **Dependencies:** Added `pyyaml>=6.0` and `requests>=2.25.0` to `setup.py` install_requires so PyPI installs have YAML support (templates, CLI config) and nuclear data downloads.
- **Documentation:** Updated `__init__.py` docstring to reference `docs/status/feature-status.md` (was ambiguous FEATURE_STATUS.md).
- **Coverage:** Removed stale `*/convenience.py` from `.coveragerc` omit list (file no longer exists).
- **Documentation:** Coding guidelines expanded in `docs/development/code-style.md` (optional deps, Rich, convenience APIs, kwargs hygiene, path handling). CONTRIBUTING.md PR checklist updated (changelog, Docker, docstrings). Testing-and-coverage.md: "Testing Optional Features" and "Coverage Exclusions" sections. Help examples for `system_info`, `quick_sweep`, `quick_economics`, `quick_optimize`, `quick_uq` (including `display=True`). Discovery example (`examples/discovery_help_example.py`) extended with `quick_optimize` and `quick_uq` demos.

## [0.2.0] - 2026-02-XX (Beta)

### Added
- **Serpent round-trip (Community):** Serpent run and result parsing in Community tier. `smrforge.io.serpent_run.run_serpent()`, `parse_res_file()`, `run_and_parse()` for running Serpent 2 and extracting k-eff from `_res.m`. Completes round-trip with Pro export: Pro export → Community run Serpent → parse results. Convenience: `smrforge.io.run_serpent()`, `parse_serpent_res()`.
- **OpenMC integration (Community):** Full OpenMC export/import in Community tier. Export PrismaticCore/PebbleBedCore to geometry.xml, materials.xml, settings.xml; import OpenMC geometry; run OpenMC via subprocess; parse statepoint HDF5 for k-eff and tallies. `OpenMCConverter.export_reactor()`, `import_reactor()`, `smrforge.io.openmc_run.run_openmc()`, `parse_statepoint()`. See examples/openmc_export_example.py.
- Rich colorized logging: Console output now uses Rich's RichHandler for color-coded log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL), rich tracebacks, and improved readability. File logging remains plain text. Falls back to standard handler if Rich is unavailable. Respects NO_COLOR environment variable.
- Docker: Updated Dockerfile, Dockerfile.dev, and docker-compose.yml with Rich logging notes and February 2026 date. Added Rich verification and NO_COLOR note to docs/guides/docker.md.
- Docker: Added documentation provenance note (SMRForge original work; OpenMC/Serpent inspiration/analysis).

### Fixed
- **Examples on Windows**: Replaced Unicode checkmarks (✓/✗) with ASCII-safe markers in preset validation and examples to prevent `UnicodeEncodeError` on Windows cp1252 consoles.

### Added (January 2026)
- Pint mandatory dependency: `pint>=0.20.0` added to `setup.py` install_requires
- Parameter sweep coverage tests: burnup analysis path, preset path fallback, parallel save intermediate, correlations
- Constraints coverage tests: save/load, value from reactor spec, min/max severity paths, unknown type skip

### Changed (January 2026)
- Documentation: Updated README, COVERAGE_TRACKING, DOCUMENTATION_INDEX, docker guide with current info
- Archived `docs/development/coverage-inventory.md` → `docs/archive/coverage-inventory-archived-2026-01-29.md` (superseded by COVERAGE_TRACKING.md)
- Coverage status: ~89.7% overall (target 90%), testing-and-coverage.md updated with COVERAGE_TRACKING as source of truth

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

