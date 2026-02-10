# SMRForge Dockerfile
# Supports both runtime and development use cases
#
# Build: docker build -t smrforge:latest .
# Run:   docker run -it smrforge:latest
#
# Last Updated: February 10, 2026
# Recent Additions (February 2026):
# - Serpent round-trip (Community): run_serpent, parse_res_file, run_and_parse in smrforge.io.serpent_run; run_serpent, parse_serpent_res in smrforge.io.
# - OpenMC integration (Community): Full export/import (geometry.xml, materials.xml, settings.xml), subprocess runner, statepoint HDF5 parsing. See smrforge.io.openmc_export, openmc_import, openmc_run.
# - Rich colorized logging: Console logging uses RichHandler for color-coded levels (DEBUG, INFO, WARNING, ERROR, CRITICAL), rich tracebacks. File logging remains plain text. Set NO_COLOR=1 to disable colors.
# - Documentation: README and technical docs clarify SMRForge is original work; OpenMC/Serpent references are inspiration and analysis, not code derivation.
# Recent Additions (January 2026):
# - Pint mandatory: pint>=0.20.0 now in setup.py install_requires (required for unit checking)
# - Memory and performance profiling (January 2026): profile_performance.py (--mode cpu|memory|both, --function keff|mesh|monte_carlo), run_performance_profile.*, update_performance_baselines.py, smrforge.utils.profiling. See docs/development/memory-and-performance-assessment.md.
# - Performance optimizations (January 25, 2026):
#   * Vectorized burnup fission rate integration (~10-100x faster)
#   * Vectorized control rod shadowing calculation (~5-20x faster)
#   * Optimized gamma transport sparse matrix construction (~5-10x faster)
#   * Vectorized cross-section broadcasting (~ng times faster)
#   * Optimized control rod distance calculation (~5-10x faster)
#   * Temperature interpolation with 2D spline (~10-50x faster)
#   * Numba JIT for matrix construction helpers (~2-5x faster)
#   * Optimized self-shielding subgroup method (~2-3x faster)
# - CLI enhancements (January 25, 2026):
#   * Added 'data interpolate' command for cross-section temperature interpolation
#   * Added 'data shield' command for self-shielding calculations
#   * Both commands support JSON/CSV output and optional plotting
# Recent Additions (January 2026):
# - Creep models (primary, secondary, tertiary, irradiation-enhanced) for fuel rod materials
# - Material degradation models for long-term fuel rod analysis
# - Multi-physics coupling framework (unified coupling of all physics domains)
# - Model Predictive Control (MPC) for advanced reactor control algorithms
# - Fuel Performance module (temperature calculations, swelling, fission gas release)
# - General Optimization module (design optimization, loading pattern optimization)
# - General I/O Utilities module (JSON/YAML/CSV readers/writers, format converters)
# Regulatory Traceability (Complete):
# - Calculation audit trails - Complete input → output traceability for licensing applications
# - Model assumption documentation - Explicit assumption tracking per calculation
# - Safety margin reports - Automated safety margin calculations with text/JSON export
# - BEPU methodology support - Best Estimate Plus Uncertainty workflow integration
# Phase 3 Optimizations (Complete):
# - Implicit Monte Carlo (IMC) for transients - 5-10x faster for time-dependent calculations
# - Enhanced memory pooling - 5-10% speedup, reduced allocation overhead
# - Memory-mapped files - Enable datasets larger than RAM
# Phase 2 Optimizations (Foundation Complete):
# - Adaptive sampling - 2-5x faster convergence by focusing on important regions
# - Hybrid solver - 10-100x faster than pure MC (diffusion + MC combination)
# Phase 1 Optimizations (Complete):
# - Progress indicators with Rich library
# - Enhanced error messages with suggestions
# - Code formatting (black, isort, mypy)
# - Parallel batch processing
# - Enhanced vectorization
# - JIT optimization (fastmath, nogil, boundscheck=False) - 90-95% of C++ performance
# - Added comprehensive CLI with nested subcommands (reactor, data, burnup, validate, visualize, config, shell, workflow)
# - Added batch processing support for reactor analysis
# - Added interactive shell mode (IPython/REPL) via `smrforge shell`
# - Added workflow scripts support (YAML-based workflows) via `smrforge workflow run`
# - Added configuration management (`smrforge config show/set/init`)
# - Added validation testing framework with benchmark comparison
# - Added tab completion scripts (Bash/Zsh and PowerShell)
# - Enhanced CLI with Rich library (colored output, tables, progress bars)
# - Added Parameter Sweep Workflow (smrforge sweep) - automated parameter sweeps with parallel execution
# - Enhanced Design Comparison & Trade Studies (smrforge reactor compare) - multi-design comparison with metrics
# - Added Template Library System (smrforge reactor template) - parameterized reactor design templates
# - Added Simulation Checkpointing & Resume - automatic checkpointing for long burnup simulations
# - Added Design Constraints & Validation (smrforge validate design) - automated constraint checking
# - Added I/O Converters Framework - Serpent/OpenMC format support (framework ready)
# - Added Dash web dashboard with dark/gray mode support
# - Added CLI command (smrforge serve) for dashboard
# - Added Geometry Designer GUI - Interactive visual core layout editor with material palette, 3D preview, export/import
# - Added LWR SMR transient analysis (PWR/BWR/Integral SMR transients)
# - Added LWR SMR burnup features (gadolinium depletion, assembly/rod-wise tracking)
# - Added automated data downloader with parallel downloads and progress indicators
# - Added Pint-based unit checking (pint>=0.20.0)
# - Added lumped-parameter thermal hydraulics (fast 0-D thermal circuits)
# - Added simplified point kinetics API (quick transient analysis)
# - Added transient and thermal visualization capabilities
# - Updated dashboard with quick transient and lumped thermal analysis interfaces
# - Optimized Monte Carlo solver (5-10x faster, 50-70% memory reduction)
#   * Vectorized particle tracking with NumPy arrays
#   * Memory pooling for reduced allocations
#   * Parallel processing with Numba (scales with CPU cores)
#   * Pre-computed cross-section lookup tables
#   * Batch tally processing
# - Structural mechanics module (fuel rod mechanics, stress/strain, PCI, fuel swelling, creep models, material degradation)
# - Advanced control systems (PID controllers, load-following, reactor control, Model Predictive Control)
# - Economics cost modeling (capital costs, operating costs, LCOE calculations)
# - Advanced two-phase flow models (drift-flux, two-fluid, enhanced boiling correlations, CHF)
# - Advanced interfacial transfer models (mass, momentum, energy transfer) - Ishii-Hibiki, RELAP5, TRACE models
# - Fuel cycle optimization and long-term simulation (optimization algorithms, material aging)
# - Advanced optimization algorithms (Genetic Algorithm, Particle Swarm Optimization) for fuel cycle optimization
# - Fuel Performance module (fuel temperature, swelling, fission gas release)
# - General Optimization module (reactor design optimization, loading pattern optimization)
# - General I/O Utilities (file readers/writers, format converters for Serpent/OpenMC)
# - Parallel multi-group diffusion solver (red-black group ordering, parallel spatial operations with Numba prange, 4-8x speedup)
# - MPI support for distributed memory (optional, via mpi4py)
# - Comprehensive CLI guide documentation (docs/guides/cli-guide.md)
# - Robust CLI import handling with multiple fallback strategies
# - Visualization dependencies (plotly, pyvista, dash) are now required and included automatically
# - Fixed Debian Trixie compatibility (libgl1 instead of libgl1-mesa-glx)
# - Fixed Dash 3.x API compatibility (app.run() instead of app.run_server())
# - Fixed dashboard preset loading and validation issues
# - Fixed create_reactor and list_presets import resolution (convenience module conflict)
# - Fixed dashboard State component initialization (all analysis options always in layout)
# - Fixed LumpedThermalHydraulics parameter passing (adaptive/max_step moved to solve_transient)
# - Improved validation warning messages (show actual validation details)
# - Comprehensive CLI guide documentation (docs/guides/cli-guide.md)
# - Updated tutorial with CLI usage and advanced features (docs/guides/tutorial.md)
# - Help system integration (smr.help() function for interactive documentation)
# - Complete dashboard workflow: reactor creation → analysis → results → export
# - Real data capture: flux and power distributions from solver
# - Enhanced visualizations: plots use actual solver data, not sample data
# - Complete exports: JSON/CSV include reactor spec + analysis results
# - Project save/open: full workflow persistence
# - Enhanced error handling and user feedback throughout dashboard
# - Includes support for advanced features (mesh conversion, CAD import - optional)
# - Test coverage: 79.2% overall, 75-80%+ on priority modules (239+ new tests added in latest session)
# - Recent coverage improvements (January 19, 2026):
#   * core/multigroup_advanced.py: 35.7% → 76.4% (+35 tests, bug fix)
#   * validation/standards_parser.py: 44.0% → 93.5% (+32 tests)
#   * validation/regulatory_traceability.py: 0% → 100% (+46 tests)
#   * burnup/lwr_burnup.py: 47.2% → 100% (+33 tests)
#   * economics/integration.py: 0% → 100% (+11 tests)
# - CLI test coverage: 71.8% (130+ passing tests covering all major CLI commands and edge cases)
# - Comprehensive test suite: 194+ test files including Phase 1/2 module tests, __init__.py import error path tests, utility module tests, and CLI tests
# - Utility module coverage: memory_mapped.py (100%), parallel_batch.py (67.2%), error_messages.py (98.2%), optimization_utils.py (97.8%), memory_pool.py (100%), material_mapping.py (100%), units.py (improved), logo.py (improved), logging.py (improved)
# - New test files: test_burnup_init, test_validation_init, test_convenience_init, test_presets_init, test_version, test_utils_units, test_utils_error_messages, test_utils_logo, test_utils_logging, test_help, test_data_downloader
# - Advanced error handling and async edge case coverage
# - Manual testing framework: 13 test scripts (test_*.py) for feature validation (testing/ directory)
#   Optional Jupyter notebooks available for interactive testing (01_CLI_Commands.ipynb)
# - Comprehensive test suite: 133+ test files including Phase 1/2 module tests
# - Advanced error handling and async edge case coverage
# - Quick start validation guide for running tests with real ENDF data (docs/validation/QUICK_START_VALIDATION.md)

FROM python:3.11-slim

# Metadata labels
LABEL maintainer="SMRForge Development Team" \
      description="Small Modular Reactor Design and Analysis Toolkit" \
      version="0.1.0" \
      org.opencontainers.image.title="SMRForge Community" \
      org.opencontainers.image.description="SMRForge Community Edition - reactor design and analysis toolkit"

# Set working directory
WORKDIR /app

# Set environment variables
# Headless-friendly defaults for containers:
# - MPLBACKEND=Agg avoids GUI backends in headless environments
# - PYVISTA_OFF_SCREEN=true helps avoid display requirements
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLBACKEND=Agg \
    PYVISTA_OFF_SCREEN=true \
    SMRFORGE_TIER=community

# Install system dependencies
# Scientific Python packages require various system libraries
# Added libgl1 and libglib2.0-0 for pyvista visualization support
# libgomp1 is required for OpenMP (used by Numba for parallel execution)
# libffi-dev may be needed for some Python C extensions
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    pkg-config \
    libhdf5-dev \
    libblas-dev \
    liblapack-dev \
    libxml2-dev \
    libpng-dev \
    libgl1 \
    libglib2.0-0 \
    libxrender1 \
    libfontconfig1 \
    libgomp1 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first (better layer caching)
COPY requirements.txt /app/requirements.txt

# Copy package metadata first (for better layer caching)
COPY setup.py pyproject.toml README.md README_PYPI.md MANIFEST.in /app/
COPY smrforge/ /app/smrforge/
# Copy CLI scripts and utilities (validation scripts, completion scripts, etc.)
COPY scripts/ /app/scripts/

# Install Python dependencies
# Upgrade pip and install wheel first (helps with some packages)
RUN pip install --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r /app/requirements.txt

# Install SMRForge with all dependencies from setup.py
# This includes visualization dependencies (plotly, pyvista, dash) which are now required
RUN pip install --no-cache-dir .

# Optional: Install additional mesh conversion and CAD import dependencies
# Uncomment the next lines to include mesh conversion and CAD import support:
# RUN pip install --no-cache-dir \
#     meshio>=5.0.0 \
#     trimesh>=3.0.0
# Note: joblib is already included as a dependency of scikit-learn

# Copy examples (optional - can be mounted as volume instead)
COPY examples/ /app/examples/

# Copy testing infrastructure (manual test scripts and documentation)
COPY testing/ /app/testing/
COPY docs/testing/ /app/docs/testing/

# Create directories for data/output/results and ENDF storage
# ENDF data can be mounted as volume or stored in container
RUN mkdir -p /app/data /app/output /app/results /app/endf-data

# Set environment variable for standard ENDF directory
# Users can override this or mount their own ENDF directory
# Also supports configuration file: ~/.smrforge/config.yaml
ENV SMRFORGE_ENDF_DIR=/app/endf-data

# Dashboard port
EXPOSE 8050

# Default command (can be overridden)
# Note: ENDF files can be downloaded automatically using the data downloader
# Run: smrforge data download --library ENDF-B-VIII.1 --output /app/endf-data
# Or: python -c "from smrforge.data_downloader import download_endf_data; download_endf_data(library='ENDF/B-VIII.1', output_dir='/app/endf-data')"
# Or set up manually: smrforge data setup
# 
# To run the web dashboard:
#   smrforge serve --host 0.0.0.0 --port 8050
#   Or: python -c "from smrforge.gui import run_server; run_server(host='0.0.0.0', port=8050)"
#   Then access at http://localhost:8050 (map port 8050 in docker run -p 8050:8050)
#
# CLI Commands available:
#   smrforge reactor create/list/analyze/compare
#   smrforge reactor template create/modify/validate (template library)
#   smrforge data setup/download/validate/interpolate/shield
#     - data interpolate: Cross-section temperature interpolation (linear/log-log/spline)
#     - data shield: Self-shielding calculations (Bondarenko/subgroup/equivalence)
#   smrforge burnup run/visualize (with checkpointing support)
#   smrforge transient run (quick transient analysis - reactivity insertion, decay heat, etc.)
#   smrforge thermal lumped (lumped-parameter thermal hydraulics)
#   smrforge validate run (validation framework - run validation tests)
#   Optimized Monte Carlo: Use OptimizedMonteCarloSolver for 5-10x faster calculations
#   Structural mechanics: Fuel rod analysis (thermal expansion, stress/strain, PCI, fuel swelling, creep models, material degradation)
#   Control systems: PID controllers, load-following, reactor control, Model Predictive Control (MPC) (integrated with transients)
#   Economics: Capital cost estimation, operating costs, LCOE calculations
#   Advanced two-phase flow: Drift-flux models, two-fluid models, enhanced boiling correlations, CHF predictions
#   Fuel cycle optimization: Cycle length optimization, refueling strategy, material aging models
#   Parallel multi-group diffusion: Red-black group ordering, parallel spatial operations (4-8x speedup)
#   MPI support: Optional distributed memory support via mpi4py
#   Phase 2: Adaptive sampling (2-5x faster) and Hybrid solver (10-100x faster than pure MC)
#   Phase 3: Implicit Monte Carlo (5-10x faster transients), Enhanced memory pooling (5-10% speedup), Memory-mapped files (large datasets)
#   smrforge validate design (design constraints validation)
#   smrforge visualize geometry/flux
#   smrforge config show/set/init
#   smrforge shell (interactive IPython/REPL)
#   smrforge workflow run (YAML workflows)
#   smrforge sweep (parameter sweep and sensitivity analysis)
#
# By default, start the web dashboard. Override `command:` in docker-compose.yml
# or `docker run ... <cmd>` for CLI-only usage.
CMD ["smrforge", "serve", "--host", "0.0.0.0", "--port", "8050"]

